#!/usr/bin/env perl

use English;
use strict;
use warnings;
use Carp;
use Encode;
use FeedMaker;


sub main
{
	my $link = "";
	my $title = "";

	while (my $line = <STDIN>) {
		while ($line =~ m!
							 [^}]*,
							 "prodId":"\s*([^"]+)\s*",
							 [^}]*,
							 "prodNm":"\s*([^"]+)\s*",
						 !igx) {
			$title = $2;
			$link = "http://m.tstore.co.kr/mobilepoc/webtoon/webtoonDetail.omp?prodId=" . $1;
			print "$link\t$title\n";
		}
	}
}


main();
