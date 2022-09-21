from attr import field
from bs4 import BeautifulSoup  # Importing the Beautiful Soup Library
import requests  # Importing the requests library
import json
import requests_cache
import csv
import locationtagger


topSkipStateWords = ['North', 'West', 'South', 'East']

# for the older variant, if find 404 page, then stop
def isFinalPageOld(link):
    soup = BeautifulSoup(requests.get(link).text, 'lxml')
    if soup.find(class_='error-404 not-found') is not None:
        return True

    return False

# for the newer variant, if find an empty array, then stop
def isFinalPageNew(jsonFile):
    if len(jsonFile['items']) < 1:
        return True

    return False

def bulletPointScrape(arr, link, date, category):
    curItem = {}
    blurbText = ''
    links = []

    if len(arr) < 1:
        return

    # adding all the children text, except the last since the last element should be the publication
    for childPos in range(len(arr)-1):
        blurbText += arr[childPos].text

        # if the child is an a tag, get the link
        if arr[childPos].name == 'a':
            links.append(arr[childPos].get('href'))

    # remove the first character since that should be the bullet point
    if len(blurbText) > 0 and blurbText[0] == '•':
        blurbText = blurbText[1:]

    curItem['category'] = category
    curItem['date'] = date
    curItem['publication'] = arr[-1].text.strip()[1:-1]
    curItem['blurb'] = blurbText
    curItem['article-link'] = link
    curItem['links-within-blurb'] = ', '.join(links)

    regionsAndCities = getStates(curItem)

    curItem['states'] = ', '.join(x for x in regionsAndCities.regions if x not in topSkipStateWords)

    digestItems.append(curItem)


def getStates(item):
    text = item['blurb'] + ' ' + item['publication']

    entities = locationtagger.find_locations(text=text)

    return entities


digestItems = []

# digestLink is the link to an article
def getDigestItems(digestLink):
    print('getting digest for this page', digestLink)

    response = requests.get(digestLink)
    soup = BeautifulSoup(response.text, 'lxml')

    date = ''

    datePosted = soup.find(class_='posted-on')
    if datePosted:
        dateTag = list(datePosted.children)[0]
        date = dateTag.text
    else:
        date = 'Unknown'

    # all of the content we want within each article (aka the paragraphs of information)
    entryContentEls = soup.find_all(class_='entry-content')

    for entry in entryContentEls:

        # each p tag is a category in each article
        paragraphLinks = entry.find_all('p')

        for p in paragraphLinks:
            curItem = {}

            # run though each category by finding the strong tags
            strongTags = p.find_all('strong')
            strongTags.extend(p.find_all('b'))

            # the first strong tag should be the category name
            if len(strongTags) < 1 or strongTags[0] == '':
                continue

            curCategory = strongTags[0].text.strip()[:-1]

            if 'sponsored' in curCategory.lower() or 'ad' in curCategory.lower() or 'message' in curCategory.lower():
                continue

            if '•' in p.text:

                currentString = []
                gettingDataActive = False

                for child in p:

                    # checks if the first character is a bullet point, if so starts collecting child tags
                    if not gettingDataActive and len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = True
                        currentString.append(child)
                    # if last is bullet point, stop collecting then start collecting for next one
                    elif len(child.text.strip()) > 0 and child.text.strip()[-1] == '•':
                        bulletPointScrape(
                            currentString, link=digestLink, date=date, category=curCategory)
                        currentString = []
                    # if the first or last character is open/close paranthses, stop collecting
                    elif (len(child.text.strip()) > 0 and child.text.strip()[0] == '(') or (len(child.text.strip()) > 0 and child.text.strip()[-1] == ')'):
                        currentString.append(child)
                        gettingDataActive = False
                        bulletPointScrape(
                            currentString, link=digestLink, date=date, category=curCategory)
                        currentString = []
                    # if the first is bullet point, stop collecting
                    elif len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                        gettingDataActive = False
                        bulletPointScrape(
                            currentString, link=digestLink, date=date, category=curCategory)
                        currentString = []
                    # if neither stop condition met and actively collecting data, add to active
                    elif gettingDataActive:
                        currentString.append(child)

            # if there is only one strong tag, that means no bullet points
            else:
                curItem['category'] = curCategory
                curItem['date'] = date

                # default to unknown for publication
                publication = 'Unknown'

                # because of inconsistencies, the oublication can either be in an em or in an i tag, so check both
                if p.find('em') is not None:
                    publication = p.find('em').text.strip()[1:-1]
                elif p.find('i') is not None:
                    publication = p.find('i').text.strip()[1:-1]
                curItem['publication'] = publication

                blurbText = ''
                # add all text to blurb except category and publication
                for element in p:
                    if element.name != 'strong' and element.name != 'em' and element.name != 'i' and element.name != 'b':
                        blurbText += element.text

                curItem['blurb'] = blurbText

                links = []
                for link in p.find_all('a'):
                    links.append(link.get('href'))

                curItem['article-link'] = digestLink
                curItem['links-within-blurb'] = ', '.join(links)

                regionsAndCities = getStates(curItem)

                curItem['states'] = ', '.join(x for x in regionsAndCities.regions if x not in topSkipStateWords)

                digestItems.append(curItem)

        # TODO should get state


requests_cache.install_cache('getting-article-cache', backend='sqlite')

NUM_POSTS_PER_PAGE_NEW = 10

march2022Posts = 'https://energynews.us/category/digest/page/{0}/'
curentPosts = 'https://energynews.us/wp-json/newspack-blocks/v1/articles?className=is-style-borders&showExcerpt=0&moreButton=1&showCategory=1&postsToShow={0}&categories%5B0%5D=20720&categories%5B1%5D=20721&categories%5B2%5D=20710&categories%5B3%5D=20711&categories%5B4%5D=20348&typeScale=3&sectionHeader=Newsletter%20archive&postType%5B0%5D=newspack_nl_cpt&excerptLength=55&showReadMore=0&readMoreLabel=Keep%20reading&showDate=1&showImage=1&showCaption=0&disableImageLazyLoad=0&imageShape=landscape&minHeight=0&moreButtonText&showAuthor=1&showAvatar=1&postLayout=list&columns=3&mediaPosition=top&&&&&&imageScale=3&mobileStack=0&specificMode=0&textColor&customTextColor&singleMode=0&showSubtitle=0&textAlign=left&includedPostStatuses%5B0%5D=publish&page={1}&amp=1'

digestLinks = []
oldArticles = []
newArticles = []

oldPostCounter = 0
newPostCounter = 1
debugMode = False

# run until stop condition of no links
while True:
    print('new pages getting page', newPostCounter)
    response = requests.get(curentPosts.format(
        NUM_POSTS_PER_PAGE_NEW, newPostCounter))
    parsedText = json.loads(response.text)

    if isFinalPageNew(parsedText):
        break

    for block in parsedText['items']:
        soup = BeautifulSoup(block['html'], 'lxml')
        articleArray = soup.find_all(class_='entry-title')
        newArticles.extend(articleArray)

    newPostCounter += 1

    if debugMode:
        break

# get the links from each tag
for metaEl in newArticles:
    link = metaEl.find_all('a', rel="bookmark")
    for el in link:
        digestLinks.append(el.get('href'))
    


# run until stop condition of finding 404 page
while True:
    print('old pages getting page', oldPostCounter)

    if isFinalPageOld(march2022Posts.format(oldPostCounter)):
        break

    if debugMode and oldPostCounter >= 3:
        break

    response = requests.get(march2022Posts.format(oldPostCounter))
    soup = BeautifulSoup(response.text, 'lxml')
    articleArray = soup.find_all('article')
    oldArticles.extend(articleArray)

    oldPostCounter += 1

# get the links from each tag
for aElement in oldArticles:
    # There is also a link for the author, only intereseted in the links below entry header
    metaElements = aElement.find_all(class_='entry-header')
    for metaEl in metaElements:
        link = metaEl.find_all('a', rel="bookmark")
        for el in link:
            digestLinks.append(el.get('href'))


# Get all the links for all of the pages, then extract info we are looking for
for link in digestLinks:
    getDigestItems(link)

# write to csv
with open('digestItems.csv', 'w') as csvfile:
    fieldNames = ['category', 'date', 'publication', 'blurb',
                  'links-within-blurb', 'article-link', 'states']
    writer = csv.DictWriter(csvfile, fieldnames=fieldNames)

    writer.writeheader()

    for row in digestItems:
        writer.writerow(row)
