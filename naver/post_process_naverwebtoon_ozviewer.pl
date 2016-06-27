#!/usr/bin/env perl

use English;
use strict;
use warnings;
use Carp;
use Modern::Perl;
use Digest::MD5;


sub main
{
    my $page_url = $ARGV[0];
    my $url_prefix = "";
    my $data_url = "";

    while (my $line = <STDIN>) {
        if ($line =~ m!jpg: '([^']+\/){=filename}\?type=[^']+'!) {
            $url_prefix = $1;
        } elsif ($line =~ m!documentURL:\s*'([^']+)'!) {
            $data_url = $1;
            last;
        }
      }
    if (not defined $data_url or $data_url eq "" or not defined $url_prefix or $url_prefix eq "") {
        confess "can't get a data url from input\n";
    }
    
    my $cmd = qq(wget.sh "$data_url" utf8 | gunzip 2> /dev/null || wget.sh "$data_url" utf8);
    #print $cmd . "\n";
    if (not open(DATA, "$cmd | ")) {
        confess "Error: can't get data list from '$data_url'\n";
        return -1;
    }
    while (my $line = <DATA>) {
        chomp $line;
        while ($line =~ m!
                             "[^"]+"
                             :
                             "(assets/still/[^"]+\.(?:png|jpg))"
                             ,
                         !gx) {
            my $img_url = $url_prefix . $1;
            print "<img src='$img_url' width='100%'/>\n"
        }
    }
    close(DATA);
}    


main();
