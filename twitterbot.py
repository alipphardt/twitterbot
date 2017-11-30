# Python Twitter-bot

import tweepy
import requests
import json
import pandas as pd
import bs4 as bs
import datetime

# Access Keys and Secrets for Twitter API
CONSUMER_KEY = 'COPY KEY HERE'
CONSUMER_SECRET = 'COPY SECRET HERE'
ACCESS_KEY = 'COPY ACCESS KEY HERE'
ACCESS_SECRET = 'COPY ACCESS SECRET HERE'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# Access token for Bitly API
ACCESS_TOKEN = 'COPY BITLY TOKEN HERE'
BITLY_ACCOUNT = 'COPY BITLY ACCOUNT ID HERE'

# News API Key
apiKey = 'COPY NEWS API KEY HERE'


# Term for bot to search news feeds on
term = 'ENTER TERM HERE'

# Filename for image to be included in twitter update with media
imageFilename = 'ENTER FILENAME HERE'


# Get all sources from News API
response = requests.get("https://newsapi.org/v1/sources?language=en")
Data = json.loads(response.text)

sources = []

for source in Data['sources']:
    sources.append(source['id'])

    
# Get articles with search term, if available, from each News API source

newsAPIArticles = pd.DataFrame()

for i in range(len(sources)):
    source_name = sources[i]
    response = requests.get("https://newsapi.org/v1/articles", params = {'source':source_name,'sortBy':'top','apiKey':apiKey})

    if response.status_code == 200:
        Data = json.loads(response.text)

        sourceArticles = []

        for article in Data['articles']:
            sourceArticles.append([source_name,
                                   article['author'],
                                   article['description'],
                                   article['publishedAt'],
                                   article['title'],
                                   article['url']])

        sourceArticles = pd.DataFrame(sourceArticles, columns=['source','author','description','pubdate','title','url'])
        newsAPIArticles = pd.concat([newsAPIArticles, sourceArticles])

newsAPIArticles = newsAPIArticles.reset_index(drop='True')

newsAPIArticles['description'] = newsAPIArticles['description'].str.lower()
newsAPIArticles['title'] = newsAPIArticles['title'].str.lower()

newsAPIArticles['pubdate'] = newsAPIArticles['pubdate'].apply(pd.to_datetime)

newsAPIArticles = newsAPIArticles.fillna(' ')

termInTitle = newsAPIArticles['title'].str.contains(term)
termInDescription = newsAPIArticles['description'].str.contains(term)

foundArticles = pd.concat([newsAPIArticles[termInTitle], newsAPIArticles[termInDescription]]).drop_duplicates().reset_index(drop=True)


# Find news articles from google news RSS feed

response = requests.get("https://news.google.com/news/rss/search/section/q/" + term + "/" + term + "?hl=en&gl=US&ned=us")

if response.status_code == 200:
    soup = bs.BeautifulSoup(response.content,"xml")
    googleNewsArticles = []

    for item in soup.find_all("item"):
        googleNewsArticles.append([item.title.string,
                                 item.link.string,
                                 item.pubDate.string])

    googleNewsArticles = pd.DataFrame(googleNewsArticles, columns=['title','url','pubdate'])
    googleNewsArticles['pubdate'] = googleNewsArticles['pubdate'].apply(pd.to_datetime)

    currentDT = datetime.datetime.now()
    currentDate = currentDT.strftime("%Y/%m/%d")

    googleNewsArticles = googleNewsArticles[(googleNewsArticles['pubdate'] >= currentDate)]
    googleNewsArticles['titleLower'] = googleNewsArticles['title'].str.lower()

    termInTitle = googleNewsArticles['titleLower'].str.contains(term)
    foundArticles2 = googleNewsArticles[termInTitle]
else:
    print("something went wrong")

allFoundArticles = pd.concat([foundArticles,foundArticles2]).fillna('')


# Get shortened bitly URLs for each long URL

bitlyURLs = []

for index, article in allFoundArticles.iterrows():
    url = article['url']
    bitly_response = requests.get("https://api-ssl.bitly.com/v3/shorten", params = {'longUrl':url,'access_token': ACCESS_TOKEN})

    if bitly_response.status_code == 200:
        Data = json.loads(bitly_response.text)
        bitlyURLs.append(Data['data']['url'])

        
# Merge News API and Google News API

allFoundArticles = pd.concat([foundArticles, foundArticles2]).fillna('')
allFoundArticles['bitly'] = bitlyURLs


# Update Twitter profile with media including shortened link, title, and image

for index, article in allFoundArticles.iterrows():
    title = article['title']
    url = article['bitly']
    message = (url + " " + title)[0:140]
    api.update_with_media(filename=imageFilename,status=message)

