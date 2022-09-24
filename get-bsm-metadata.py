from distutils.log import error
import requests
import csv
import argparse
import pandas as pd
import time
import re
import json
import ast

#inspire codes for LBL
ef_groups = ['EF08', 'EF09', 'EF10'] #, EF00
checkAlsoSecondaryGroups=True #count a paper even if not the primary group 
maxNumberOfAuthors = 20

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse CVS files and gather metadata. Filter entries for selected EF groups.')
    cmdParser.add_argument('input_files', metavar='inputFile', type=str, nargs='+', help='Input CSV file(s)')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-bsm-papers-metadata.json', help='Output JSON file with metadata')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    #load data in a dataframe
    if cmdArgs.debug > 0:
        print('Loading input files: ', cmdArgs.input_files)
    papers = pd.concat(pd.read_csv(f, dtype={'arxiv': str, 'frontier': str, 'also': str}) for f in cmdArgs.input_files)

    #explicitly add new columns we'd like to fill
    papers['title'] = ['' for _ in range(len(papers))] #title of papers
    papers['authors_dicts'] = [[] for _ in range(len(papers))] #Authors
    papers['selected'] = [False for _ in range(len(papers))]

    #now loop over records and retrieve metadata, carefully filling all entries with the same arxiv number
    #selectedPapers = pd.DataFrame(columns=papers.columns, dtype={'arxiv':str, 'frontier':str, 'also':str, 'title':str, 'authors_dicts':str, 'selected':bool}, copy=False)
    #selectedPapers = pd.DataFrame(columns=papers.columns, copy=False)
    errorsRetrival=[] #keep track of errors retrieving metadata
    maxAuthors=[] #keep track of papers with too many authors
    nPapersProcessed = 0
    if cmdArgs.debug > 2:
        papers.head()
    for index, p in papers.iterrows():
        nTries=0
        nPapersProcessed = nPapersProcessed + 1
        if (nPapersProcessed % 10 == 0):
            print('Processed {:d}/{:d} papers'.format(nPapersProcessed, len(papers)))
        if cmdArgs.debug > 1:
            print('Processing ', p['arxiv'])

        #first, filter by EF group
        passEFGroupFilter=False
        if p['frontier'] in ef_groups:
            passEFGroupFilter=True
        elif checkAlsoSecondaryGroups:
            if not p['also'] == '':
                papers.at[index,'also'] = [] #initialize as empty list
            else:
                papers.at[index,'also'] = ast.literal_eval(p['also']) #convert to actual list
            for grp in papers.at[index,'also']:
                if grp in ef_groups:
                    passEFGroupFilter=True
        if not passEFGroupFilter:
            if (cmdArgs.debug > 5):
                print('Paper did not pass EF frontier filter:', p['arxiv'])
            continue

        #now, retrieve metadata and check authors and store the additional information
        passAuthorFilter=False
        metadata={}
        while True:
            #time.sleep(0.2) #wait a bit to satisfy the max 15 requests per 5 seconds limit
            nTries = nTries + 1
            #get metadata using INSDPIRE REST-API
            url = "https://inspirehep.net/api/arxiv/"+str(p['arxiv'])
            if cmdArgs.debug > 5:
                print('Get meadata: ', url)
            metadata = requests.get(url).json()
            #check for errors
            if 'status' in metadata:
                if cmdArgs.debug > 5:
                    print(metadata['status'])
                if int(metadata['status']) > 100:
                    print('ERROR retrieving information for {}. Error {}: {}'.format(p['arxiv'], metadata['status'], metadata['message']))
                    if (nTries >= 3):
                        #mas tries
                        print('ERROR. Giving up after max tries.')
                        errorsRetrival.append(p['arxiv'])
                        break
                    time.sleep(1) #wait one second, then retry
                    continue

            #successfully retrieved metadata
            if (not 'metadata' in metadata) or (not 'authors' in metadata['metadata']):
                if cmdArgs.debug > 0:
                    print('Cannot find authors information for paper:', p['arxiv'])
                    if (cmdArgs.debug > 1):
                        print(p)
                    errorsRetrival.append(p['arxiv'])
                    break #skip to next record

            #add also title information, if available
            if ('titles' in metadata['metadata']):
                titles = metadata['metadata']['titles']
                papers.at[index,'title'] = titles[0]['title'] #take first title occurrence

            #now filter by maximum number of authors
            author_list = metadata['metadata']['authors']
            if len(author_list) > maxNumberOfAuthors:
                if (cmdArgs.debug > 1):
                    print('Maximum number of authors exceeded for paper: {} ({})'.format(p['arxiv'], p['title']))
                maxAuthors.append(p)
                break #skip to next record
            
            #ok, add the additional fields we need
            passEFGroupFilter=True
            papers.at[index,'authors_dicts'] = author_list
            papers.at[index,'selected'] = True

            break #break loop of attempts
            
        #if a valid record was found, store it in the output dictionary
        if not passEFGroupFilter:
            continue
            
    #print stat
    print('== Summary ==')
    print('Processed entries: ', len(papers))
    print('Selected BSM papers: ', len(papers[papers.selected == True]))
    print('Exceeding max Authors (but passing EF groups selection): ', len(maxAuthors))
    for p in maxAuthors:
        print(' - {}, {}'.format(p['arxiv'],p['title']))
    print('Errors: ', len(errorsRetrival))
    if (len(errorsRetrival) > 0):
        print(' ', errorsRetrival)

    #write output to json
    print('Saving selected papers to: ', cmdArgs.output_file)
    with open(cmdArgs.output_file, 'w') as fout:
        raw_json = papers[papers.selected == True].to_json()
        txt_json = json.loads(raw_json)
        json.dump(txt_json, fout, indent=3)
