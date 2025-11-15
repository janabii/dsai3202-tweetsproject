# DSAI 3202 Tweets Project
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

### Feature Prep
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
