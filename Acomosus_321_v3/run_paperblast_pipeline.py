import os
import sys
from os import path
import shlex, subprocess

input_fasta=sys.argv[1]


input_fasta_without_gz=None
if (input_fasta.endswith(".gz")):
    pass
else:
    exit("Not a valid gz file")


if (path.exists("input")):
    exit ("remove directory 'input' for a fresh run")

if (not path.exists("faSplit")):
    exit ("faSplit doesn't exist. Download in this folder from and change to executable mode http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/faSplit")



def prepare_command(input_fasta):
    input_fasta_without_gz = input_fasta[:-len(".gz")]
    command =  'mkdir input && ' \
              + 'cp ' + input_fasta + ' input && ' \
              + 'cp faSplit input && ' \
              + 'cd input &&' \
              + 'gzip -d ' + input_fasta + ' && ' \
              + './faSplit sequence ' + input_fasta_without_gz + ' 100 blast_query_ && ' \
              + 'rm ' + input_fasta_without_gz 
    return (command)
              


command = prepare_command (input_fasta);
print (command)
os.system(command)   



   

