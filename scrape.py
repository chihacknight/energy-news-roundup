from bs4 import BeautifulSoup  #Importing the Beautiful Soup Library
import requests				   #Importing the requests library
import time					   #Importing the time library
import csv
import pandas as pd

from zmq import curve_public					   #Importing the csv module

def bulletPointScrape(arr, link, date, category):
    print(arr)
    curItem = {}
    blurbText = ''
    links = []

    for childPos in range(len(arr)-1):
        blurbText += arr[childPos].text
        if arr[childPos].name == 'a':
            links.append(arr[childPos].get('href'))
    
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
    print(digestLink)

    response = requests.get(digestLink)
    soup = BeautifulSoup(response.text, 'lxml')
    curDigestLink = digestLink

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
            # for i in range(len(strongTags)-1,0,-1):
            #     if str(type(strongTags[i])) == "<class 'bs4.element.Tag'>":
            #                 if list(strongTags[i].children)[-1].name == 'br':
            #                     print('del cause thing while')
            #                     del strongTags[i]

            strongTags.extend(p.find_all('b'))

            #the fitst string tag should be the category name
            if len(strongTags) < 1:
                continue
            curCategory = strongTags[0].text[:-1]
            
            #if there is more than the one strong tag, this means there are bullet points
            if len(strongTags) > 1:
                addingString = ''

                #run through each of the bullet points, skip the first one because the first on is the category name
                # for curStringIndex in range(1,len(strongTags)):
                #     curItem = {}
                #     curString = []
                #     links = []
                #     publication = 'Unknown'

                #     addingString = strongTags[curStringIndex].next_sibling

                #     #until there is a new line or no more elements, keep adding the next element in the tree


                #     while addingString is not None and addingString.name != 'br' and addingString.name != 'b':
                #         if str(type(addingString)) == "<class 'bs4.element.Tag'>":
                #             if list(addingString.children)[-1].name == 'br':
                #                 print('broke out cause thing while')
                #                 break

                #         curString.append(addingString)
                #         addingString = addingString.next_sibling

                #     blurbText = ''

                #     #for each element, if it is an a tag, get the link and text, if it is a em tag, that means it is the publication, and if it is neither, it is just text
                #     for tag in curString:
                #         if tag.name == 'a':
                #             links.append(tag.get('href'))
                #             blurbText += tag.text
                #         elif tag.name == 'em' or tag.name == 'i':
                #             publication = tag.text.strip()[1:-1]
                #         else:
                #             blurbText += tag.text

                #     curItem['category'] = curCategory
                #     curItem['date'] = date
                #     curItem['publication'] = publication
                #     curItem['blurb'] = blurbText
                #     curItem['links-within-blurb'] = links
                #     curItem['article-link'] = digestLink

                #     digestItems.append(curItem)

                currentString = []
                gettingDataActive = False

                for child in p:
                    print(child.text)
                    if not gettingDataActive and len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = True
                        currentString.append(child)
                    elif len(child.text.strip()) > 0 and child.text.strip()[0] == '(':
                        currentString.append(child)
                        gettingDataActive = False
                        bulletPointScrape(currentString, link=digestLink, date=date, category = curCategory)
                        currentString = []
                    elif len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = False
                        bulletPointScrape(currentString, link=digestLink, date=date, category = curCategory)
                    elif gettingDataActive:
                        currentString.append(child)


            #if there is only one strong tag, that means no bullet points
            else:
                curItem['category'] = curCategory
                curItem['date'] = date

                publication = 'Unknown'

                if p.find('em') is not None:
                    publication = p.find('em').text.strip()[1:-1]
                elif p.find('i') is not None:
                    publication = p.find('i').text.strip()[1:-1]

                curItem['publication'] = publication


                blurbText = ''
                for element in p:
                    if element.name != 'strong' and element.name != 'em' and element.name != 'i':
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

# Get all the links for all of the pages, then extract info we are looking for
for link in digestLinks:
    getDigestItems(link)

# TODO store in a structured way.


# print(digestItems)
df = pd.DataFrame.from_dict(digestItems)
df.to_excel('digestItems.xlsx')
