from distutils.log import error
import csv
import argparse
import pandas as pd
import time
import re

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse CSV file from google drive and output unique entries')
    cmdParser.add_argument('input_files', metavar='inputFile', type=str, nargs='+', help='Input CSV file(s)')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-lbl-unique-papers-metadata.csv', help='Output CSV file')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    #load data in a dataframe
    if cmdArgs.debug > 0:
        print('Loading input files: ', cmdArgs.input_files)
    papers = pd.concat(pd.read_csv(f, dtype={'arxiv': str, 'frontier': str, 'title': str, 'LBL direct role?': str, 'lbl_authors': str, 'lbl_inst': str}) for f in cmdArgs.input_files)

    #now make unique (in arxiv number) rows and make an "OR" of the 'LBL direct role?' column
    paper_merge = {'arxiv': 'first', 'frontier': ','.join, 'title':'first', 'LBL direct role?': 'any','lbl_authors': 'first', 'lbl_inst': 'first'}
    out_papers = papers.groupby(papers['arxiv']).aggregate(paper_merge)

    #retrieve statistics
    print('=== Statistics')
    ## number of LBNL papers per frontier (note: using out_papers, but allowing per-frontier duplicates since the 'frontier' field is a merge)
    print('Papers with LBNL author per frontier:')
    for f in ['AF', 'CEF', 'CF', 'COMPF','EF', 'IF', 'NF', 'RF','TF','UF']:
        if cmdArgs.debug > 5:
            print('Processing frontier', f)
            print(out_papers[out_papers['frontier'].str.contains(f)].head())
        n = len(out_papers[out_papers['frontier'].str.contains(f)])
        print('- {frontier}: {number:d}'.format(frontier=f, number=n))
    total_unique = len(out_papers)
    print('- Total unique: {number:d}'.format(number=total_unique))

    ## number of LBNL papers leading contrib
    print('Papers with LEADING/SUBSTANTIAL LBNL contribution per frontier:')
    for f in ['AF', 'CEF', 'CF', 'COMPF','EF', 'IF', 'NF', 'RF','TF','UF']:
        if cmdArgs.debug > 5:
            print('Processing frontier', f)
            print(out_papers[out_papers['frontier'].str.contains(f)].head(10))
        n = len(out_papers[ (out_papers['frontier'].str.contains(f)) & (out_papers['LBL direct role?'])])
        print('- {frontier}: {number:d}'.format(frontier=f, number=n))
    total_unique = len(out_papers[out_papers['LBL direct role?']])
    print('- Total unique: {number:d}'.format(number=total_unique))    
    
    ## number of unique LBNL authors
    all_authors = set()
    for a in out_papers['lbl_authors']:
        if str(a).startswith('['):
            #list if authors, interpret as a list
            la = list(a)
            for new_author in la:
                all_authors.add(str(new_author))
        else:
            #simple comma-separated list
            la = str(a).split(',')
            for new_author in la:
                all_authors.add(str(new_author).strip())
    print('Number of unique LBNL authors: {:d}'.format(len(all_authors)))

    print('Saving selected papers to: ', cmdArgs.output_file)
    out_papers.to_csv(cmdArgs.output_file,index=False)
    