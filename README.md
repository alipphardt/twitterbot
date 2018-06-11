# Python Twitter-bot

This script was developed as part of a project for a programming in data science class. It defines a TwitterBot class to easily create and configure one or more Twitter bot instances for use.

Given a list of terms, the bot searches either the News or Twitter API (defined by search_on parameter) to find articles or tweets containing any of the terms. If a bitly token and account are provided, long URLs are passed to the Bitly API for shortening. A status update is then posted to the specified Twitter profile using the status type set in the configure_tweet method (e.g., link, reply, at, rt).

An example of the Twitter-bot using this script can be found at [https://twitter.com/millennialYell](https://twitter.com/millennialYell).

In order to run the script on a schedule, consider using a hosting service that supports python such as **pythonanywhere.com**. A free account may be obtained with one daily scheduled task which must be renewed on a monthly basis.

The following is sample code creating a bot and sending tweets.

```
# Create sample TwitterBot
sampleBot = TwitterBot(twitter_consumer_key='COPY KEY HERE', twitter_consumer_secret='COPY SECRET HERE', 
                       twitter_access_key='COPY KEY HERE', twitter_access_secret='COPY SECRET HERE', 
                       search_terms=['LIST OF SEARCH TERMS'], search_on='news',
                       bitly_access_token='COPY OPTIONAL BITLY TOKEN HERE', 
                       news_api_key='COPY NEWS API KEY HERE')
                            
# Configure tweet and create lists for tweets based on search_on parameter
sampleBot.configure_tweet(status= 'SAMPLE STATUS TEXT')
sampleBot.create_list()

# Look at created list
sampleBot.list

# Send tweets using created list
sampleBot.sendTweets()
```