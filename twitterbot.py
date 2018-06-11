import tweepy  # Tweepy facilitates easy Twitter API calls
from datetime import datetime  # To check datetime for articles/tweets
import requests  # To issue HTTP requests to APIs
import json  # For parsing json in news/twitter responses
import pandas as pd  # For storing and displaying lists retrieved in create_list method
import urllib.parse  # For URL encoding of news API query


class TwitterBot:

    def __init__(self, twitter_consumer_key, twitter_consumer_secret,
                 twitter_access_key, twitter_access_secret,
                 search_terms, search_on='news',
                 bitly_access_token='',
                 news_api_key=''):

        """ Create generic twitter bot that tweets message on twitter account
            given twitter API consumer and access credentials"""

        # Access Keys and Secrets for Twitter API obtained at: https://developer.twitter.com/
        auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
        auth.set_access_token(twitter_access_key, twitter_access_secret)

        # Store API object for access to Twitter REST API
        self.__api = tweepy.API(auth)

        # Term(s) to search news feeds or Twitter on
        self.search_terms = search_terms

        # Method TwitterBot will use to search on. Current options are 'news' or 'twitter'
        self.search_on = search_on

        # Access token for optional Bitly API: https://dev.bitly.com/
        self.__bitly_access_token = bitly_access_token

        # Access token for optional News API: https://newsapi.org/
        self.__news_api_key = news_api_key

        # Will store list of items scraped from news or Twitter
        self.list = []

    def configure_tweet(self, status=None, image=None, status_type='link'):

        """ Changes configuration settings for Twitter status to be sent.
            Status types:
                - link (default) includes url, status, and optional image
                - single_msg posts status and optional image once if any matches are found
                - reply includes status and optional image as reply to a specific tweet
                - at includes user mention, status, and optional image
                - rt retweets a specific tweet specified by id. No status or image """

        self.__status = status
        self.__image = image
        self.__status_type = status_type

        return

    def create_list(self):

        """ Generate list of articles or tweets based on search_on parameter """

        if self.search_on == 'news':
            self.news()
        elif self.search_on == 'twitter':
            self.twitter()
        else:
            print("Invalid search method")
        return

    def any_term(self, row):
        """Helper function returns True if any term is in row passed in"""
        return any(term in row for term in self.search_terms)

    def news(self):

        """ News API Search for any of the provided terms, excluding articles prior to current date.
            Stores list of articles with title, description, url and publish date.
            List returned will be top 10 articles sorted by popularity.  """

        # Get articles with search term, if available, from each News API source
        news_api_articles = pd.DataFrame()

        q = urllib.parse.quote(" OR ".join(self.search_terms), safe='')

        response = requests.get("https://newsapi.org/v2/everything?q=" + q + "&from=" + datetime.now().strftime(
            "%Y-%m-%d") + "&sortBy=popularity&pageSize=100&apiKey=" + self.__news_api_key)

        if response.status_code == 200:
            data = json.loads(response.text)

            source_articles = []

            for article in data['articles']:
                source_articles.append([article['title'],
                                        article['description'],
                                        article['url'],
                                        article['publishedAt']])

            source_articles = pd.DataFrame(source_articles, columns=['title', 'description', 'url', 'publishedAt'])
            news_api_articles = pd.concat([news_api_articles, source_articles])

            news_api_articles = news_api_articles.reset_index(drop='True')

            news_api_articles['publishedAt'] = news_api_articles['publishedAt'].apply(pd.to_datetime)

            news_api_articles = news_api_articles.fillna(' ')

            term_in_title = news_api_articles['title'].apply(self.any_term)

            news_api_articles = news_api_articles[term_in_title]

            if (len(news_api_articles) > 10):
                news_api_articles = news_api_articles[0:10]

        else:
            print("News API failed to return any items")

        # Create shortened links using bitly if access token is provided
        if self.__bitly_access_token != '':

            bitly_urls = []

            for index, article in news_api_articles.iterrows():
                url = article['url']
                bitly_response = requests.get("https://api-ssl.bitly.com/v3/shorten",
                                              params={'longUrl': url, 'access_token': self.__bitly_access_token})

                if bitly_response.status_code == 200:
                    data = json.loads(bitly_response.text)
                    bitly_urls.append(data['data']['url'])

            news_api_articles['url'] = bitly_urls

        # Store final list to TwitterBot object
        self.list = news_api_articles

        return

    def twitter(self):

        """ Twitter API Search for any of the provided terms, excluding retweets, replies, and messages
            prior to current date. Stores list of tweets with tweet ID, text, screen name, publish date
            and number of followers. List returned will be top 10 according to follower count """

        q = " OR ".join(self.search_terms) + " -filter:retweets"
        results = self.__api.search(q=q, lang='en', count=100)

        tweets = []

        for res in results:

            publishedAt = datetime.strptime(res._json['created_at'], '%a %b %d %H:%M:%S +0000 %Y').strftime("%Y-%m-%d")

            if (res._json['in_reply_to_screen_name'] == None and publishedAt == datetime.now().strftime("%Y-%m-%d")):
                tweets.append([res._json['id'],
                               res._json['text'],
                               res._json['user']['screen_name'],
                               publishedAt,
                               res._json['user']['followers_count']])

        self.list = pd.DataFrame(tweets, columns=['id', 'title', 'user', 'publishedAt', 'followers_count']).nlargest(10,
                                                                                                                     'followers_count')

        return

    def sendTweets(self):

        """ Send tweet based on configuration settings """

        if self.__status_type == 'link':

            for index, item in self.list.iterrows():

                title = item['title']
                url = item['url']
                message = (url + " " + title)[0:140]

                if self.__image == None:
                    self.__api.update_status(status=message)
                else:
                    self.__api.update_with_media(filename=self.__image, status=message)

        elif self.__status_type == 'single_msg':

            message = (self.__status)[0:140]

            if self.__image == None:
                self.__api.update_status(status=message)
            else:
                self.__api.update_with_media(filename=self.__image, status=message)

        elif self.__status_type == 'reply':

            for index, item in self.list.iterrows():

                message = (".@" + item['user'] + " " + self.__status)[0:140]

                try:
                    if self.__image == None:
                        self.__api.update_status(status=message, in_reply_to_status_id=item['id'])
                    else:
                        self.__api.update_with_media(filename=self.__image, status=message,
                                                     in_reply_to_status_id=item['id'])
                except KeyError:
                    print("List does not include necessary column(s).")
                    print("reply status type used when generating list based on Twitter search.")
                    print("Change search_on to twitter and create list.")
                    return

        elif self.__status_type == 'at':

            for index, item in self.list.iterrows():

                try:

                    message = (".@" + item['user'] + " " + self.__status)[0:140]

                    if self.__image == None:
                        self.__api.update_status(status=message)
                    else:
                        self.__api.update_with_media(filename=self.__image, status=message)

                except KeyError:
                    print("List does not include necessary column(s).")
                    print("at status type used when generating list based on Twitter search.")
                    print("Change search_on to twitter and create list.")
                    return

        elif self.__status_type == 'rt':

            for index, item in self.list.iterrows():
                try:
                    self.__api.retweet(item['id'])
                except KeyError:
                    print("List does not include necessary column(s).")
                    print("at status type used when generating list based on Twitter search.")
                    print("Change search_on to twitter and create list.")
                    return

        else:
            print("Invalid status type. Change status type through configure_tweet method.")

        return