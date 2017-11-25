#!/usr/bin/env python3

"""
@author: rob.dunne@manchester.ac.uk
Fetch a list of research papers from computer science research literature databases based on specified search terms.
Databases: Google Scholar, ACM digital library, IEEE Xplore, ScienceDirect, SpringerLink, and Wiley Online Library.

Useful list of APIs for further expansion: https://libraries.mit.edu/scholarly/publishing/apis-for-scholarly-resources/
"""

import urllib
from bs4 import BeautifulSoup, SoupStrainer
import time
import csv
import contextlib
from habanero import Crossref
import json
import requests
import pymysql.cursors

class Litfetch():
    # Constructor
    def __init__(self):
        # Set the search terms
        self.config = self.getConfig()
        self.startYear = '2011'
        self.endYear = '2017'
        self.searchTerms = ['ambient intelligence', 'ambient system', 'smart environment']
        self.secondaryTerms = [['home','domestic'],['care', 'elderly', 'assisted living', 'assistive'],['healthcare','health','medical'],['shops','shopping','recommender systems','business'],['data','data management','AI','artificial intelligence'],['human','affective'],['social','economic','ethics','ethical']]

        # Depth of results
        self.maxResults = 30

        # Perform the search
        self.fetchPapers()

    def fetchPapers(self):
        # Databases selection
        selection = input('Please enter a database or de-duplicate: google, acm, ieee, sciencedirect, springer, wiley, dedupe.\n')
        print('You selected: '+selection)

        if selection == 'google':
            # Scrape the webpage and append to the CSV
            print('Searching Google Scholar...')
            self.googleScholar()
        elif selection == 'acm':
            # Call the database API and append to the CSV
            print('Searching ACM Digital Library...')
            self.acmDL()
        elif selection == 'ieee':
            # Call the database API and append to the CSV
            print('Searching IEEE Xplore...')
            self.ieeeXplore()
        elif selection == 'sciencedirect':
            # Call the database API and append to the CSV
            print('Searching ScienceDirect...')
            self.scienceDirect()
        elif selection == 'springer':
            # Call the database API and append to the CSV
            print('Searching SpringerLink...')
            self.springerLink()
        elif selection == 'wiley':
            # Call the database API and append to the CSV
            print('Searching Wiley Online Library...')
            self.wileyOL()
        elif selection == 'dedupe':
            # Write a de-duplicated list as a CSV
            print('De-duplicating list...')
            self.deDuplicatePapers()
        else:
            print('Uh oh, I don\'t know what '+selection+' is?')

    def googleScholar(self):
        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-google.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-google.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            print('Searching Google Scholar for: '+searchString+'.')
            print('Found:')

            pageResults = ['0','10','20']
            for page in pageResults:
                searchURL = 'https://scholar.google.co.uk/scholar?q='+urllib.parse.quote_plus(searchString)+'&hl=en&as_sdt=0%2C5&as_ylo='+self.startYear+'&as_yhi='+self.endYear+'&start='+page
                #print(searchURL)
                user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
                headers = { 'User-Agent': user_agent }
                req = urllib.request.Request(searchURL, data=None, headers=headers)
                with contextlib.closing(urllib.request.urlopen(req)) as get:
                    results = BeautifulSoup(get, "lxml")
                    #print(results)

                    for paper in results.find_all("div", { "class" : "gs_ri" }):
                        paperTitle = '-'
                        paperAuthors = '-'
                        paperYear = '0000'
                        paperSource = '-'

                        for h3 in paper.find_all('h3'):
                            for title in h3.find_all('a', href=True):
                                print(title.text)
                                print(title['href'])

                                paperTitle = title.text
                                paperSource = title['href']

                        for author in paper.find_all("div", { "class" : "gs_a" }):
                            paperAuthors = author.text

                        yearParts = paperAuthors.split('-')
                        yearParts2 = yearParts[1].split(',')
                        yearParts2Length = len(yearParts2)-1
                        paperYear = yearParts2[yearParts2Length]

                        resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'Google Scholar', paperSource, searchURL]

                        # Append to the CSV
                        with open(r'review-search-google.csv', 'a', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(resultRow)

                # Sleep to prevent bot blocking
                time.sleep(1)

            print('-----------')
            print('Done.')

    def acmDL(self):
        # Using Crossref API: https://github.com/sckott/habanero
        cr = Crossref()

        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-acm.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-acm.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            searchURL = 'https://api.crossref.org/works?mailto=rob.dunne@manchester.ac.uk&rows=100&from-index-date=2011member=320&query='+searchString;
            #print(searchURL)

            print('Searching ACM via Crossref for: '+searchString+'.')
            print('Found:')

            results = cr.works(query=searchString, limit=30, order='desc', filter={'from-pub-date':'2011', 'member': '320'})
            for paper in results['message']['items']:
                print(paper['title'][0])
                """
                print(paper['created']['date-parts'][0][0])
                for author in paper['author']:
                    print(author['family']+','+author['given'])
                print(paper['link'][0]['URL'])
                """

                paperTitle = paper['title'][0]

                paperAuthors = ''
                try:
                    for author in paper['author']:
                        paperAuthors = author['family']+','+author['given']+', '+paperAuthors
                except KeyError:
                    paperAuthors = 'Not available'

                paperYear = paper['created']['date-parts'][0][0]
                try:
                    paperSource = paper['link'][0]['URL']
                except KeyError:
                    paperSource = 'Not available'

                resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'ACM - Crossref', paperSource, searchURL]

                # Append to the CSV
                with open(r'review-search-acm.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(resultRow)

        print('Done.')

    def ieeeXplore(self):
        # http://ieeexploreapi.ieee.org/api/v1/search/articles?format=json&apikey='+self.config['ieeeKey']+'&querytext=
        # Crossref ID 263
        # Using Crossref API: https://github.com/sckott/habanero
        cr = Crossref()

        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-ieee.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-ieee.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            searchURL = 'https://api.crossref.org/works?mailto=rob.dunne@manchester.ac.uk&rows=100&from-index-date=2011member=263&query='+searchString;
            #print(searchURL)

            print('Searching IEEEvia Crossref for: '+searchString+'.')
            print('Found:')

            results = cr.works(query=searchString, limit=30, order='desc', filter={'from-pub-date':'2011', 'member': '263'})
            for paper in results['message']['items']:
                print(paper['title'][0])

                paperTitle = paper['title'][0]
                paperAuthors = ''
                try:
                    for author in paper['author']:
                        paperAuthors = author['family']+','+author['given']+', '+paperAuthors
                except KeyError:
                    paperAuthors = 'Not available'

                paperYear = paper['created']['date-parts'][0][0]
                try:
                    paperSource = paper['link'][0]['URL']
                except KeyError:
                    paperSource = 'Not available'

                resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'IEEE - Crossref', paperSource, searchURL]

                # Append to the CSV
                with open(r'review-search-ieee.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(resultRow)

        print('Done.')

    def scienceDirect(self):
        # https://api.elsevier.com/content/search/scidir?apiKey='+self.config['sdKey']+'&query=
        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-sciencedirect.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-sciencedirect.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            print('Searching ScienceDirect for: '+searchString+'.')
            print('Found:')

            searchURL = 'https://api.elsevier.com/content/search/scidir?apiKey='+self.config['sdKey']+'&count=30&sort=-date&httpAccept=application%2Fjson&query='+urllib.parse.quote_plus(searchString)
            data = json.loads(requests.get(searchURL).text)

            for paper in data['search-results']['entry']:
                print(paper['dc:title'])
                for author in paper['authors']['author']:
                    print(author['surname']+','+author['given-name'])

                dateLong = paper['prism:coverDate'][0]['$'].split('-')
                paperYear = dateLong[0]
                print(paperYear)
                print(paper['link'][0]['@href'])

                paperTitle = paper['dc:title']
                paperAuthors = ''
                for author in paper['authors']['author']:
                    paperAuthors = author['surname']+','+author['given-name']+', '+paperAuthors

                dateLong = paper['prism:coverDate'][0]['$'].split('-')
                paperYear = dateLong[0]

                paperSource = paper['link'][0]['@href']

                resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'ScienceDirect', paperSource, searchURL]

                # Append to the CSV
                with open(r'review-search-sciencedirect.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(resultRow)

        print('Done.')

    def springerLink(self):
        # 'http://api.springer.com/metadata/json?api_key='+self.config['springerKey']+'&p=30&q='+searchString+' sort:date'
        # Reset the file
        # PUBLICATION DATES ARE INCORRECT IN THE SPRINGER API
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-springer.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-springer.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            print('Searching SpringerLink for: '+searchString+'.')
            print('Found:')

            searchURL = 'http://api.springer.com/metadata/json?api_key='+self.config['springerKey']+'&p=30&q='+urllib.parse.quote_plus(searchString)+' sort:date'
            data = json.loads(requests.get(searchURL).text)
            print(searchURL)

            for paper in data['records']:
                print(paper['title'])
                for author in paper['creators']:
                    print(author['creator'])

                dateLong = paper['publicationDate'].split('-')
                paperYear = dateLong[0]
                print(paperYear)
                print(paper['url'][0]['value'])

                paperTitle = paper['title']
                paperAuthors = ''
                for author in paper['creators']:
                    paperAuthors = author['creator']+', '+paperAuthors

                dateLong = paper['publicationDate'].split('-')
                paperYear = dateLong[0]

                paperSource = paper['url'][0]['value']

                resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'Springer', paperSource, searchURL]

                # Append to the CSV
                with open(r'review-search-springer.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(resultRow)

            print('Done.')

    def wileyOL(self):
        # Using Crossref API: https://github.com/sckott/habanero
        cr = Crossref()

        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-wiley.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-wiley.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        for terms in self.secondaryTerms:
            searchString = '('+self.searchTerms[0]+' OR '+self.searchTerms[1]+' OR '+self.searchTerms[2]+') AND ('
            secondaryTerms = ' OR '.join(terms)
            searchString = searchString+secondaryTerms+')'
            #print(searchString)

            searchURL = 'https://api.crossref.org/works?mailto=rob.dunne@manchester.ac.uk&rows=100&from-index-date=2011member=311&query='+searchString;
            #print(searchURL)

            print('Searching Wiley-Blackwell via Crossref for: '+searchString+'.')
            print('Found:')

            results = cr.works(query=searchString, limit=30, order='desc', filter={'from-pub-date':'2011', 'member': '311'})
            for paper in results['message']['items']:
                print(paper['title'][0])
                """
                print(paper['created']['date-parts'][0][0])
                for author in paper['author']:
                    print(author['family']+','+author['given'])
                print(paper['link'][0]['URL'])
                """

                paperTitle = paper['title'][0]

                paperAuthors = ''
                try:
                    for author in paper['author']:
                        paperAuthors = author['family']+','+author['given']+', '+paperAuthors
                except KeyError:
                    paperAuthors = 'Not available'

                paperYear = paper['created']['date-parts'][0][0]
                try:
                    paperSource = paper['link'][0]['URL']
                except KeyError:
                    paperSource = 'Not available'

                resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, paperTitle, paperAuthors, paperYear, 'Wiley - Crossref', paperSource, searchURL]

                # Append to the CSV
                with open(r'review-search-wiley.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(resultRow)

        print('Done.')

    def deDuplicatePapers(self):
        # Reset the file
        csvHeader = ['section','searched','terms','title','authors','published','database','source','url']
        f = open('review-search-deduped.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-deduped.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Combine and remove duplicates from the database CSVs. Write one file.
        files = ['google', 'sciencedirect', 'springer', 'wiley', 'acm', 'ieee']
        paperList = {}

        for csvData in files:
            with open('review-search-'+csvData+'.csv', newline='') as csvfile1:
                data1 = csv.reader(csvfile1, delimiter=',', quotechar='"')
                for entry in data1:
                    print(entry[0])
                    print(entry[3])
                    if entry[0] != 'section':
                        paperList[entry[3]] = entry

        # Append to the CSV
        with open(r'review-search-deduped.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            for (key, value) in paperList.items():
                # Too many papers - filter out any before 2016
                try:
                    #if int(value[5]) > 2016 and int(value[5]) < 2019:
                    if int(value[5]) > 2016:
                        writer.writerow(value)
                except:
                    print('Bad date, skipping...')
                    print(value)

        print('Done.')

    def getSearchString(self, primaryOrSecondary, database):
        # TODO: Return a boolean search string for the database specified.
        # primaryOrSecondary determines whether to use just the primary search terms or combine them with the secondaryTerms
        pass

    def getConfig(self):
        # Get the config file details (database login)
        d = {}
        with open(".config") as f:
            for line in f:
                (key, val) = line.split(':')
                d[key] = val.replace('\n', '').strip()

            return d

Litfetch()
