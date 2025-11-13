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

