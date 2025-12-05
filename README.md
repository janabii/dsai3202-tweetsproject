# DSAI 3202 Tweets Project
## Ahmed Al Janabi | 60300347
I will be trying to update this readme file with my findings and approaches since there are no specific guidelines of what we are asked to do.

## Data Ingestion 
To begin with yesterday (Nov 12th) I created a new storage account: project60300347, inside it I created the bronze medallion folder: raw, where I will store the file I downloaded from kaggle. 

From kaggle I opened sentiment140 and donwloaded the file, I started off following the same steps we learnt from the very first lab, where I would open a VM and then through the terminal I would connect to my kaggle through the API and download the kaggle file, but while working on it the steps started to be too time consuming for the tasks simplicity so I decided to just upload it instantly to the raw folder since I already had the file downloaded on my PC.

##  Data Factory
For the DF process, keeping the cost in mind I thought creating a new DF even though I have an active and usable one would be pointless as I would be redoing the same steps that I already know how to perform and it would not be vital so I will just use goodreads-data-factory-60300347.

Inside the DF though I had to create a new linked service in-order to link the container to the DF, I called it ProjectLink60300347. 

I then created 2 datasets: 
raw_tweets & tweets_parquet. It was a simple process where I just had to link each one of them back their path, for the parquet dataset I created a new processed folder in the lakehouse container.

Everything was going smoothly until I ran to an error in the raw_tweets dataset. I haven't came across before, my data was actually in csv format which is different to what we practiced in class, so while I was trying to preview data I kept getting a "Expected EOF, found 'h' at 12". I tried several things to try and make it work.
Firstly, I thought the problem would be from the schema so I imported schema and tested but that didnt solve anything. 
After that, I kept trying to play around with the column, row delimiter, quote character and escape character but it was still not solving anything. 

<img width="1318" height="569" alt="project-df" src="https://github.com/user-attachments/assets/94e377a8-0bf0-4fed-acb5-bab112faa880" />

I then started looking online and in one of the forums I was guided to try making a dataflow, this was an untouched territory, but I gave it a shot. Attached above is the dataflow that I created, I also played with some of the settings by the assistance of the information sign which if it seemed helpful I would tick the box, I ticked the 'Allow schema drift'
and 'Infer drifted column types' so that if there was any issues with some of the columns in the dataset it would automatically fix it.

I then added the tweetsparquet in the dataflow, and went over to the pipelines and added the move and transform -> data flow option and debugged, sadly after all that the same error was there... 

Lastly, I then decided to just self assess the situation and while I was looking around I realized that there was a button that was hidden from my macbook screen, but when I was working at home using a monitor I saw a button called 'Detect Format', which when I clicked it ended up automatically importing the correct schema and when I tested the connection and previewed the data the error was gone... it was funny and annoying at the same time.

I then created a pipeline again and in Move and Transform -> copy data, I dragged copy data and I added raw_tweets as the source and tweets_parquet as the sink and enabled perserve hierarchy, the mapping was automatically correctly detected so all was left was to debug, and thankfully it ran successfully.

## Databricks

Now I have reached the databricks part where I will be starting off with the data cleaning and the feature prepping. Similar to the Data Factory I have decided not to create a new Databricks service as it would add more costs and be pointless as creating a new one would not add anything vital.

### Data cleaning
#### NOTE: To view notebook head to data_cleaning branch -> notebooks/databricks-data_cleaning.ipynb
For the data cleaning part I started off by printing the schema which, like I mentioned earlier that it was able to detect the format had automatically made up the columns so they were detected as generic columns with the following names:

root
 |-- Column1: string (nullable = true)
 |-- Column2: string (nullable = true)
 |-- Column3: string (nullable = true)
 |-- Column4: string (nullable = true)
 |-- Column5: string (nullable = true)
 |-- Column6: string (nullable = true)

 So this clearly needed changing... by using .withColumnRename i changed the schemas to:

 root
 |-- polarity: string (nullable = true)
 |-- id: string (nullable = true)
 |-- date: string (nullable = true)
 |-- query: string (nullable = true)
 |-- user: string (nullable = true)
 |-- text: string (nullable = true)

After that I needed to perform data null checks to see if there are any and thankfully there were none.
```python
from pyspark.sql.functions import col, trim, length, count, when
total_rows = tweets.count()

null_polarity = tweets.filter(col("polarity").isNull()).count()
null_id = tweets.filter(col("id").isNull()).count()
null_date = tweets.filter(col("date").isNull()).count()
null_query = tweets.filter(col("query").isNull()).count()
null_user = tweets.filter(col("user").isNull()).count()
null_text = tweets.filter(col("text").isNull()).count()

empty_text = tweets.filter(
    (col("text").isNull()) | (trim(col("text")) == "")
).count()

print(f"Total rows: {total_rows}")
print(f"NULL polarity: {null_polarity}, NULL id: {null_id}, NULL date: {null_date}")
print(f"NULL query: {null_query}, NULL user: {null_user}")
print(f"NULL or empty text: {empty_text}")
```
-----------------------------------------------------------------------------
I then felt the need to change a few things in the data as the query column was messy as it was showing this NO_QUERY, so I added this replacement where if there was no query it would change to null and if there was query it would stay as is.
```python
tweets = tweets.withColumn(
    "query",
    when(col("query") == "NO_QUERY", None).otherwise(col("query"))
)
```
-----------------------------------------------------------------------------
then, I changed the polarity column to a more suitable name of sentiment and to make it make more sense it would show 4 as positive and 0 for negative which is not a neat way for presenting the data so I changed it to 0 for negative and 1 for positive.
```python
tweets = tweets.withColumn(
    "sentiment",
    when(col("polarity") == "4", 1).otherwise(0)
)
```
-----------------------------------------------------------------------------
Then I performed data normalization by lowercasing, removing urls, mentions, hashtags, keeping letters and collpasing spaces.

```python
from pyspark.sql.functions import regexp_replace, lower, trim

tweets = (
    tweets
    .withColumn("text", lower(trim(col("text"))))
    .withColumn("text", regexp_replace(col("text"), r"http\S+", ""))
    .withColumn("text", regexp_replace(col("text"), r"@\w+", "")) 
    .withColumn("text", regexp_replace(col("text"), r"#[\w-]+", ""))
    .withColumn("text", regexp_replace(col("text"), r"[^a-z\s]", ""))
    .withColumn("text", regexp_replace(col("text"), r"\s+", " "))
)
```
-----------------------------------------------------------------------------
I then dropped tweets with length less than 5 as they would deem useless for my findings, and I fixed the datatype for the date column and also fixed its format to be a simpler dd-mm-yyyy. 
After I completed all this the data was ready and clean to move onto feature prepping with my current schema being:

root
 |-- id: string (nullable = true)
 |-- user: string (nullable = true)
 |-- date: date (nullable = true)
 |-- query: string (nullable = true)
 |-- text: string (nullable = true)
 |-- sentiment: integer (nullable = false)

### Feature Prep (features_v1)
#### NOTE: To view notebook head to features_v1 branch -> notebooks/databricks-feature_prep.ipynb
Now that data cleaning is successful, I move onto feature prep. I decided on creating 3 aggregations as I thought they would be great additions to the current column list by giving more insight and deeper analysis:

1. Daily Sentiment Count

By grouping the date and breaking the tweets down from total, positive and negative to show us a positive ratio of the tweets on a certain date.
```python
daily_sentiment = (
    tweets_clean.groupBy("date")
    .agg(
        count("*").alias("total_tweets"),
        _sum(col("sentiment")).alias("positive_tweets")
    )
    .withColumn("negative_tweets", col("total_tweets") - col("positive_tweets"))
    .withColumn("positive_ratio", round(col("positive_tweets") / col("total_tweets"), 3))
)
```
-----------------------------------------------------------------------------
2. Top Active Users
Shows the most tweeting user by grouping the user and tweet count.
```python
top_users = (
    tweets_clean.groupBy("user")
    .agg(count("*").alias("user_tweet_count"))
    .orderBy(col("user_tweet_count").desc())
)
```
-----------------------------------------------------------------------------
3. Tweet Length Stats
By grouping the sentiment along with the tweet length's average, I get the average length depending on positive or negative sentiment.
```python
tweet_length_stats = (
    tweets_clean.withColumn("tweet_length", length(col("text")))
    .groupBy("sentiment")
    .agg(
        round(avg("tweet_length"), 2).alias("sentiment_avg_length"),
        count("*").alias("sentiment_tweet_count")
    )
    .orderBy("sentiment")
)
```
-----------------------------------------------------------------------------
The schema I end up with when completing feature prep, which I save as features_v1 is:

root
 |-- sentiment: integer (nullable = true)
 |-- user: string (nullable = true)
 |-- date: date (nullable = true)
 |-- id: string (nullable = true)
 |-- query: string (nullable = true)
 |-- text: string (nullable = true)
 |-- total_tweets: long (nullable = true)
 |-- positive_tweets: long (nullable = true)
 |-- negative_tweets: long (nullable = true)
 |-- positive_ratio: double (nullable = true)
 |-- user_tweet_count: long (nullable = true)
 |-- sentiment_avg_length: double (nullable = true)
 |-- sentiment_tweet_count: long (nullable = true)

 I then performed a few checks after making sure that the datatypes are correct to what they need to be:

 ```python
# 1. Basic structure & row count
print("Row count:", features_v1.count())
features_v1.printSchema()

# 2. Null & empty value checks
print("\nChecking for null values in each column:")
null_counts = features_v1.select(
    [_sum(col(c).isNull().cast("int")).alias(c) for c in features_v1.columns]
)
null_counts.show(truncate=False)

# 3. Range & logical checks
print("\nChecking value ranges and logical limits:")
features_v1.select(
    F.min("total_tweets").alias("min_total_tweets"),
    F.max("total_tweets").alias("max_total_tweets"),
    F.min("positive_ratio").alias("min_positive_ratio"),
    F.max("positive_ratio").alias("max_positive_ratio"),
    F.min("user_tweet_count").alias("min_user_tweet_count"),
    F.max("user_tweet_count").alias("max_user_tweet_count"),
    F.min("sentiment_avg_length").alias("min_avg_length"),
    F.max("sentiment_avg_length").alias("max_avg_length")
).show()

# 4. Descriptive statistics overview
print("\nDescriptive statistics overview:")
features_v1.describe([
    "total_tweets", 
    "positive_tweets", 
    "negative_tweets", 
    "positive_ratio", 
    "user_tweet_count", 
    "sentiment_avg_length"
]).show()

# 5. Date sanity check
print("\nChecking for any future-dated rows:")
future_dates = features_v1.filter(F.col("date") > current_date())
print("Future-dated rows:", future_dates.count())

# 6. Duplicate check based on unique tweet ID
print("\nChecking for duplicate tweet IDs:")
dupes = features_v1.groupBy("id").count().filter("count > 1")
print("Duplicate tweet_id count:", dupes.count())

# 7. Sentiment distribution check
print("\nSentiment distribution:")
features_v1.groupBy("sentiment").count().orderBy("sentiment").show()
```
I ended up having no duplicates or nulls in my dataset, as well as the data being valid and not having illogical values which means I can now save my data in the curated (gold) container.

### Data Engineering (features_v2)
#### NOTE: To view notebook head to features_v2 branch -> notebooks/databricks-feat_eng.ipynb & for code scripts/tweets_text_features.py
For the final part of phase 1 of this project it was time to data engineer, I loaded the features_v1 and using the same logic basis from lab 4, which I came to find out is the common industry practice, will apply the 70/15 train, test and validation split to then engineer the data.

```python
train_df, val_df, test_df = df.randomSplit([0.7, 0.15, 0.15], seed=42)

# save data
v2_path = "abfss://lakehouse@project60300347.dfs.core.windows.net/curated/features_v2/"

# putting each split as delta table
train_df.write.format("delta").mode("overwrite").save(v2_path + "train/")
val_df.write.format("delta").mode("overwrite").save(v2_path + "validation/")
test_df.write.format("delta").mode("overwrite").save(v2_path + "test/")
```

-----------------------------------------------------------------------------
The data splits were saved and then I ran them using the tweets_text_features.py which was originally inspired from lecture 5, to lab 4 to have spark changes and now it has reached the changes for this distinct tweets data which had some changes to make as the data is different to the goodreads data. 
I used the bonus lexical diversity I added in lab 4, as it was a bonus I enjoyed and is also relevant to the tweets data, since words are important for understanding the user's sentiment, so I decided to keep it for this.

```python
import os
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
```
-----------------------------------------------------------------------------
After the data concluded its run it was time to make the usual data checks to see if it is valid and verified before I conclude the features_v2 part.

```python
# numeric feature summary
print("Numeric feature summary:")
train_df.select(
    "tweet_length_words",
    "tweet_length_chars",
    "lex_sent_compound",
    "lexical_diversity"
).summary().show()

# check tf-idf feature count
from pyspark.ml.linalg import VectorUDT
from pyspark.sql.functions import udf

tfidf_cols = [c for c in train_df.columns if c.startswith("tfidf_")]
print("TF-IDF feature columns found:", tfidf_cols)

if "tfidf_features" in train_df.columns:
    size_udf = udf(lambda v: int(v.size), "int")
    tfidf_size = train_df.select(size_udf("tfidf_features").alias("size")).limit(1).collect()[0]["size"]
    print(f"TF-IDF feature count: {tfidf_size}")
else:
    print("No TF-IDF feature column found.")

# null value check
print("\nNull value check per column:")
from pyspark.sql.functions import col, sum

null_counts = train_df.select(
    [sum(col(c).isNull().cast("int")).alias(c) for c in train_df.columns]
)
null_counts.show(truncate=False)

# total row count
print("\nTotal rows:", train_df.count())

# schema preview
print("\nSchema:")
train_df.printSchema()
```

Thankfully all the data came back valid logically and with correct datatypes without the need for any curation, so it was all done for this data engineering part successfully.

To end this part, I will now send the schema for features_v2, which is then going to be ready for what im guessing from lectures will be the analysis part.

Schema:
root
 |-- id: string (nullable = true)
 |-- user: string (nullable = true)
 |-- date: date (nullable = true)
 |-- query: string (nullable = true)
 |-- clean_text: string (nullable = true)
 |-- sentiment: integer (nullable = true)
 |-- tweet_length_words: integer (nullable = true)
 |-- tweet_length_chars: integer (nullable = true)
 |-- lex_sent_pos: float (nullable = true)
 |-- lex_sent_neu: float (nullable = true)
 |-- lex_sent_neg: float (nullable = true)
 |-- lex_sent_compound: float (nullable = true)
 |-- lexical_diversity: float (nullable = true)
 |-- tfidf_features: vector (nullable = true)
 |-- total_tweets: long (nullable = true)
 |-- positive_tweets: long (nullable = true)
 |-- negative_tweets: long (nullable = true)
 |-- positive_ratio: double (nullable = true)
 |-- user_tweet_count: long (nullable = true)
 |-- sentiment_avg_length: double (nullable = true)
 |-- sentiment_tweet_count: long (nullable = true)

 ### Data Modeling (PHASE 2)
 After completing all the engineering work for features_v2, the dataset was finally ready for the analysis and modeling stage. At this point, I had a clean, validated, feature-rich dataset stored as Delta tables for train, validation, and test splits (70/15/15). With the data foundation solid, I proceeded to build and evaluate the machine learning models in Databricks.

#### Loading the engineered data
I began by loading the train, validation, and test splits from the curated (Gold) layer:

Each split included:
TF-IDF features, VADER sentiment scores (pos, neu, neg, compound),
lexical diversity, tweet_length metrics, daily aggregated sentiment statistics,
and user activity features.

These columns captured a mixture of text semantics, behavioral patterns, and temporal sentiment indicators.

#### Feature Assembly

Before training any model, I combined all numeric features + TF-IDF vector into a single "features" column using Spark’s VectorAssembler.
This created a unified input vector containing:

TF-IDF 300-dimensional vector

tweet_length_words

tweet_length_chars

lex_sent_pos

lex_sent_neu

lex_sent_neg

lex_sent_compound

lexical_diversity

total_tweets

positive_tweets

negative_tweets

positive_ratio

user_tweet_count

sentiment_avg_length

sentiment_tweet_count

After assembling and indexing the target variable, the dataset was ready for modeling.

#### Logistic Regression 
I started with Logistic Regression because TF-IDF vectors are naturally suited for linear models and it is widely used as a strong baseline for text classification.

Training completed quickly and smoothly despite the dataset size (over 1M rows), which confirmed that the features were well-prepared and the data pipeline was efficient.

Results (Validation Set)

##### Accuracy: ~0.63

##### F1 Score: ~0.62

Observations

Positive sentiment was the easiest class to detect because positive tweets often contain clear emotional words.

Negative sentiment was the hardest due to subtle sarcasm and short expressions.

The model performed surprisingly well given the complexity of tweet language and the large amount of noise in short, informal text.

Logistic Regression established a reliable performance baseline for comparison with a more complex model.

#### Gradient Boosted Trees (GBT)

Gradient Boosted Trees (One-vs-Rest)

Spark's native GBTClassifier only supports binary classification, so to handle the three sentiment classes (negative, neutral, positive), I used One-vs-Rest (OvR) on top of GBT.

GBT trains more slowly and is non-linear, so I expected it to perform differently from LR.

Results (Validation Set)

##### Accuracy: ~0.61

##### F1 Score: ~0.61

Observations

GBT slightly underperformed compared to Logistic Regression.

This showed an important insight:
The TF-IDF + engineered features create a feature space that is mostly linearly separable, which explains why LR performed better.

OvR adds overhead because GBT trains a separate boosted model for each class.

Still, GBT was valuable for comparison because it represents a more expressive model class.

#### Model Comparison Plot
To visually compare the two models, I generated a simple bar chart showing both accuracy and F1 score side-by-side. The plot clearly showed:

Logistic Regression > GBT for both metrics

The gap was small but consistent

This reinforced the conclusion that LR is the more suitable model for this dataset and feature pipeline, to see all the plots it is in the docs -> figures folder.

#### Model Evaluation applied to Test data

After finalizing the comparison between Logistic Regression and GBT on the validation split, the final step was to evaluate the chosen model on the test dataset. Since Logistic Regression consistently performed slightly better and aligned naturally with the TF-IDF–based feature space, it was selected as the only model to be carried forward to the test stage.

I applied the trained Logistic Regression model on the held-out test data, which had never been used during training or validation. The model produced the following results:

##### Test Accuracy: ~0.627
##### Test F1 Score: ~0.622

These numbers closely mirror the validation metrics, confirming that:

the model generalizes well to unseen tweets

performance is stable across all three splits

no overfitting or underfitting occurred

This stability reinforces that the feature engineering and data preparation pipeline were effective.

#### Why Only Logistic Regression Was Evaluated on the Test Set
Although Gradient Boosted Trees were tested during validation for comparison, I intentionally did not extend GBT evaluation to the test split. This was a deliberate modeling decision for three reasons:

###### 1. Performance Consideration
Logistic Regression consistently outperformed GBT on the validation set, both in accuracy and F1. Since the goal of the test set is to assess the final model, evaluating multiple models on it is unnecessary.

###### 2. Model Suitability
The dataset relies heavily on TF-IDF sparse vectors, which linear models (like LR) are known to handle more efficiently and more effectively than tree-based methods. GBTs, in contrast, are not naturally suited to extremely high-dimensional sparse inputs.

###### 3. Practicality
GBT training and inference are significantly more computationally expensive. Given that LR already demonstrated superior validation performance, running additional GBT test evaluations would add cost without offering meaningful benefit.

For these reasons, Logistic Regression was the most appropriate and efficient model to use for the final test-set evaluation.
#### Final Decision 
With stable performance across train, validation, and test splits—and with strong alignment to the structure of the engineered features, Logistic Regression is the recommended model for this sentiment analysis pipeline.

### Deployment
After finalizing the evaluation on the test split, I deployed the Logistic Regression model using Databricks MLflow. Unity Catalog requires every registered model to include both a signature and an input example, so I generated them directly from the engineered test data. I then logged the model along with the test metrics and registered it under the name tweet_sentiment_lr.

```python
from mlflow.models.signature import ModelSignature
from mlflow.types import TensorSpec, Schema

# model signature
input_schema = Schema([TensorSpec("float32", (-1,))])
output_schema = Schema([TensorSpec("float32", (1,))])
signature = ModelSignature(inputs=input_schema, outputs=output_schema)

# input example
example_row = test2.select("features").limit(1).toPandas()
input_example = {"features": example_row["features"][0].toArray()}

import mlflow
import mlflow.spark

model_name = "tweet_sentiment_lr"

with mlflow.start_run(run_name="LR_Final_Test_Model"):

    mlflow.log_metric("test_accuracy", acc)
    mlflow.log_metric("test_f1", f1)

    mlflow.spark.log_model(
        lr_model,
        artifact_path="lr_model",
        signature=signature,
        input_example=input_example
    )

    model_uri = f"runs:/{mlflow.active_run().info.run_id}/lr_model"
    mlflow.register_model(model_uri, model_name)
```
<img width="1631" height="592" alt="image" src="https://github.com/user-attachments/assets/41c3e5fe-198d-4fcc-afbf-9cb5c1954a52" />

The model is now fully registered in the Databricks Model Registry with versioning, metadata, and test performance included.
