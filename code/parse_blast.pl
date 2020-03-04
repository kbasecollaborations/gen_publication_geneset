use strict;

my $hitsfile = $ARGV[0];
chomp ($hitsfile);
my $annot_file = $ARGV[1];
chomp ($annot_file);


my $evalue_cutoff = 1e-10;
my $alignment_cutoff = 40;


my %hash_annot = ();
my %seen = ();



open (ANNOT, $annot_file) or die ("cannot open file $annot_file\n");
while (<ANNOT>){
 
   my @l = split ("\t", $_);
   $hash_annot{$l[3]}=$l[1]; 

}

close (ANNOT);



open (FILE, $hitsfile) or die ("could not open file $hitsfile\n");
while (<FILE>){
    chomp($_);
    my @line = split ("\t", $_);
    #filter by e-value
    next if ($line[-2] > $evalue_cutoff);

    #filter by alignment_cutoff
    next if ($line[2] < $alignment_cutoff); 


    my $id = shift @line;
    my $sid = $hash_annot{$id};
    my $line = join ("\t", @line);


       #Fulter if already seen this gene- subject pair
    my $mid = $sid . "---" . $line[0];
    next if ($seen{$mid});


    $seen{$mid}++;

    print "$sid\t$line\n"; 

}
close (FILE);


