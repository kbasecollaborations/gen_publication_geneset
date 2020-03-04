import sys
import csv
from collections import defaultdict
import json
import re



paperblast_json = sys.argv[1]
blasthits = sys.argv[2]

blast_hits_dict = defaultdict(list)
paper_dict = defaultdict(list)
seen = defaultdict(int)
gmt_dict = defaultdict(list)

title = defaultdict(str)


def removelcl(list): 
    pattern = 'lcl\|'
    list = [re.sub(pattern, '', i) for i in list] 
    return list


with open (paperblast_json) as json_file:
    paperblast = json.load(json_file)

for pub in paperblast['data']:
    if (pub['pubmed_url'] != 'http://www.ncbi.nlm.nih.gov/pubmed/'):
        subjectId = pub['subjectId']
        pubmed_url = pub['pubmed_url']
        paper_dict[subjectId].append(pubmed_url)
        title[pubmed_url] = pub['title']

with open (blasthits) as blast_results:
    reader = csv.reader(blast_results, delimiter='\t')
    for row in reader:
       gene_id = row[0]
       subjectId = row[1]
       evalue = float(row[10])
       if (evalue < 1E-10):
           blast_hits_dict[subjectId].append(gene_id)



for subjectId in paper_dict:
    for gene_id in blast_hits_dict[subjectId]:
        for pubmed_url in paper_dict[subjectId]:
            unique_key = gene_id + pubmed_url
            if seen[unique_key] != 1:
               gmt_dict[pubmed_url].append(gene_id)
               seen[unique_key] = 1

for pubmed_url, genes in gmt_dict.items():
     genes = removelcl(genes)
     genelist = " ".join(genes)
     title_text = title[pubmed_url]
     try:
             title_text = title_text.decode('utf-8')
             print (title_text + "\t" + pubmed_url + "\t" + genelist)
     except:
             pass
        
       
