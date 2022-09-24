from distutils.log import error
import json
import csv
import argparse
import pandas as pd
import time
import re

def find_author_id(author):
    id = author['uuid']
    if 'ids' in author.keys():
        #loop over for INSPIRE BAI id
        for cid in author['ids']:
            if cid['schema'] == 'INSPIRE BAI':
                id = cid['value']
    return id

def check_duplicate_inst(inst, list_insts):
    is_dupl=False
    code = inst['code']
    name = inst['name']
    if (inst['code'] != 0):
        #valid code present, check for duplicates
        if inst['code'] in list_insts.values():
            is_dupl = True
            #find index of institution with this code
            idx_inst = list(list_insts.values()).index(inst['code'])
            key_inst = list(list_insts.keys())[idx_inst]
            if key_inst != name:
                #mismatch of name. Keep original and print warning.
                print('Mismatch of institute name with same code. Keeping "{}" over "{}"'.format(key_inst, inst['name']))
                name = key_inst
    else:
        #check duplicates by name and manual fixing
        if inst['name'] in list_insts.keys():
            is_dupl = True
            if list_insts[inst['name']] == 0:
                #update code
                list_insts[inst['name']] = inst['code']
            elif (code > 0) and (list_insts[inst['name']] != code):
                #mistmatch of codes. Should really never happen
                print('Mismatch of institute code with same name. Keeping {} over {}'.format(list_insts[inst['name']], code))
                code = list_insts[inst['name']]
            elif code == 0:
                code = list_insts[inst['name']]
                
    return is_dupl, name, code

def check_duplicate_author(author, list_authors):
    is_dupl=False
    code = author['code']
    name = author['full_name']
    if (code != 0):
        #valid code present, check for duplicates
        idx_author = next((i for i,item in enumerate(list_authors) if item['code'] == code), None)
        if idx_author != None:
            is_dupl = True
            if list_authors[idx_author]['full_name'] != name:
                #mismatch of name. Keep original and print warning.
                print('Mismatch of author name with same code. Keeping "{}" over "{}"'.format(list_authors[idx_author]['full_name'], name))
                name = list_authors[idx_author]['full_name']
            #TODO: possibly check if list of affiliations is different and merge
    else:
        #check duplicates by name and manual fixing
        idx_author = next((i for i,item in enumerate(list_authors) if item['full_name'] == name), None)
        if idx_author != None:
            #potential duplicate, but might also be genuinly a different author
            print('=== Potential duplicate for check:')
            print(author)
            print(list_authors[idx_author])
            print('===')
                
    return is_dupl, name, code

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse JSON file from google drive and output unique entries')
    cmdParser.add_argument('input_file', metavar='inputFile', type=str, help='Input JSON file')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-bsm-unique-authors.csv', help='Output CSV file')
#    cmdParser.add_argument('--output_tex', dest='output_tex', type=str, default='sm21-bsm-unique-authors.tex', help='Output TEX file')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    #load data in a dataframe
    if cmdArgs.debug > 0:
        print('Loading input files: ', cmdArgs.input_file)
    papers = pd.read_json(cmdArgs.input_file)

    ## create list of unique authors
    u_institutions = {} #store list of unique institutions: [name: code]
    u_authors = [] #store dict of unique authors: [first_name, last_name, full_name, code, institutions: [name, code]] 
    for idx_paper, p in papers.iterrows():
        if cmdArgs.debug > 1:
            print('Checking paper', p['arxiv'])
        if (cmdArgs.debug > 5):
            print(p)
        #now look over authors
        for author in p['authors_dicts']:
            if cmdArgs.debug > 6:
                print('Checking author', author['full_name'])
                if cmdArgs.debug > 10:
                    print(author)
            a = {}
            a['full_name'] = author['full_name'] 
            a['first_name'] = a['full_name'].split(',')[1].strip()
            a['last_name'] = a['full_name'].split(',')[0].strip()
            a['code'] = find_author_id(author)
            a['institutions'] = []
            if not 'affiliations' in author.keys():
                author['affiliations'] = [] #no affiliations
            for inst in author['affiliations']:
                out_inst = {}
                out_inst['name'] = inst['value']
                out_inst['code'] = inst['record']['$ref'].split('/')[-1] #(0 if not available)
                #check if this institution exists already and, if not, add it (note: use the returned values to allow common parsing/fixing)
                is_dupl, name, code = check_duplicate_inst(out_inst, u_institutions)
                if not is_dupl:
                    #new institution, add it
                    u_institutions[name] = code
                else:
                    #check if code information can be updated
                    if (u_institutions[name] == 0):
                        #updated institution code
                        u_institutions[name] = code

                if cmdArgs.debug > 2:
                    print('Adding new institution:', out_inst['name'])
                a['institutions'].append(out_inst)
            #now check the author (after institution, since in some papers one might be lsited with multiple inst.)
            is_dupl, name, code = check_duplicate_author(a, u_authors)
            a['full_name'] = name
            a['code'] = code
            if not is_dupl:
                if cmdArgs.debug > 2:
                    print('Adding new author:', a['full_name'])
                u_authors.append(a) #so that we can decide what to write inside the check_duplicate_author function

    ## Stat
    print('Number of unique authors: {:d}'.format(len(u_authors)))

    ## now create author list and save to output CSV
    print('Saving authors to: ', cmdArgs.output_file)
    with open(cmdArgs.output_file, 'w') as output_file:
        csvWriter = csv.DictWriter(output_file, fieldnames=u_authors[0].keys())
        csvWriter.writeheader()
        for data in u_authors:
            csvWriter.writerow(data)
    
    print('Saving institutions to: ', 'institutions.csv')
    with open('institutions.csv', 'w') as output_file:
        csvWriter = csv.DictWriter(output_file, fieldnames=['code', 'name'])
        csvWriter.writeheader()
        for k in u_institutions:
            csvWriter.writerow({'code': u_institutions[k], 'name': k})
    

    #u_authors.to_csv(cmdArgs.output_file,index=False) # if it were a DataFrame..

    ## now save author list as tex as well
    #print('Saving TEX file with authors')
    #with open(cmdArgs.output_tex) as f_tex:
    