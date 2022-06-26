from cgitb import strong
from bs4 import BeautifulSoup  #Importing the Beautiful Soup Library
import requests				   #Importing the requests library
import time					   #Importing the time library
import csv
import pandas as pd

from zmq import curve_public					   #Importing the csv module

def bulletPointScrape(arr, link, date, category):
    curItem = {}
    blurbText = ''
    links = []

    #adding all the children text, except the last since the last element should be the publication
    for childPos in range(len(arr)-1):
        blurbText += arr[childPos].text

        #if the child is an a tag, get the link
        if arr[childPos].name == 'a':
            links.append(arr[childPos].get('href'))
    
    #remove the first character since that should be the bullet point
    blurbText = blurbText[1:]

    curItem['category'] = category
    curItem['date'] = date
    curItem['publication'] = arr[-1].text.strip()[1:-1]
    curItem['blurb'] = blurbText
    curItem['links-within-blurb'] = links
    curItem['article-link'] = link

    digestItems.append(curItem)


digestItems = []

#digestLink is the link to an article
def getDigestItems(digestLink):

    response = requests.get(digestLink)
    soup = BeautifulSoup(response.text, 'lxml')

    date = ''

    datePosted = soup.find(class_='posted-on')
    dateTag = list(datePosted.children)[-1]
    date = dateTag.text

    #all of the content we want within each article (aka the paragraphs of information)
    entryContentEls = soup.find_all(class_='entry-content')


    for entry in entryContentEls:

        #each p tag is a category in each article
        paragraphLinks = entry.find_all('p')

        for p in paragraphLinks:
            curItem = {}
            # print(p.find('strong'))

            #run though each category by finding the strong tags
            strongTags = p.find_all('strong')
            strongTags.extend(p.find_all('b'))

            #the first strong tag should be the category name
            if len(strongTags) < 1:
                continue
            curCategory = strongTags[0].text.strip()[:-1]
            
            if '•' in p.text:

                currentString = []
                gettingDataActive = False

                for child in p:

                    #checks if the first character is a bullet point, if so starts collecting child tags 
                    if not gettingDataActive and len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = True
                        currentString.append(child)
                    #if the first or last character is open/close paranthses, stop collecting
                    elif (len(child.text.strip()) > 0 and child.text.strip()[0] == '(') or (len(child.text.strip()) > 0 and child.text.strip()[-1] == ')'):
                        currentString.append(child)
                        gettingDataActive = False
                        bulletPointScrape(currentString, link=digestLink, date=date, category = curCategory)
                        currentString = []
                    #if the first is bullet point, stop collecting
                    elif len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = False
                        bulletPointScrape(currentString, link=digestLink, date=date, category = curCategory)
                        currentString = []
                    #if neither stop condition met and actively collecting data, add to active
                    elif gettingDataActive:
                        currentString.append(child)


            #if there is only one strong tag, that means no bullet points
            else:
                curItem['category'] = curCategory
                curItem['date'] = date

                #default to unknown for publication
                publication = 'Unknown'

                #because of inconsistencies, the oublication can either be in an em or in an i tag, so check both
                if p.find('em') is not None:
                    publication = p.find('em').text.strip()[1:-1]
                elif p.find('i') is not None:
                    publication = p.find('i').text.strip()[1:-1]

                curItem['publication'] = publication


                blurbText = ''

                #add all text to blurb except category and publication
                for element in p:
                    if element.name != 'strong' and element.name != 'em' and element.name != 'i' and element.name != 'b':
                        blurbText += element.text

                curItem['blurb'] = blurbText

                links = []
                for link in p.find_all('a'):
                    links.append(link.get('href'))

                curItem['links-within-blurb'] = links
                curItem['article-link'] = digestLink

                digestItems.append(curItem)

        #TODO should get Category, date, publication, blurb, link to the page, plus all links within the blurb, city, state

baseUrl = 'https://energynews.us/category/digest/page/{0}/'

digestLinks = []

i = 1
# Note, keep number low for testing
while i < 51:
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

# Get all the links for all of the pages, then extract info we are looking for
for link in digestLinks:
    getDigestItems(link)

# TODO store in a structured way.


# print(digestItems)
df = pd.DataFrame.from_dict(digestItems)
df.to_excel('digestItems.xlsx')
