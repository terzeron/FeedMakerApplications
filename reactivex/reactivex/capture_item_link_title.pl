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

	# idempotent 
	while (my $line = <STDIN>) {
		while ($line =~ m!(?<link>\S+)\t(?<title>.+)!g) {
			$link = $+{"link"};
			$title = $+{"title"};
			print "$link\t$title\n";
		}
	}
}

main();
