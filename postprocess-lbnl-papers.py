from distutils.log import error
import requests
import csv
import argparse
import pandas as pd
import time
import re

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse CSV file from google drive and output unique entries')
    cmdParser.add_argument('input_files', metavar='inputFile', type=str, nargs='+', help='Input CSV file(s)')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-lbl-papers-metadata.csv', help='Output CSV file')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    #load data in a dataframe
    if cmdArgs.debug > 0:
        print('Loading input files: ', cmdArgs.input_files)
    papers = pd.concat(pd.read_csv(f, dtype={'arxiv': str, 'frontier': str, 'also': str}) for f in cmdArgs.input_files)

    #now make unique (in arxiv number) rows and make an "OR" of the 'LBL direct role?' column
    arxiv_list = papers['arxiv'].unique()

    paper_merge = {'arxiv': 'first', 'frontier': 'first', 'title':'first', 'LBL direct role?': 'any','lbl_authors': 'first', 'lbl_inst': 'first'}
    out_papers = papers.groupby(papers['arxiv']).aggregate(paper_merge)

    print(out_papers)
    print('Saving selected papers to: ', cmdArgs.output_file)
    out_papers.to_csv(cmdArgs.output_file,index=False)
     