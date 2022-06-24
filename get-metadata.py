from distutils.log import error
import requests
import csv
import argparse
import pandas as pd
import time
import re

#inspire codes for LBL
inst_LBL_codes = [1189711, 902953, 911528]

#possible  affiliation strings for LBL
inst_LBL_str = ['LBNL', 'LBL', 'Lawrence Berkeley']

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse CVS files and gather metadata')
    cmdParser.add_argument('input_files', metavar='inputFile', type=str, nargs='+', help='Input CSV file(s)')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-lbl-papers-metadata.csv', help='Output CSV file with metadata')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    #load data in a dataframe
    if cmdArgs.debug > 0:
        print('Loading input files: ', cmdArgs.input_files)
    papers = pd.concat(pd.read_csv(f, dtype={'arxiv': str, 'frontier': str, 'also': str}) for f in cmdArgs.input_files)

    #explicitly add new columns we'd like to fill
    papers['title'] = '' #title of papers
    papers['lbl_authors'] = [[] for _ in range(len(papers))] #list of LBL-affiliated authors
    papers['lbl_inst'] = [[] for _ in range(len(papers))] #list of actual institution, as spelled on inspire
    papers['lbl_inst_code'] = [[] for _ in range(len(papers))] #list of corresponding institution INSPIRE ID, if available

    #now loop over records and retrieve metadata, carefully filling all entries with the same arxiv number
    errorsRetrival=[]
    nPapersProcessed = 0
    if cmdArgs.debug > 2:
        papers.head()
    for index, p in papers.iterrows():
        nTries=0
        nPapersProcessed = nPapersProcessed + 1
        if (nPapersProcessed % 50 == 0):
            print('Processed {:d}/{:d} papers'.format(nPapersProcessed, len(papers)))
        if cmdArgs.debug > 1:
            print('Processing ', p['arxiv'])

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

            author_list = metadata['metadata']['authors']
            isLBLPaper=False
            for author in author_list:
                if cmdArgs.debug > 10:
                    print('Processing author: ', author)
                #get institution names and codes, to check for LBL affiliation
                isLBL=False
                found_inst_str=''
                found_inst_code=0
                if not 'affiliations' in author:
                    #no affiliation information found, skip it
                    if cmdArgs.debug > 11:
                        print('No affiliation found. Skip.')
                    continue
                for inst in author['affiliations']:
                    #retrieve institution name and code
                    if cmdArgs.debug > 13:
                        print('Checking institution: ', inst)
                    inst_name = inst['value']
                    try:
                        inst_code = int(inst['record']['$ref'].split('/')[-1])
                    except:
                        #invalid institution code, it's ok
                        if cmdArgs.debug > 13:
                            print('Invalid or missing institution code. Ok.')
                        inst_code = 0

                    if cmdArgs.debug > 11:
                        print('Checking affiliation:', inst)
                    #check if it's a known LBL institution spelling or code
                    if inst_code in inst_LBL_codes: isLBL=True
                    for lbl_name in inst_LBL_str:
                        if re.search(lbl_name, inst_name, re.IGNORECASE): isLBL=True

                    if isLBL:
                        found_inst_str = inst_name
                        found_inst_code = inst_code
                        break #stop loop over affiliations
                    
                #if not LBL author, check next one
                if cmdArgs.debug > 10:
                    print('Found?', isLBL)
                if not isLBL: continue

                #add info to the output record
                isLBLPaper=True
                p['lbl_authors'].append(author['full_name'])
                p['lbl_inst'].append(found_inst_str)
                p['lbl_inst_code'].append(found_inst_code)

            if isLBLPaper:
                #add also title information, if available
                if ('titles' in metadata['metadata']):
                    titles = metadata['metadata']['titles']
                    p['title'] = titles[0]['title'] #take first title occurrence

            #break while loop of attempts
            break


    #Re-format first the authors for convenience
    #papers.assign(lbl_authors_str = lambda x: ', '.join(x.lbl_authors))

    # select LBL papers only
    lbl_papers = papers[papers.lbl_authors.astype(bool)]
    lbl_papers.reset_index()

    #print stat
    print('== Summary ==')
    print('Processed entries: ', len(papers))
    print('Selected LBL papers: ', len(lbl_papers))
    print('Errors: ', len(errorsRetrival))
    if (len(errorsRetrival) > 0):
        print(' ', errorsRetrival)

    #write output to csv
    print('Saving selected papers to: ', cmdArgs.output_file)
    lbl_papers.to_csv(cmdArgs.output_file,index=False,columns=['frontier','arxiv','title','lbl_authors','lbl_inst'])

        
