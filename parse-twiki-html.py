from html.parser import HTMLParser
import argparse
from os.path import exists
import re
import csv

#output record
currentRecord={
    'arxiv': '', 
    'frontier':'', 
    'also': ''
}

#need to keep track of frontier from file name unfortunately
currentFrontierFile=''

#output list of dictionary of the format of currentRecord above
outputPapers=[]


# Check if HTML tag contains the start of a relevant frontier and return its code, if deemed relevant
def getFrontierLabelFromTag(tag, attrs):
    validFrontier=''
    #only 'h4' tag contain new frontiers/groups
    if not (tag == 'h4'):
        return validFrontier

    #now check attributes
    for att in attrs:
        if (att[0] == 'id'):
            #check if we're starting a new relevant frontier
            if att[1] == 'papers_of_general_interest_to_this_frontier':
                #frontier depends on file name
                validFrontier = currentFrontierFile+'00'
            else:
                if cmdArgs.debug > 15:
                    print('Searching "({}\d\d).+" in string: {}'.format(currentFrontierFile.lower(), att[1]))

                searchResult = re.search('({}\d\d).+'.format(currentFrontierFile.lower()), att[1])
                if searchResult:
                    validFrontier = searchResult.group(1).upper()
#            for relevantSection in listOfFrontiers.keys():
#                if att[1] == relevantSection:
#                    validFrontier=listOfFrontiers[relevantSection]
#                    break

    #return result
    return validFrontier


class paperHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if cmdArgs.debug > 10:
            print("Encountered a start tag: {}, attr={}".format(tag, attrs))
        #first check if we have a new frontier
        tagFrontier = getFrontierLabelFromTag(tag, attrs)
        if tagFrontier:
            currentRecord['frontier'] = tagFrontier
            if cmdArgs.debug > 1:
                print('Now parsing frontier: {}'.format(currentRecord['frontier']))

            

    def handle_endtag(self, tag):
        if cmdArgs.debug > 10:
            print("Encountered an end tag :", tag)

        #append output record when finding a closing "li" tag and we have a valid arXiv number
        if tag == 'li':
            if currentRecord['arxiv']:
                outputPapers.append(currentRecord.copy())
                if cmdArgs.debug > 3:
                    print('- New record found: ', currentRecord)
                #empty field, but keep frontier
                currentRecord['arxiv'] = ''
                currentRecord['also'] = ''

        #check if we need to close active frontier (close of div tag opened with class 'level4', first after h4 tag)
        # Disabled for now, does not work like this (we have a div tag closing after each line)
#        if tag == 'div' and currentRecord['frontier']:
#            if cmdArgs.debug > 2:
#                print('Finished parsing frontier: {}'.format(currentRecord['frontier']))
#            currentRecord['frontier']=''

    def handle_data(self, data):
        if cmdArgs.debug > 10:
            print("Encountered some data  :", data)

        #only analyze data if in an active frontier
        if not currentRecord['frontier']:
            return
         
        #check if data might contain the arXiv number, if so assume title came before and finish the record
        #searchResult = re.search('arXiv:(\S+)', data)
        searchResult = re.search('arXiv:(\d+\.\d+)', data)
        if searchResult:
            #found new arXiv reference, store record
            currentRecord['arxiv'] = searchResult.group(1)
            if cmdArgs.debug > 5:
                print('Found arXiv: ', currentRecord['arxiv'])
            return

        #check if data might contain the 'also under..' information
        searchResult = re.search('\(also under (.*)\)', data)
        if searchResult:
            #found new "also under" information
            currentRecord['also'] = searchResult.group(1).split(',')
            #trim strings
            currentRecord['also'] = [ s.strip() for s in currentRecord['also']]
            if cmdArgs.debug > 5:
                print('Found also: ', currentRecord['also'])
            return
        
            

if __name__ == '__main__':

    cmdParser = argparse.ArgumentParser(description='Parse twiki HTML source for contributed papers')
    cmdParser.add_argument('input_files', metavar='inputFile', type=str, nargs='+', help='Input HTML source file(s)')
    cmdParser.add_argument('--output_file', dest='output_file', type=str, default='sm21-papers.csv', help='Output CSV file')
    cmdParser.add_argument('--debug', dest='debug', type=int, default=0, help='Enable debug printout')
    cmdArgs = cmdParser.parse_args()

    #parse input file(s)
    for input_file in cmdArgs.input_files:
        if cmdArgs.debug:
            print('Processing {}'.format(input_file))

        if not exists(input_file):
            print('WARNING: input file ({}) does not exist. Skipping.'.format(input_file))
            #skip to next file
            continue 

        # open and parse input HTML file
        with open(input_file, encoding="utf-8") as fHTML:
            currentFrontierFile = input_file.split('_')[6].split('.')[0].upper()
            linesHTML = fHTML.read()

        phParser = paperHTMLParser()
        phParser.feed(linesHTML)

    #print statistics
    stat={}
    groups = sorted(list(set([rec['frontier'] for rec in outputPapers])))
    print('Number of papers per frontier:')
    for g in groups:
        #count occurrences in outputPapers
        occ = len([rec for rec in outputPapers if rec['frontier'] == g])
        print('{}: {}'.format(g, occ))
        stat[g] = occ
    print('Total:', sum([stat[g] for g in groups]))
    with open('stat.csv', 'w') as output_stat:
        csvWriter = csv.writer(output_stat)
        for g in groups:
            csvWriter.writerow([g, stat[g]])

    #save to file
    with open(cmdArgs.output_file, 'w') as output_file:
        csvWriter = csv.DictWriter(output_file, fieldnames=outputPapers[0].keys())
        csvWriter.writeheader()
        for data in outputPapers:
            csvWriter.writerow(data)
    print('Output saved to CSV file: ', cmdArgs.output_file)
