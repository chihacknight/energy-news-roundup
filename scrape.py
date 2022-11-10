from bs4 import BeautifulSoup  # Importing the Beautiful Soup Library
import requests  # Importing the requests library
import json
import requests_cache
import csv
import locationtagger

debugMode = True

topSkipStateWords = ['North', 'West', 'South', 'East']
stateNames = [
    "alabama",
    "alaska",
    "arizona",
    "arkansas",
    "california",
    "colorado",
    "connecticut",
    "delaware",
    "district of columbia",
    "florida",
    "georgia",
    "hawaii",
    "idaho",
    "illinois",
    "indiana",
    "iowa",
    "kansas",
    "kentucky",
    "louisiana",
    "maine",
    "maryland",
    "massachusetts",
    "michigan",
    "minnesota",
    "mississippi",
    "missouri",
    "montana",
    "nebraska",
    "nevada",
    "new hampshire",
    "new jersey",
    "new mexico",
    "new york",
    "navajo nation",
    "north carolina",
    "north dakota",
    "northern chumash",
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "puerto rico",
    "rhode island",
    "south carolina",
    "south dakota",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "west virginia",
    "wisconsin",
    "wyoming",
]

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

def findAndReturnStates(blurb, pub):
    regionsAndCities = getStates(blurb, pub)

    curState = ', '.join(
        x.lower() for x in regionsAndCities.regions if x not in topSkipStateWords)

    if len(curState) <= 0:
        curState = check_states(blurb)
    
    return curState

def addToDigestItems(links, cat, date, pub, blurb, states):
    curItem = {}
    curItem['links-within-blurb'] = ', '.join(links)
    curItem['category'] = cat
    curItem['date'] = date
    curItem['publication'] = pub
    curItem['blurb'] = blurb
    curItem['states'] = states

    digestItems.append(curItem)

def bulletPointScrape(arr, link, date, category, inTextLink):
    curItem = {}
    blurbText = ''
    links = []

    if len(arr) < 1:
        return

    # adding all the children text, except the last since the last element should be the publication
    for childPos in range(len(arr)-1):
        try:
            blurbText += arr[childPos].text
        except:
            blurbText += arr[childPos].string

    # remove the first character since that should be the bullet point
    blurbText = blurbText.strip(" •")

    for link in inTextLink:
        links.append(link.get('href'))

    if '•' in blurbText:
        raise Exception('Found bullet point in blurb')
    
    pub = arr[-1].text.strip()

    curState = findAndReturnStates(blurb=blurbText, pub=pub)

    addToDigestItems(link=links, cat=category, date=date, pub=pub, blurb=blurbText, states=curState)


def getStates(blurb, pub):
    text = blurb + ' ' + pub

    entities = locationtagger.find_locations(text=text)

    return entities


digestItems = []

# digestLink is the link to an article


def check_states(text):
    retArr = []
    for s in stateNames:
        if s in text.lower():
            retArr.append(s.lower())

    return ', '.join(retArr)

# clean "publication name" to remove parentheses if there are parentheses


def clean_pub(pub):
    if len(pub) <= 0:
        return pub

    temp = pub.strip()
    if temp[0] == '(' and temp[-1] == ')':
        temp = temp[1:-1]
    return temp


def bullet_scrape_logic(p, digestLink, date, curCategory):
    currentElements = []
    gettingDataActive = False

    for child in p:
        try:
            # checks if the first character is a bullet point, if so starts collecting child tags
            if not gettingDataActive and len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                gettingDataActive = True
                currentElements.append(child)
            # if last is bullet point, stop collecting then start collecting for next one
            elif len(child.text.strip()) > 0 and child.text.strip()[-1] == '•':
                bulletPointScrape(
                    currentElements, link=digestLink, date=date, category=curCategory, inTextLink=p.find_all('a'))
                currentElements = []
            # if the first or last character is open/close paranthses, stop collecting
            elif (len(child.text.strip()) > 0 and child.text.strip()[0] == '(') or (len(child.text.strip()) > 0 and child.text.strip()[-1] == ')'):
                currentElements.append(child)
                gettingDataActive = False
                bulletPointScrape(
                    currentElements, link=digestLink, date=date, category=curCategory, inTextLink=p.find_all('a'))
                currentElements = []
            # if the first is bullet point, stop collecting
            elif len(child.text.strip()) > 0 and child.text.strip()[0] == '•':
                gettingDataActive = False
                bulletPointScrape(
                    currentElements, link=digestLink, date=date, category=curCategory, inTextLink=p.find_all('a'))
                currentElements = []
            # if neither stop condition met and actively collecting data, add to active
            elif gettingDataActive:
                currentElements.append(child)
        except:
            currentElements.append(child)


def getDigestItems(digestLink):
    print('getting digest for', digestLink)

    response = requests.get(digestLink)
    soup = BeautifulSoup(response.text, 'lxml')

    if soup.i or soup.b:
        if soup.i:
            soup.i.replace_with(soup.new_tag('em'))

        if soup.b:
            soup.b.replace_with(soup.new_tag('strong'))

        print(soup)

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

            if 'sponsored' in curCategory.lower() or 'ad' in curCategory.lower() or 'message' in curCategory.lower() or 'ponsored' in curCategory.lower():
                continue

            if '•' in p.text:
                bullet_scrape_logic(p=p, digestLink=digestLink,
                                    date=date, curCategory=curCategory)

            # if there is only one strong tag, that means no bullet points
            else:
                curItem['category'] = curCategory
                curItem['date'] = date

                # default to unknown for publication
                publication = 'Unknown'

                # because of inconsistencies, the oublication can either be in an em or in an i tag, so check both
                if p.find_all('em') is not None:
                    publication = clean_pub(p.find_all('em')[-1].text.strip())
                elif p.find_all('i') is not None:
                    publication = clean_pub(p.find_all('i')[-1].text.strip())
                curItem['publication'] = publication

                if 'sponsored link' in publication:
                    continue

                blurbText = ''
                # add all text to blurb except category and publication
                for element in p:
                    if element.name != 'strong' and element.name != 'em' and element.name != 'i' and element.name != 'b':
                        try:
                            blurbText += element.text
                        except:
                            blurbText += element.string

                curItem['blurb'] = blurbText

                links = []
                for link in p.find_all('a'):
                    links.append(link.get('href'))

                curItem['links-within-blurb'] = ', '.join(links)

                curState = findAndReturnStates(blurbText, publication)

                if '•' in blurbText:
                    raise Exception('Found bullet point in blurb')

                addToDigestItems(links=link, pub=publication, cat=curCategory, date=date, blurb=blurbText, states=curState)


requests_cache.install_cache('getting-article-cache', backend='sqlite')

NUM_POSTS_PER_PAGE_NEW = 10

march2022Posts = 'https://energynews.us/category/digest/page/{0}/'

digestLinks = []
oldArticles = []

oldPostCounter = 0
newPostCounter = 1

# run until stop condition of finding 404 page
print("getting pages before March 2022")
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

if debugMode:
    with open('testDigest.csv', 'w') as csvfile:
        fieldNames = ['category', 'date', 'publication', 'blurb',
                      'links-within-blurb', 'states']
        writer = csv.DictWriter(csvfile, fieldnames=fieldNames)

        writer.writeheader()

        for row in digestItems:
            writer.writerow(row)
else:
    # write to csv
    with open('digestItems.csv', 'w') as csvfile:
        fieldNames = ['category', 'date', 'publication', 'blurb',
                      'links-within-blurb', 'states']
        writer = csv.DictWriter(csvfile, fieldnames=fieldNames)

        writer.writeheader()

        for row in digestItems:
            writer.writerow(row)
