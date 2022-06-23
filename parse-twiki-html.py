from html.parser import HTMLParser
import argparse
from os.path import exists
import re

#Dictionat of section id names to be searched for in the HTML and their convenience label
listOfFrontiers={
    "papers_of_general_interest_to_this_frontier": "EF0",
    "ef01higgs_boson_properties_and_couplings": "EF01",
    "ef02higgs_boson_as_a_portal_to_new_physics": "EF02",
    "ef03heavy_flavor_and_top_quark_physics": "EF03",
    "ef04electroweak_precision_physics_and_constraining_new_physics": "EF04",
    "ef05precision_qcd": "EF05",
    "ef06hadronic_struture_and_forward_qcd": "EF06",
    "ef07heavy_ions": "EF07",
    "ef08beyond_the_standard_modelmodel-specific_explorations": "EF08",
    "ef09beyond_the_standard_modelmore_general_explorations": "EF09",
    "ef10beyond_the_standard_modeldark_matter_at_colliders": "EF10"
}

#output record
# - frontier (one of the convenience labels defined in listOfFrontiers)
# - arXiv (arXiv number)
# - title
# - also: list of other frontiers the paper appears in
currentRecord={
    'frontier':'', 
    'arxiv': '', 
    'title': '',
    'also': ''
}

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
            for relevantSection in listOfFrontiers.keys():
                if att[1] == relevantSection:
                    validFrontier=listOfFrontiers[relevantSection]
                    break

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
                outputPapers.append(currentRecord)
                if cmdArgs.debug > 3:
                    print('- New record found: ', currentRecord)
                #empty field, but keep frontier
                currentRecord['arxiv'] = ''
                currentRecord['title'] = ''
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

        # simply store potential title found in data, if we're parsing a valid frontier
        #check if data might contain a title in double quotes
        searchResult = re.search('\u0022(.+)\u0022', data, re.UNICODE)
        #searchResult = re.search(u'“(.+)“,', data, re.UNICODE)
        #searchResult = re.search('“(.+)“,', data)
        if searchResult:
            #found new potential title
            currentRecord['title'] = searchResult.group(1)
            if cmdArgs.debug > 5:
                print('Found title: ', currentRecord['title'])
            return
            
        #check if data might contain the arXiv number, if so assume title came before and finish the record
        searchResult = re.search('arXiv:(\S+)', data)
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
            linesHTML = fHTML.read()

        phParser = paperHTMLParser()
        phParser.feed(linesHTML)

    #print statistics
    