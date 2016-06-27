#!/usr/bin/env perl

use English;
use strict;
use warnings;
use Carp;
use Encode;


sub main
{
    my $link = "";
    my $title = "";
    my $state = 0;
    my $id = "";

    while (my $line = <STDIN>) {
        if ($state == 0) {
            if ($line =~ m!<li class="list viewerLinkBtn (?:pointer )?list_[HV][^>]*data-productid="(\d+)"!) {
                $id = $1;
                $link = "http://page.kakao.com/viewer?productId=" . $id;
                $state = 1;
            }
        } elsif ($state == 1) {
			if ($line =~ m!<span class="Lfloat (?:listTitle )?ellipsis">!) {
				$state = 2;
			}
		} elsif ($state == 2) {
            if ($line =~ m!^\s*(\S+.*\S+)\s*$!) {
                $title = $1;
				$title =~ s/&lt;/ /g;
				$title =~ s/&gt;/ /g;
                print "$link\t$title\n";
                $state = 0;
            }
        }
    }
}


main();
