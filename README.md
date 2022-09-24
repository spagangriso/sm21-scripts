# Utility scripts for snowmass 2021

Scripts for parsing contributed papers and extract useful metadata. Each script can be invoked with `-h` to see a quick description of its purpose and options.

Brief description:
* same HTML page form snowmass twiki page with list of contributed papers for each frontier, e.g. for EF [here](https://snowmass21.org/submissions/ef).
* Use `parse-twiki-html.py` to parse one or more frontier's HTML files to create an output CSV file with the list of contributed papers, categorized by frontier and topical group(s)
* Now parse the output above to retrieve metadata for the needed entries:
    * Use `get-lbl-metadata.py` to gather metadata information from inspirehep using their API on author list and their institution, filtering entries that include LBL authors. Save to CSV.
        * Optionally, upload the output as google drive spreadsheet and allow collaborative manual entry and edit of papers/names
    * Use `get-bsm-metadata.py` to gather metadata information from inspirehep using their API on author list and their institution, filtering entries that belong to EF08,EF09,EF10. Save to jSON.
* Finally, do some post-processing:
    * Use `postprocess-lbnl-papers.py` to derive statistics about LBNL contributed papers
    * Use `postprocess-ef-bsm.py` to create the needed author list for the EF BSM report and save as CSV file, then `generate-tex-ef-bsm.py` is used to generate the text code (note: some ugly custom caveats inside to handle additional authors given in different format and manually pre-handled)


