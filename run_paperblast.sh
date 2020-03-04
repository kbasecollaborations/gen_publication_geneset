
parseblastcgi=code/paperblast_final.cgi
parse_blast=code/parse_blast.pl
parse_blast_hits=code/parse_blasthits.py


#Will change for every species
ANNOTFILE=$1
species=`echo  $ANNOTFILE | sed -e "s/.annotation_info.txt//g"`
BLASTOUTDIR=/lustre/or-hydra/cades-bsd/4pz/blastruns/$species/output

echo $species
echo $BLASTOUTDIR

cat $BLASTOUTDIR/blast*.out > $species.blast.txt
perl $parse_blast  $species.blast.txt $ANNOTFILE  > $species.blast.txt.tmp

echo "running paperblast"


/lustre/or-hydra/cades-bsd/4pz/paperblastrun/paperblast_final.cgi  $species.blast.txt.tmp > $species.blast.txt.tmp.json

echo "paperblast finished"

python $parse_blast_hits  $species.blast.txt.tmp.json $species.blast.txt.tmp >$species.gmt




#cleanup

#rm -f $species.blast.txt*

#echo "output is in $species.gmt"
