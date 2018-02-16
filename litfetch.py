#!/usr/bin/env python3

"""
@author: rob.dunne@manchester.ac.uk
Fetch a list of research papers from computer science research literature databases based on specified search terms.
Databases: Google Scholar, ACM digital library, IEEE Xplore, ScienceDirect, SpringerLink, and Wiley Online Library.

Useful list of APIs for further expansion: https://libraries.mit.edu/scholarly/publishing/apis-for-scholarly-resources/
"""

import urllib
import urllib.parse
from bs4 import BeautifulSoup, SoupStrainer
import time
import csv
import contextlib
from habanero import Crossref
import json
import requests
import pymysql.cursors
import re
import xml.etree.ElementTree as ET

class Litfetch():
    # Constructor
    def __init__(self):
        # Print the notice
        self.programNotice()

        # Set the search terms
        self.config = self.getConfig()
        self.searchLimit = 1000
        self.startYear = '2005'
        self.endYear = '2014'
        self.searchString = '((predict OR predicting OR prediction) AND arousal) OR ((detect OR detecting OR detection) AND arousal) OR ((sense OR sensing) AND arousal) OR ((measure OR measuring) AND arousal) OR ((capture OR capturing) AND arousal)'
        #self.searchString = '(human OR people OR person) AND (behaviour OR behavior OR action OR activity) AND (prediction OR predicting OR forecast OR forecasting) AND (algorithm OR method OR technique OR learning) AND ("smart home" OR "smart environment" OR "smart homes" OR "smart environments" OR "ambient intelligence")'
        #self.searchString = 'behaviour prediction smart home'

        # Perform the search
        self.fetchPapers()

    def fetchPapers(self):
        # Databases selection
        selection = input('\nPlease select an option:\n 0. run search\n 1. de-duplicate papers\n 2. grey literature\n 3. de-duplicate grey literature\n 4. exit\n\n> ')
        print('You selected: '+selection)

        if selection == '0':
            """
            print('Searching Google Scholar...')
            print('Page results are retrieved with a 5 second delay to prevent blocking of the web scraper.')
            try:
                self.googleScholar()
            except Exception as e:
                print('Google Scholar failed because: '+str(e))

            print('Searching ACM Digital Library...')
            try:
                self.acmDL()
            except Exception as e:
                print('ACM Digital Libraryfailed because: '+str(e))

            print('Searching IEEE Xplore...')
            try:
                self.ieeeXplore()
            except Exception as e:
                print('IEEE Xplore failed because: '+str(e))

            print('Searching ScienceDirect...')
            try:
                self.scienceDirect()
            except Exception as e:
                print('ScienceDirect failed because: '+str(e))

            print('Searching SpringerLink...')
            try:
                self.springerLink()
            except Exception as e:
                print('SpringerLink failed because: '+str(e))

            print('Searching Wiley Online Library...')
            try:
                self.wileyOL()
            except Exception as e:
                print('Wiley Online Library failed because: '+str(e))
            """
            print('Searching PubMed...')
            try:
                self.pubmed()
            except Exception as e:
                print('PubMed failed because: '+str(e))

        elif selection == '1':
            # Write a de-duplicated list as a CSV
            print('De-duplicating list of papers...')
            self.deDuplicatePapers()

        elif selection == '2':
            # Search grey literature
            print('Searching grey literature...')
            self.researchGate()
            self.arxiv()
            self.zenodo()

        elif selection == '3':
            # De-duplicate grey literature
            print('De-duplicating grey literature...')
            self.deDuplicateGrey()

        elif selection == '4':
            print('Goodbye.')
            exit()
        else:
            print('Uh oh, I don\'t know what '+selection+' is?')

    def googleScholar(self):
        # Reset the file
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-google.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-google.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        print('Searching Google Scholar for: '+self.searchString+'.')
        print('Found:')

        pageResults = self.searchLimit/10
        for i in range(int(pageResults)):
            page = 10*i
            searchURL = 'https://scholar.google.co.uk/scholar?q='+urllib.parse.quote_plus(self.searchString)+'&hl=en&as_sdt=0%2C5&as_ylo='+self.startYear+'&as_yhi='+self.endYear+'&start='+str(page)
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

                    findYear = re.findall(r'.*([1-3][0-9]{3})', paperAuthors)
                    if findYear:
                        paperYear = findYear[0]

                    resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'Google Scholar', paperSource]

                    # Append to the CSV
                    with open(r'review-search-google.csv', 'a', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(resultRow)

            # Sleep to prevent bot blocking
            time.sleep(5)

            print('-----------')
            print('Done.')

    def acmDL(self):
        # Using Crossref API: https://github.com/sckott/habanero
        cr = Crossref()

        # Reset the file
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-acm.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-acm.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        print('Searching ACM via Crossref for: '+self.searchString+'.')
        print('Found:')

        results = cr.works(query=self.searchString, limit=self.searchLimit, order='desc', filter={'from-pub-date':self.startYear, 'member': '320'})
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

            resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'ACM - Crossref', paperSource]

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
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-ieee.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-ieee.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        print('Searching IEEEvia Crossref for: '+self.searchString+'.')
        print('Found:')

        results = cr.works(query=self.searchString, limit=self.searchLimit, order='desc', filter={'from-pub-date':self.startYear, 'member': '263'})
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

            resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'IEEE - Crossref', paperSource]

            # Append to the CSV
            with open(r'review-search-ieee.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(resultRow)

        print('Done.')

    def scienceDirect(self):
        # https://api.elsevier.com/content/search/scidir?apiKey='+self.config['sdKey']+'&query=
        # Reset the file
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-sciencedirect.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-sciencedirect.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        print('Searching ScienceDirect for: '+self.searchString+'.')
        print('Found:')

        searchLimit = self.searchLimit
        if searchLimit > 500:
            searchLimit = 500

        searchURL = 'https://api.elsevier.com/content/search/scidir?apiKey='+self.config['sdKey']+'&count='+str(searchLimit)+'&sort=-date&httpAccept=application%2Fjson&query='+urllib.parse.quote_plus(self.searchString)
        print(searchURL)
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

            resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'ScienceDirect', paperSource]

            # Append to the CSV
            with open(r'review-search-sciencedirect.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(resultRow)

        print('Done.')

    def springerLink(self):
        # 'http://api.springer.com/metadata/json?api_key='+self.config['springerKey']+'&p=30&q='+searchString+' sort:date'
        # Reset the file
        # PUBLICATION DATES ARE INCORRECT IN THE SPRINGER API
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-springer.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-springer.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        print('Searching SpringerLink for: '+self.searchString+'.')
        print('Found:')

        searchURL = 'http://api.springer.com/metadata/json?api_key='+self.config['springerKey']+'&p='+str(self.searchLimit)+'&q='+urllib.parse.quote_plus(self.searchString)+' sort:date'
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

            resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'Springer', paperSource]

            # Append to the CSV
            with open(r'review-search-springer.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(resultRow)

        print('Done.')

    def wileyOL(self):
        # Using Crossref API: https://github.com/sckott/habanero
        cr = Crossref()

        # Reset the file
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-wiley.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-wiley.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Get the Google scholar papers
        print('Searching Wiley-Blackwell via Crossref for: '+self.searchString+'.')
        print('Found:')

        results = cr.works(query=self.searchString, limit=self.searchLimit, order='desc', filter={'from-pub-date':self.startYear, 'member': '311'})
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

            resultRow = [time.strftime("%d/%m/%Y"), paperTitle, paperAuthors, paperYear, 'Wiley - Crossref', paperSource]

            # Append to the CSV
            with open(r'review-search-wiley.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(resultRow)

        print('Done.')

    def pubmed(self):
        searchURL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="+urllib.parse.quote(self.searchString)+"&retmode=json&retmax="+str(self.searchLimit)

        with urllib.request.urlopen(searchURL) as url:
            data = json.loads(url.read().decode())

            # Reset the file
            csvHeader = ['searched','title','authors','published','database','source']
            f = open('review-search-pubmed.csv', "w+")
            f.close()
            # Append to the CSV
            with open(r'review-search-pubmed.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(csvHeader)

            # Append to the CSV
            with open(r'review-search-pubmed.csv', 'a', encoding='utf-8') as f:
                print('Adding PubMed papers to review-search-pubmed.csv')
                writer = csv.writer(f)
                for item in data['esearchresult']['idlist']:
                    with urllib.request.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id='+str(item)) as url2:
                        paper = json.loads(url2.read().decode())
                        try:
                            print(paper['result'][str(item)]['title'])
                            pY = paper['result'][str(item)]['pubdate']
                            pY2 = pY.split(' ')
                            paperYear = pY2[0]

                            writer.writerow([time.strftime("%d/%m/%Y"), paper['result'][str(item)]['title'], paper['result'][str(item)]['authors'][0]['name'], paperYear, 'PubMed', 'https://www.ncbi.nlm.nih.gov/pubmed/'+str(item)])
                        except Exception as exception:
                            print(exception)

        print('PubMed done.')

    def researchGate(self):
        searchURL = "https://www.researchgate.net/search.SearchBox.loadMore.html?type=publication&query="+urllib.parse.quote(self.searchString)+"&offset=0&limit="+str(self.searchLimit)+"&viewId=IDlNl4Vyl3nQ7giYvShhPkj1dMkru0GibMJ3&iepl%5BgeneralViewId%5D=YQZWEQPe4YAuAN1ntHw4KLcXcJGRwZ1Eztzq&iepl%5Bcontexts%5D%5B0%5D=searchReact&subfilter"

        with urllib.request.urlopen(searchURL) as url:
            data = json.loads(url.read().decode())

            # Reset the file
            csvHeader = ['Searched','Title','Authors','Published','Type','Include?','Exclusion code','Database','Source']
            f = open('review-search-researchgate.csv', "w+")
            f.close()
            # Append to the CSV
            with open(r'review-search-researchgate.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(csvHeader)

            # Append to the CSV
            with open(r'review-search-researchgate.csv', 'a', encoding='utf-8') as f:
                print('Adding ResearchGate papers to review-search-researchgate.csv')
                writer = csv.writer(f)
                for item in data['result']['searchSearch']['publication']['items']:
                    try:
                        writer.writerow([time.strftime("%d/%m/%Y"), item['title'], item['authors'][0]['name'], item['metaItems'][0]['label'], item['type'], '', '', 'ResearchGate', 'https://www.researchgate.net/'+item['urls']['CTA']])
                    except Exception as exception:
                        print(exception)

        print('ResearchGate done.')

    def arxiv(self):
        searchURL = "http://export.arxiv.org/api/query?search_query=all:"+self.searchString+"&start=0&max_results="+str(self.searchLimit)
        #searchURL = "http://export.arxiv.org/api/query?search_query=all:"+urllib.parse.quote('Human behaviour behavior predict smart home ambient intelligence')+"&start=0&max_results=100"

        xml = requests.get(searchURL).text

        # Reset the file
        csvHeader = ['Searched','Title','Authors','Published','Type','Include?','Exclusion code','Database','Source']
        f = open('review-search-arxiv.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-arxiv.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Append to the CSV
        with open(r'review-search-arxiv.csv', 'a', encoding='utf-8') as f:
            print('Adding arXiv papers to review-search-arxiv.csv')
            writer = csv.writer(f)
            xmlstring = re.sub(' xmlns="[^"]+"', '', xml, count=1)
            root = ET.fromstring(xmlstring)

            for item in root:
                if item.tag == 'entry':
                    entry = item
                    try:
                        writer.writerow([time.strftime("%d/%m/%Y"), entry[3].text, entry[5][0].text, entry[2].text, '-', '', '', 'arXiv', entry[0].text])
                    except Exception as exception:
                        print(exception)

        print('arXiv done.')

    def zenodo(self):
        searchURL = "https://zenodo.org/api/records/?q="+urllib.parse.quote(self.searchString)+"&size="+str(self.searchLimit)
        #searchURL = "https://zenodo.org/api/records/?size=100q="+urllib.parse.quote('Human behaviour behavior predict smart home ambient intelligence')

        with urllib.request.urlopen(searchURL) as url:
            data = json.loads(url.read().decode())

            # Reset the file
            csvHeader = ['Searched','Title','Authors','Published','Type','Include?','Exclusion code','Database','Source']
            f = open('review-search-zenodo.csv', "w+")
            f.close()
            # Append to the CSV
            with open(r'review-search-zenodo.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(csvHeader)

            # Append to the CSV
            with open(r'review-search-zenodo.csv', 'a', encoding='utf-8') as f:
                print('Adding Zenodo papers to review-search-zenodo.csv')
                writer = csv.writer(f)
                for item in data['hits']['hits']:
                    try:
                        writer.writerow([time.strftime("%d/%m/%Y"), item['metadata']['title'], item['metadata']['creators'][0]['name'], item['metadata']['publication_date'], item['metadata']['resource_type']['subtype'], '', '', 'Zenodo', item['links']['html']])
                    except Exception as exception:
                        print(exception)

        print('Zenodo done.')

    def deDuplicatePapers(self):
        totalRows = 0
        deDupedRows = 0
        # Reset the file
        csvHeader = ['searched','title','authors','published','database','source']
        f = open('review-search-deduped.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-deduped.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Combine and remove duplicates from the database CSVs. Write one file.
        files = ['google', 'sciencedirect', 'springer', 'wiley', 'acm', 'ieee', 'pubmed']
        paperList = {}

        for csvData in files:
            with open('review-search-'+csvData+'.csv', newline='') as csvfile1:
                print('Deduplicating review-search-'+csvData+'.csv')
                data1 = csv.reader(csvfile1, delimiter=',', quotechar='"')
                for entry in data1:
                    # Skip the header
                    if entry[0] != 'searched':
                        # Add the row to a dictionary - duplicate keys (paper titles) are overwritten, thus deduplicating.
                        #if 'predict' in entry[1] or 'forecast' in entry[1]: # Inclusion criteria 1, IC1.
                        if 'arousal' in entry[1] and ('detect' in entry[1] or 'predict' in entry[1] or 'captur' in entry[1] or 'sens' in entry[1] or 'measur' in entry[1]): # Inclusion criteria
                            # Filter by year
                            if int(entry[3]) > 2004 and int(entry[3]) < 2015:
                                paperList[entry[1]] = entry

                        totalRows = totalRows+1

        # Append to the CSV
        with open(r'review-search-deduped.csv', 'a', encoding='utf-8') as f:
            print('Adding de-duplicated papers to review-search-deduped.csv')
            writer = csv.writer(f)
            for (key, value) in paperList.items():
                writer.writerow(value)
                deDupedRows = deDupedRows+1

        print('Done.')
        print('Total papers: '+str(totalRows))
        print('De-duplicated papers: '+str(deDupedRows))

    def deDuplicateGrey(self):
        totalRows = 0
        deDupedRows = 0
        # Reset the file
        csvHeader = ['Searched','Title','Authors','Published','Type','Include?','Exclusion code','Database','Source']
        f = open('review-search-deduped-grey.csv', "w+")
        f.close()
        # Append to the CSV
        with open(r'review-search-deduped-grey.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csvHeader)

        # Combine and remove duplicates from the database CSVs. Write one file.
        files = ['researchgate', 'arxiv', 'zenodo']
        paperList = {}

        for csvData in files:
            with open('review-search-'+csvData+'.csv', newline='') as csvfile1:
                print('Deduplicating review-search-'+csvData+'.csv')
                data1 = csv.reader(csvfile1, delimiter=',', quotechar='"')
                for entry in data1:
                    # Skip the header
                    if entry[0] != 'searched':
                        # Add the row to a dictionary - duplicate keys (paper titles) are overwritten, thus deduplicating.
                        #if 'predict' in entry[1] or 'forecast' in entry[1]: # Inclusion criteria 1, IC1.
                        paperList[entry[1]] = entry

                        totalRows = totalRows+1

        # Append to the CSV
        with open(r'review-search-deduped-grey.csv', 'a', encoding='utf-8') as f:
            print('Adding de-duplicated grey literature to review-search-deduped-grey.csv')
            writer = csv.writer(f)
            for (key, value) in paperList.items():
                writer.writerow(value)
                deDupedRows = deDupedRows+1

        print('Done.')
        print('Total grey literature papers: '+str(totalRows))
        print('De-duplicated grey literature papers: '+str(deDupedRows))

    def getSearchString(self, primaryOrSecondary, database):
        # TODO: Return a boolean search string for the database specified.
        # primaryOrSecondary determines whether to use just the primary search terms or combine them with the secondaryTerms
        # Search terms are contained in files ./searchterms/primary.csv and ./searchterms/secondary.csv
        pass

    def getConfig(self):
        # Get the config file details
        d = {}
        with open(".config") as f:
            for line in f:
                (key, val) = line.split(':')
                d[key] = val.replace('\n', '').strip()

            return d

    def programNotice(self):
        print('****************************************************************')
        print('*** Computer Science database search script. UoM CS, 2018    ***')
        print('*** This software is provided as is, under an MIT licence    ***')
        print('****************************************************************')

Litfetch()
