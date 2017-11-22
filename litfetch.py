#!/usr/bin/env python3

"""
@author: rob.dunne@manchester.ac.uk
Fetch a list of literature based on specified search terms from computer science research literature databases.
"""

import urllib
from bs4 import BeautifulSoup, SoupStrainer
import time
import csv
import contextlib

class Letfetch():
    # Constructor
    def __init__(self):
        # Set the search terms
        self.startYear = '2011'
        self.endYear = '2017'
        self.searchTerms = ['ambient intelligence', 'ambient system', 'smart environment']
        self.secondaryTerms = [['home','domestic'],['care', 'elderly', 'assisted living', 'assistive'],['healthcare','health','medical'],['shops','shopping','recommender systems','business'],['data','data management','AI','artificial intelligence'],['human','affective'],['social','economic','ethics','ethical']]

        # Depth of results
        self.maxResults = 30

        # Perform the search
        self.fetchPapers()

    def fetchPapers(self):
        # Call the database APIs and append to the CSV
        self.googleScholar()

        # Write a de-duplicated list as a CSV
        self.deDuplicatePapers()

    def googleScholar(self):
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
                        paperTitle = ''
                        paperAuthors = ''
                        paperYear = ''
                        paperSource = ''

                        for h3 in paper.find_all('h3'):
                            for title in h3.find_all('a', href=True):
                                print(title.text)
                                print(title['href'])

                                paperTitle = title.text
                                paperSource = title['href']

                        for author in paper.find_all("div", { "class" : "gs_a" }):
                            paperAuthors = author.text

                        yearParts = paperAuthors.split('-')
                        yearParts2 = yearParts[0].split(',')
                        for year in yearParts2:
                            paperYear = year

                        resultRow = [",".join(terms), time.strftime("%d/%m/%Y"), searchString, title.text, paperAuthors, paperYear, 'Google Scholar', paperSource, searchURL]

                        # Append to the CSV
                        with open(r'review-search.csv', 'a') as f:
                            writer = csv.writer(f)
                            writer.writerow(resultRow)

                # Sleep to prevent bot blocking
                time.sleep(1)

            print('-----------')

        # Append to the CSV

    def deDuplicatePapers(self):
        # Remove duplicates
        pass

Letfetch()
