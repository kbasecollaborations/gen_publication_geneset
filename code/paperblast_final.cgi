#!/usr/bin/perl -w
#######################################################
## litSearch.cgi
##
## Copyright (c) 2017 University of California
##
## Authors: Morgan Price
#######################################################
#
# Optional CGI garameters:
# query -- this should be the protein sequence in FASTA or UniProt or plain format,
#	or a VIMSS id, or a gene identifier in the database,
#	or a locus tag in MicrobesOnline,
#	or a UniProt id or other gene name that UniProt recognizes
#	or a Genbank protein (or RefSeq protein) identifier.
# more -- which geneId (in the database) to show the full list of papers for
#	(not to be used with query)
#
# If none of these is specified, shows the query box, an example link, and some documentation

use strict;
use CGI qw(:standard Vars);
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use Time::HiRes qw{gettimeofday};
use DBI;
use LWP::Simple qw{get};
use IO::Handle; # for autoflush
use Data::Dumper;
use JSON;

sub fail($);
sub simstring($$$$$$$$$$$$$);
sub SubjectToGene($);
sub commify($);
my @data = ();
my $base = "";
my $sqldb = "/lustre/or-hydra/cades-bsd/4pz/paperblastrun/litsearch.db";
my $hitsFile = $ARGV[0];

# for that gene on a separate page

my $more_subjectId = "";
my $maxPapers = 100;

my $dbh = DBI->connect("dbi:SQLite:dbname=$sqldb","","",{ RaiseError => 1 }) || die $DBI::errstr;



my $seq = "";
my $def=12;
my $query_id = "gene1234";


      my @hits = ();
      open(HITS, "<", $hitsFile) || die "Cannot read $hitsFile";
      while(<HITS>) {
        chomp;
        my @F = split /\t/, $_;
        push @hits, \@F;
      }
      close(HITS) || die "Error reading $hitsFile";



    my $nHits = scalar(@hits);
    if ($nHits == 0) {
#        print p("Sorry, no hits to proteins in the literature.");
    } else {
#        print p("Found $nHits similar proteins in the literature:"), "\n"
#          unless $more_subjectId;

        my %seen_subject = ();
        my $li_with_style = qq{<LI style="list-style-type: none;" margin-left: 6em; >};
        my $ul_with_style = qq{<UL style="margin-top: 0em; margin-bottom: 0em;">};
        foreach my $row (@hits) {
            my ($queryId,$subjectId,$percIdentity,$alnLength,$mmCnt,$gapCnt,$queryStart,$queryEnd,$subjectStart,$subjectEnd,$eVal,$bitscore) = @$row;

            next if exists $seen_subject{$subjectId};
            $seen_subject{$subjectId} = 1;

            my $dups = $dbh->selectcol_arrayref("SELECT duplicate_id FROM SeqToDuplicate WHERE sequence_id = ?",
                                                {}, $subjectId);
            my @subject_ids = ($subjectId);
            push @subject_ids, @$dups;

            my @genes = map { &SubjectToGene($_) } @subject_ids;
            @genes = sort { $a->{priority} <=> $b->{priority} } @genes;

            my @headers = ();
            my @content = ();
            my %paperSeen = (); # to avoid redundant papers -- pmId.pmcId.doi => term => 1
            my %paperSeenNoSnippet = (); # to avoid redundant papers -- pmId.pmcId.doi => 1

            # Produce top-level and lower-level output for each gene (@headers, @content)
            # Suppress duplicate papers if no additional terms show up
            # (But, a paper could show up twice with two different terms, instead of the snippets
            # being merged...)
            foreach my $gene (@genes) {
                die "No subjectId" unless $gene->{subjectId};
                $gene->{desc} = "No description" unless $gene->{desc}; # could be missing in MicrobesOnline or EcoCyc
                foreach my $field (qw{showName URL priority subjectId desc organism protein_length source}) {
                    warn "No $field for $subjectId" unless $gene->{$field};
                }
                my @pieces = ( a({ -href => $gene->{URL}, -title => $gene->{source} }, $gene->{showName}),
                               $gene->{priority} <= 2 ? b($gene->{desc}) : $gene->{desc},
                               "from",
                               i($gene->{organism}) );



                # The alignment to show is always the one reported, not necessarily the one for this gene
                # (They are all identical, but only $subjectId is guaranteed to be in the blast database
                # and to be a valid argument for showAlign.cgi)
                push @pieces, &simstring(length($seq), $gene->{protein_length},
                                         $queryStart,$queryEnd,$subjectStart,$subjectEnd,
                                         $percIdentity,$eVal,$bitscore,
                                         $def, $gene->{showName}, $seq, $subjectId)
                    if $gene->{subjectId} eq $genes[0]{subjectId} && ! $more_subjectId;
                if (exists $gene->{pmIds} && @{ $gene->{pmIds} } > 0) {
                    my @pmIds = @{ $gene->{pmIds} };
                    my %seen = ();
                    @pmIds = grep { my $keep = !exists $seen{$_}; $seen{$_} = 1; $keep; } @pmIds;
                    my $note = @pmIds > 1 ? scalar(@pmIds) . " papers" : "paper";
                    push @pieces, "(see " .
                        a({-href => "http://www.ncbi.nlm.nih.gov/pubmed/" . join(",",@pmIds) }, $note)
                        . ")";
                }
                push @headers, join(" ", @pieces);
                push @content, $gene->{comment} if $gene->{comment};
                my $nPaperShow = 0;
                foreach my $paper (@{ $gene->{papers} }) {
                    my @pieces = (); # what to say about this paper
                    my $snippets = [];
                    $snippets = $dbh->selectall_arrayref(
                        "SELECT DISTINCT * from Snippet WHERE geneId = ? AND pmcId = ? AND pmId = ?",
                        { Slice => {} },
                        $gene->{subjectId}, $paper->{pmcId}, $paper->{pmId})
                        if $paper->{pmcId} || $paper->{pmId};

                    my $paperId = join(":::", $paper->{pmId}, $paper->{pmcId}, $paper->{doi});
                    my $nSkip = 0; # number of duplicate snippets
                    foreach my $snippet (@$snippets) {
                        my $text = $snippet->{snippet};
                        my $term = $snippet->{queryTerm};
                        if (exists $paperSeen{$paperId}{$term}) {
                            $nSkip++;
                        } else {
				#$text =~ s!($term)!<B><span style="color: red;">$1</span></B>!gi;
				  #  $text =~ s!($term)!$1!gi;
                                  push @pieces, "$text;";
                        }
                    }
                    # ignore this paper if all snippets were duplicate terms
                    next if $nSkip == scalar(@$snippets) && $nSkip > 0;
                    $nPaperShow++;
                    if ($nPaperShow > $maxPapers) {
                      last;
                      next;
                    }
                    foreach my $snippet (@$snippets) {
                        my $term = $snippet->{queryTerm};
                        $paperSeen{$paperId}{$term} = 1;
                    }

                    # Add RIFs
                    my $rifs = [];
                    $rifs = $dbh->selectall_arrayref(qq{ SELECT DISTINCT * from GeneRIF
                                                        WHERE geneId = ? AND pmcId = ? AND pmId = ? },
                                                    { Slice => {} },
                                                    $gene->{subjectId}, $paper->{pmcId}, $paper->{pmId})
                      if $paper->{pmcId} || $paper->{pmId};
                    my $GeneRIF_def = a({ -title => "from Gene Reference into Function (NCBI)",
                                          -href => "https://www.ncbi.nlm.nih.gov/gene/about-generif"},
                                        "GeneRIF");

				#-style => "color: black; text-decoration: none; font-style: italic;" },
                    # just 1 snippet if has a GeneRIF
                    pop @pieces if @$rifs > 0 && @pieces > 1;
                    foreach my $rif (@$rifs) {
                      # normally there is just one
                      unshift @pieces, $GeneRIF_def . ": " . $rif->{ comment };
                    }

                    my $paper_url = undef;
                    my $pubmed_url = "http://www.ncbi.nlm.nih.gov/pubmed/" . $paper->{pmId};
                    if ($paper->{pmcId} && $paper->{pmcId} =~ m/^PMC\d+$/) {
                        $paper_url = "http://www.ncbi.nlm.nih.gov/pmc/articles/" . $paper->{pmcId};
                    } elsif ($paper->{pmid}) {
                        $paper_url = $pubmed_url;
                    } elsif ($paper->{doi}) {
                      if ($paper->{doi} =~ m/^http/) {
                        $paper_url = $paper->{doi};
                      } else {
                        $paper_url = "http://doi.org/" . $paper->{doi};
                      }
                    }
                    my $title = $paper->{title};
		    #$title = a({-href => $paper_url}, $title) if defined $paper_url;
                    my $authorShort = $paper->{authors};
                    $authorShort =~ s/ .*//;
                    my $extra = "";
		    #$extra = "(" . a({-href => $pubmed_url}, "PubMed") . ")"
		    #    if !$paper->{pmcId} && $paper->{pmId};
                    my $paper_header = $title . br() .
                        small( a({-title => $paper->{authors}}, "$authorShort,"),
                               $paper->{journal}, $paper->{year}, $extra);
                   

		       #print "\n" . "uuuuuuuuuu$paper_header sssssss" . "\n"; 
                    if (@pieces == 0) {
                        # Skip if printed already for this gene (with no snippet)
                        next if exists $paperSeenNoSnippet{$paperId};
                        $paperSeenNoSnippet{$paperId} = 1;

                        # Explain why there is no snippet
                        my $excuse;
                        my $short;
                        if (!defined $paper->{access}) {
                          ;
                        } elsif ($paper->{access} eq "full") {
                          $short = "no snippet";
                          $excuse = "This term was not found in the full text, sorry.";
                        } elsif ($paper->{isOpen} == 1) {
                          if ($paper->{access} eq "abstract") {
                            $short = "no snippet";
                            $excuse = "This paper is open access but PaperBLAST only searched the the abstract.";
                          } else {
                            $short = "no snippet";
                            $excuse = "This paper is open access but PaperBLAST did not search either the full text or the abstract.";
                          }
                        } elsif ($paper->{isOpen} eq "") {
                          # this happens if the link is from GeneRIF
                          $short = "no snippet";
                          $excuse = "PaperBLAST did not search either the full text or the abstract.";
                        } elsif ($paper->{journal} eq "") {
                          $short = "secret";
                          $excuse = "PaperBLAST does not have access to this paper, sorry";
                        } else {
                            $short = "secret";
                            $excuse = "$paper->{journal} is not open access, sorry";
                        }
                        if ($excuse) {

                            my $href = a({-title => $excuse}, $short);
                            $paper_header .= " " . small("(" . $href . ")"); 
                        }
                    }


		    #         my $pieces = join($li_with_style, @pieces);
		    # $pieces = join("", $ul_with_style, $li_with_style, $pieces, "</UL>")
		    #    if $pieces;
		    #  push @content, $paper_header . $pieces;
		    #
		    #
		    #
                     
		    #$paper_header = "$paper_url\n$pubmed_url\n$title\n$paper->{authors}\n$authorShort\n$paper->{journal}\n$paper->{year}\n";
		    #my $pieces = join("\n###\n", @pieces);
		    #             push @content, $paper_header . $pieces;
		    #print "$paper_header\n$pieces\n";


                    my $contentx = ();
		    $contentx->{paper_url} = $paper_url;
		    $contentx->{subjectId} = $subjectId;
		    $contentx->{pubmed_url} = $pubmed_url;
		    $contentx->{title} = $title;
		    $contentx->{authors} = $paper->{authors};
		    $contentx->{authorshort} = $authorShort;
		    $contentx->{journal} = $paper->{journal};
		    $contentx->{paper_year} = $paper->{year};
		    $contentx->{organism} = $gene->{organism};
		    $contentx->{internalid} = $gene->{geneId};
		    $contentx->{geneDescription} = $gene->{desc};
		    $contentx->{id} = $gene->{showName};
		    $contentx->{pieces} = \@pieces;
                    
		    #$gene_details->{gene}=$gene->{showName};
		    #$gene_details->{geneId}= $gene->{geneId};
		    #$gene_details->{geneDesc} = $gene->{desc};
                    push @data, $contentx;		    


                }
            }


	    #my $content = join($li_with_style, @content);
	    #$content = join("", $ul_with_style, $li_with_style, $content, "</UL>")
	    #    if $content;
	    # print p({-style => "margin-top: 1em; margin-bottom: 0em;"},
	    #        join("<BR>", @headers) . $content) . "\n";
        }
    }

    my $final_result = ();
    $final_result->{query}="query";
    $final_result->{data}=\@data;
    print to_json($final_result);


    #my @pieces = $seq =~ /.{1,60}/g;
    #if (! $more_subjectId) {
    #  print h3("Query Sequence"),
    #    p({-style => "font-family: monospace;"}, small(join(br(), ">$def", @pieces))),
    #  }



sub fail($) {
    my ($notice) = @_;
    print ("<ERROR>$notice</ERROR>\n");
    exit(0);
}

sub simstring($$$$$$$$$$$$$) {
    my ($qLen, $sLen, $queryStart,$queryEnd,$subjectStart,$subjectEnd,$percIdentity,$eVal,$bitscore,
        $def1, $def2, $seq1, $acc2) = @_;
    $percIdentity = sprintf("%.0f", $percIdentity);
    # the minimum of coverage either way
    my $cov = ($queryEnd-$queryStart+1) / ($qLen > $sLen ? $qLen : $sLen);
    my $percentCov = sprintf("%.0f", 100 * $cov);
    my $title ="$queryStart:$queryEnd/$qLen of query is similar to $subjectStart:$subjectEnd/$sLen of hit (E = $eVal, $bitscore bits)";
    return "(" .
        span({ -title => $title },
	     "$percIdentity% identity, $percentCov% coverage")
        . ")";
}



sub AddCuratedInfo($) {
  my ($gene) = @_;
  my $db = $gene->{db};
  my $protId = $gene->{protId};
  die unless $db && $protId;
  $gene->{subjectId} = join("::", $db, $protId);
  $gene->{source} = $db;
  $gene->{curated} = 1;
  $gene->{curatedId} = $protId;

  if ($db eq "CAZy") {
    $gene->{source} = "CAZy via dbCAN";
    $gene->{URL} = "http://www.cazy.org/search?page=recherche&lang=en&recherche=$protId&tag=4";
    $gene->{priority} = 4;
  } elsif ($db eq "CharProtDB") {
    $gene->{priority} = 4;
    # their site is not useful, so just link to the paper
    $gene->{URL} = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3245046/";
    if ($gene->{comment}) {
      # label the comment as being from CharProtDB, as otherwise it is a bit mysterious.
      # And remove the Alias or Aliaess part.
      $gene->{comment} =~ s/Aliase?s?: [^ ;]+;? ?//;
      $gene->{comment} = i("CharProtDB") . " " . $gene->{comment};
    }
  } elsif ($db eq "SwissProt") {
    $gene->{URL} = "http://www.uniprot.org/uniprot/$protId";
    $gene->{priority} = 2;
    # and clean up the comments
    my @comments = split /_:::_/, $gene->{comment};
    @comments = map { s/[;. ]+$//; $_; } @comments;
    @comments = grep m/^SUBUNIT|FUNCTION|COFACTOR|CATALYTIC|ENZYME|DISRUPTION/, @comments;
    @comments = map {
      my @words = split / /, $_;
      my $word1 = $words[0];
      $words[0] = b(lc($words[0]));
      $words[1] = b(lc($words[1])) if @words > 1 && $words[1] =~ m/^[A-Z]+:$/;
      my $out = join(" ", @words);
      if ($word1 eq "COFACTOR:") {
        # Remove Evidence= and Xref= fields, as often found in the cofactor entry
        $out =~ s/ Evidence=[^;]*;?//g;
        $out =~ s/ Xref=[^;]*;?//g;
        # Transform Name=x; to x;
        $out =~ s/ Name=([^;]+);?/ $1/g;
        # Transform Note=note. to <small>(note.)</small>
        # require last char to be non-space to avoid " )" in output
        $out =~ s!Note=(.*)[.]!<small>($1.)</small>!g;
      } elsif ($word1 eq "CATALYTIC") {
        # Convert Xref=Rhea:RHEA:nnnn to a link to the Rhea entry, if it exists
        # Remove everthing else after the Reaction (i.e. EC: or ChEBI: entries)
        my $rheaId = $1 if $out =~ m/Xref=Rhea:RHEA:(\d+)/;
        $out =~ s/Reaction=([^;]+);.*$/$1/;
        $out .= " " . small("("
                      . a({ -href => "https://www.rhea-db.org/reaction?id=$rheaId" }, "RHEA:$rheaId")
                      . ")") if defined $rheaId;
      }
      $out;
    } @comments;
    my $comment = join("<BR>\n", @comments);
    $comment =~ s!{ECO:[A-Za-z0-9_:,.| -]+}!!g;
    $gene->{comment} = $comment;
  } elsif ($db eq "ecocyc") {
    $gene->{source} = "EcoCyc";
    $gene->{URL} = "https://ecocyc.org/gene?orgid=ECOLI&id=$protId";
    $gene->{priority} = 1;
  } elsif ($db eq "metacyc") {
    $gene->{source} = "MetaCyc";
    $gene->{URL} = "https://metacyc.org/gene?orgid=META&id=$protId";
    $gene->{priority} = 3;
  } elsif ($db eq "reanno") {
    $gene->{source} = "Fitness-based Reannotations";
    $gene->{comment} = "Mutant Phenotype: " . $gene->{comment};
    $gene->{priority} = 5;
    my ($orgId, $locusId) = split /:/, $protId;
    die "Invalid protId $protId" unless $locusId;
    $gene->{URL} = "http://fit.genomics.lbl.gov/cgi-bin/singleFit.cgi?orgId=$orgId&locusId=$locusId";
  } elsif ($db eq "REBASE") {
    $gene->{priority} = 4;
    $gene->{URL} = "http://rebase.neb.com/rebase/enz/$protId.html";
  } elsif ($db eq "BRENDA") {
    $gene->{priority} = 2.5; # just behind Swiss-Prot
    $gene->{source} = "BRENDA";
    $gene->{URL} = "http://www.brenda-enzymes.org/sequences.php?AC=" . $protId;
  } else {
    die "Unexpected curated database $db";
  }
  my @ids = ( $gene->{name}, $gene->{id2} );
  push @ids, $protId if $db eq "SwissProt";
  @ids = grep { $_ ne "" } @ids;
  $gene->{showName} = join(" / ", @ids) || $protId;
  $gene->{showName} = $protId if $db eq "REBASE";
}


sub SubjectToGene($) {
  my ($subjectId) = @_;
  if ($subjectId =~ m/::/) { # curated gene
    my ($db, $protId) = split /::/, $subjectId;
    my $gene = $dbh->selectrow_hashref("SELECT * FROM CuratedGene WHERE db = ? AND protId = ?", {}, $db, $protId);
    die "Unrecognized subject $subjectId" unless defined $gene;
    AddCuratedInfo($gene);
    $gene->{pmIds} = $dbh->selectcol_arrayref("SELECT pmId FROM CuratedPaper WHERE db = ? AND protId = ?",
                                              {}, $db, $protId);
    return $gene;
  } else { # look in Gene table
    my $gene = $dbh->selectrow_hashref("SELECT * FROM Gene WHERE geneId = ?", {}, $subjectId);
    die "Unrecognized gene $subjectId" unless defined $gene;
    $gene->{subjectId} = $subjectId;
    $gene->{priority} = 6; # literature mined is lowest
    if ($subjectId =~ m/^VIMSS(\d+)$/) {
      my $locusId = $1;
      $gene->{source} = "MicrobesOnline";
      $gene->{URL} = "http://www.microbesonline.org/cgi-bin/fetchLocus.cgi?locus=$locusId";
    } elsif ($subjectId =~ m/^[A-Z]+_[0-9]+[.]\d+$/) { # refseq
      $gene->{URL} = "http://www.ncbi.nlm.nih.gov/protein/$subjectId";
      $gene->{source} = "RefSeq";
    } elsif ($subjectId =~ m/^[A-Z][A-Z0-9]+$/) { # SwissProt/TREMBL
      $gene->{URL} = "http://www.uniprot.org/uniprot/$subjectId";
      $gene->{source} = "SwissProt/TReMBL";
    } else {
      die "Cannot build a URL for subject $subjectId";
    }

    my $papers = $dbh->selectall_arrayref(qq{ SELECT DISTINCT * FROM GenePaper
                                              LEFT JOIN PaperAccess USING (pmcId,pmId)
                                              WHERE geneId = ?
                                              ORDER BY year DESC },
                                          { Slice => {} }, $subjectId);
    $gene->{papers} = $papers;

    # set up showName
    my @terms = map { $_->{queryTerm} } @$papers;
    my %terms = map { $_ => 1 } @terms;
    @terms = sort keys %terms;
    $gene->{showName} = join(", ", @terms) if !defined $gene->{showName};

    return $gene;
  }
}




