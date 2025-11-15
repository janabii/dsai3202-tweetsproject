# tweets_text_features.py
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType, StructType, StructField
from nltk.sentiment import SentimentIntensityAnalyzer
from pyspark.ml.feature import Tokenizer, StopWordsRemover, HashingTF, IDF, IDFModel

# -------------------------------
# TEXT CLEANING
# -------------------------------
def clean_text(text):
    if text is None:
        return ""
    import re, emoji
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " <URL> ", text)
    text = re.sub(r"\b\d+\b", " <NUM> ", text)
    text = emoji.replace_emoji(text, replace="<EMOJI>")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# -------------------------------
# SENTIMENT ANALYZER
# -------------------------------
sia = SentimentIntensityAnalyzer()
def get_sentiment(text):
    if not text:
        return (0.0, 0.0, 0.0, 0.0)
    s = sia.polarity_scores(text)
    return (s["pos"], s["neu"], s["neg"], s["compound"])

# -------------------------------
# LEXICAL DIVERSITY
# -------------------------------
def lexical_diversity(text):
    if not text:
        return 0.0
    words = text.split()
    return len(set(words)) / len(words) if len(words) > 0 else 0.0

sentiment_schema = StructType([
    StructField("pos", FloatType()),
    StructField("neu", FloatType()),
    StructField("neg", FloatType()),
    StructField("compound", FloatType())
])

# -------------------------------
# MAIN PROCESS FUNCTION
# -------------------------------
def process_split(split_name, fit=False):
    print(f"\n--- Processing {split_name} split ---")

    # Load data from features_v1 (train/val/test created earlier)
    df = spark.read.format("delta").load(
        f"abfss://lakehouse@project60300347.dfs.core.windows.net/curated/features_v2/{split_name}/"
    )

    # Text cleaning
    from pyspark.sql.functions import udf
    clean_text_udf = udf(clean_text)
    df = df.withColumn("clean_text", clean_text_udf(F.col("text")))
    df = df.filter(F.length(F.col("clean_text")) >= 10)

    # Basic numeric text stats
    df = df.withColumn("tweet_length_words", F.size(F.split(F.col("clean_text"), " ")))
    df = df.withColumn("tweet_length_chars", F.length(F.col("clean_text")))

    # Lexical sentiment features (VADER)
    sentiment_udf = udf(get_sentiment, sentiment_schema)
    df = df.withColumn("sent", sentiment_udf(F.col("clean_text")))
    df = df.select("*",
        F.col("sent.pos").alias("lex_sent_pos"),
        F.col("sent.neu").alias("lex_sent_neu"),
        F.col("sent.neg").alias("lex_sent_neg"),
        F.col("sent.compound").alias("lex_sent_compound")
    ).drop("sent")

    # Lexical diversity
    lexdiv_udf = F.udf(lexical_diversity, FloatType())
    df = df.withColumn("lexical_diversity", lexdiv_udf(F.col("clean_text")))

    # -------------------------------
    # TF-IDF pipeline
    # -------------------------------
    tokenizer = Tokenizer(inputCol="clean_text", outputCol="words")
    df = tokenizer.transform(df)

    remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")
    df = remover.transform(df)

    hashing_tf = HashingTF(inputCol="filtered_words", outputCol="raw_features", numFeatures=300)
    df = hashing_tf.transform(df)

    idf = IDF(inputCol="raw_features", outputCol="tfidf_features")
    model_path = "/dbfs/tmp/tweets_idf_model"

    if fit:
        print("Fitting TF-IDF on training data...")
        idf_model = idf.fit(df)
        idf_model.write().overwrite().save(model_path)
    else:
        print("Loading existing TF-IDF model...")
        idf_model = IDFModel.load(model_path)

    df = idf_model.transform(df)

    # -------------------------------
    # Select final columns
    # -------------------------------
    final_cols = [
        "id", "user", "date", "query", "clean_text", "sentiment",
        "tweet_length_words", "tweet_length_chars",
        "lex_sent_pos", "lex_sent_neu", "lex_sent_neg", "lex_sent_compound",
        "lexical_diversity", "tfidf_features",
        "total_tweets", "positive_tweets", "negative_tweets", "positive_ratio",
        "user_tweet_count", "sentiment_avg_length", "sentiment_tweet_count"
    ]

    df_final = df.select(*[c for c in final_cols if c in df.columns])

    # -------------------------------
    # Write each split to its own Delta table
    # -------------------------------
    out_path = f"abfss://lakehouse@project60300347.dfs.core.windows.net/curated/features_v2_{split_name}/"
    df_final.write.format("delta").mode("overwrite").save(out_path)
    print(f"Saved {split_name} features to {out_path}")

# -------------------------------
# RUN PIPELINE FOR ALL SPLITS
# -------------------------------
process_split("train", fit=True)
process_split("validation", fit=False)
process_split("test", fit=False)