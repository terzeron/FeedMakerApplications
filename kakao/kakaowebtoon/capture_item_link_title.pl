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
    my $num = "";
    my $state = 0;

    while (my $line = <STDIN>) {
        if ($state == 0) {
            if ($line =~ m!<li class="list ajaxCallList\s*" data-seriesid="(\d+)">!) {
                $link = "http://page.kakao.com/home/" . $1;
                $state = 1;
            }
        } elsif ($state == 1) {
            if ($line =~ m!<dt class="title ellipsis">!) {
                $state = 2;
            }
        } elsif ($state == 2) {
            if ($line =~ m!<img!){
                next;
            }
            if ($line =~ m!^\s*(\S.*\S)\s*$!) {
                $title = $1;
                print "$link\t$title\n";
                $state = 0;
            }
        }
    }
}


main();
