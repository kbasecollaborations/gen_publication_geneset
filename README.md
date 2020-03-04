# gen_publication_geneset

## Set Environment Variables <br>

sh evn.sh <br><br>

## 1. grep protein file name from files.xml <br>
grep -e "Acoerulea.*protein.fa.gz" files.xml <br> <br>

## 2. download protein and info file from phytozome <br>
perl download.pl Acoerulea_322_v3.1.protein.fa.gz <br>
perl download.pl Acomosus_321_v3.annotation_info.txt <br><br>

## 3. create species name folder <br>
mkidr Acoerulea_322_v3.1 <br><br>

## 4. copy protein file, run_blast_slurm.sh, run_paperblast_pipeline.py and faSplit into species folder <br>
cp Acoerulea_322_v3.1.protein.fa.gz Acoerulea_322_v3.1 <br>
cp run_blast_slurm.sh Acoerulea_322_v3.1 <br>
cp run_paperblast_pipeline.py Acoerulea_322_v3.1 <br>
cp faSplit Acoerulea_322_v3.1 <br><br>

## 5. split protein file <br>
python run_paperblast_pipeline.py Acoerulea_322_v3.1.protein.fa.gz <br><br>

## 6. run blast <br>
sbatch run_blast_slurm.sh <br><br>

## 7. Generate publication gmt file <br>
sh run_paperblast.sh Acomosus_321_v3.annotation_info.txt <br><br>
