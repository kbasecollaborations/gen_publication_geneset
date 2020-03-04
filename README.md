# gen_publication_geneset


##1. grep protein file name from files.xml
grep -e "Acoerulea.*protein.fa.gz" files.xml

##2. download protein and info file from phytozome
perl download.pl Acoerulea_322_v3.1.protein.fa.gz
perl download.pl Acomosus_321_v3.annotation_info.txt

##3. create species name folder 
mkidr Acoerulea_322_v3.1

##4. copy protein file, run_blast_slurm.sh, run_paperblast_pipeline.py and faSplit into species folder
cp Acoerulea_322_v3.1.protein.fa.gz Acoerulea_322_v3.1
cp run_blast_slurm.sh Acoerulea_322_v3.1
cp run_paperblast_pipeline.py Acoerulea_322_v3.1
cp faSplit Acoerulea_322_v3.1

##5. split protein file 
python run_paperblast_pipeline.py Acoerulea_322_v3.1.protein.fa.gz

##6. run blast 
sbash run_blast_slurm.sh 

##7. Generate publication gmt file
run_paperblast.sh Acomosus_321_v3.annotation_info.txt
