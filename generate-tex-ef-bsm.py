from distutils.log import error
import json
import csv
import argparse
import pandas as pd
import time
import re
import ast



if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse JSON file from google drive and output unique entries')
    cmdParser.add_argument('--input-authors', dest='input_authors', type=str, help='Input CSV file with unique authors')
    cmdParser.add_argument('--input-additional-authors', dest='input_additional_authors', type=str, help='Input CSV file with unique additional authors')
    cmdParser.add_argument('--input-institutions', dest='input_institutions', type=str, help='Input CSV file with unique institutions')
    cmdParser.add_argument('--output-tex', dest='output_tex', type=str, default='sm21-bsm-unique-authors.tex', help='Output TEX file')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=1, help='Enable debug printout. Set to 0 for no un-necessary printout')
    cmdArgs = cmdParser.parse_args()

    print('Loading input file: ', cmdArgs.input_authors)
    authors = pd.read_csv(cmdArgs.input_authors)

    print('Loading input file: ', cmdArgs.input_additional_authors)
    additional_authors = pd.read_csv(cmdArgs.input_additional_authors,dtype={'full_name': str, 'simple_affiliation_2':str, 'simple_affiliation_1':str})


    print('Loading input file: ', cmdArgs.input_institutions)
    institutions = pd.read_csv(cmdArgs.input_institutions)

    out_tex = open(cmdArgs.output_tex, 'w')

    out_tex.write("\n\n\n %%List of institutions\n\n")
    #Now generate institution commands, based on their code.
    for idx_inst, inst in institutions.iterrows():
        out_tex.write('\\newcommand{{\\inst{0}}}{{\\Affil{{{1}}}}}\n'.format(inst['code'], inst['name']))

    out_tex.write("\n\n\n %%List of authors\n\n")

    for idx_auth, auth in authors.iterrows():
        auth['institutions'] = ast.literal_eval(auth['institutions'])
        out_tex.write('\\author{{{0}}}'.format(auth['full_name']))
        for inst in auth['institutions']:
            out_tex.write('\\inst{0}'.format(inst['code']))        
        out_tex.write('\n')

    print(additional_authors.tail())

    for idx_auth, auth in additional_authors.iterrows():
        out_tex.write('\\author{{{0}}}'.format(auth['full_name']))
        if (auth['simple_affiliation_1']):
            out_tex.write('\\inst{0}'.format(auth['simple_affiliation_1']))
        if (str(auth['simple_affiliation_2']) and str(auth['simple_affiliation_2']) != 'nan'):
            out_tex.write('\\inst{0}'.format(auth['simple_affiliation_2']))
        out_tex.write('\n')

    out_tex.close()
