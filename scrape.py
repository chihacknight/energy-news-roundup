from bs4 import BeautifulSoup  #Importing the Beautiful Soup Library
import requests				   #Importing the requests library
import time					   #Importing the time library
import csv					   #Importing the csv module

def getDigestItems(digestLink):
    response = requests.get(digestLink)
    soup = BeautifulSoup(response.text, 'lxml')
    entryContentEls = soup.find_all(class_='entry-content')
    for entry in entryContentEls:
        print(entry.find_all('p'))
        #TODO should get Category, date, publication, blurb, link to the page, plus all links within the blurb, city, state

baseUrl = 'https://energynews.us/category/digest/page/{0}/'

digestLinks = []

i = 1
# Note, keep number low for testing
while i < 2:
    response = requests.get(baseUrl.format(i))
    soup = BeautifulSoup(response.text, 'lxml')
    articles = soup.find_all('article')
    for aElement in articles:
        # There is also a link for the author, only intereseted in the links below entry header
        metaElements = aElement.find_all(class_='entry-header')
        for metaEl in metaElements:    
            link = metaEl.find_all('a', rel="bookmark")
            for el in link:
                digestLinks.append(el.get('href'))
    i+=1
    

print(digestLinks)

# Get all the links for all of the pages, then extract info we are looking for
for link in digestLinks:
    getDigestItems(link)

# TODO store in a structured way.


    