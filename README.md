# gen_publication_geneset

## 1. Set Environment Variables <br>

sh evn.sh <br><br>

## 2. grep protein and info file name using species name from files.xml <br>
grep -e "Acoerulea.*annotation_info.txt" files.xml <br>
grep -e "Acoerulea.*protein.fa.gz" files.xml <br> <br>


## 3. download protein and info file from phytozome <br>
perl download.pl Acoerulea_322_v3.1.protein.fa.gz <br>
perl download.pl Acomosus_321_v3.annotation_info.txt <br><br>

## 4. create species name folder <br>
mkdir Acoerulea_322_v3.1 <br><br>

## 5. copy protein file, run_blast_slurm.sh, run_paperblast_pipeline.py and faSplit into species folder <br>
ls -l *annotation_info.txt | sed -e "s/.annotation_info.txt//g" | awk '{print "mkdir "$9"\n cp run_blast_slurm.sh "$9"\ncp run_paperblast_pipeline.py "$9"\ncp faSplit "$9}' | sh

cp Acoerulea_322_v3.1.protein.fa.gz Acoerulea_322_v3.1 <br>
cp run_blast_slurm.sh Acoerulea_322_v3.1 <br>
cp run_paperblast_pipeline.py Acoerulea_322_v3.1 <br>
cp faSplit Acoerulea_322_v3.1 <br><br>

## 6. split protein file <br>
python run_paperblast_pipeline.py Acoerulea_322_v3.1.protein.fa.gz <br><br>

## 7. run blast <br>
sbatch run_blast_slurm.sh <br><br>

## 8. Generate publication gmt file <br>
sh run_paperblast.sh Acomosus_321_v3.annotation_info.txt <br><br>
