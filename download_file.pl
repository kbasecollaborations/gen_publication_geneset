use strict;

#my $id = "Ptrichocarpa_444_v3.1.protein.fa.gz";
my $id = $ARGV[0];
chomp ($id);

my $url = "https://genome.jgi.doe.gov/portal/ext-api/downloads/get_tape_file?blocking=true&url=";
my $txt = `grep $id files.xml`;
$txt=~s/.*url=//;
$txt=~s/.gz.*/.gz/;
$txt=~s/.txt.*/.txt/;
$txt=~s/\s*$//;

my $filename = $txt;
$filename=~s/.*\///;
$filename=~s/ //;
my $cmd = "curl '" . $url . $txt . "' -b cookies > " . $filename ;

print $cmd;

system ($cmd)


