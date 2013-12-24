#!/usr/bin/env perl

use English;
use strict;
use warnings;
use Carp;
use Encode;

use HTML::Parser;
use FeedMaker qw(read_config get_config_value print_items print_all_hash_items);


# multiline matching
$/ = "";


sub extract_urls
{
	my $config_file = shift;
	my $encoding = shift;
	my $render_js = shift;
	my $url = shift;
	my $item_capture_script = shift;
	#print "# extract_urls($config_file, $encoding, $url, $item_capture_script)\n";

	my $option = "";
	if ($render_js == 1) {
		$option = "--render_js";
	}
	my $cmd = qq(wget.sh $option "$url" $encoding | extract_element.py $config_file collection 2>&1 | $item_capture_script $config_file);
	print "# $cmd\n";
	my $result = `$cmd`;
	if ($CHILD_ERROR != 0) {
		confess "Error: can't execute '$cmd', $ERRNO\n";
		return;
	}

	my @result_list = split /\n/, $result;
	# check the result
	foreach my $item (@result_list) {
		if ($item =~ /^\#/) {
			next;
		}
		my @tuple = split /\t/, $item;
		if (scalar @tuple < 2 or $tuple[0] eq "" or $tuple[1] eq "") {
			confess "Error: can't get the link and title from '$item',";
			return;
		}
	}
	return @result_list;
}


sub compose_url_list
{
	my $config_file = shift;
	my $encoding = shift;
	my $render_js = shift;
	my $list_url_list = shift ;
	my $item_capture_script = shift;
	my $total_list = shift;

	if (not defined $list_url_list) {
		$list_url_list = "";
	} 

	print "# compose_url_list($config_file, $encoding, $render_js, $list_url_list, $item_capture_script, $total_list)\n";

	foreach my $key (keys %$list_url_list) {
		my $value = $list_url_list->{$key};
		if (UNIVERSAL::isa($value, 'ARRAY')) {
			# list_url_list 아래 list_url이 여러 개 존재하는 경우
			foreach my $url (@$value) {
				my $a_url = $url;
				my @url_list = extract_urls($config_file, $encoding, $render_js, $a_url, $item_capture_script);
				push @$total_list, @url_list;
			}
		} else {
            # list_url_list 아래 list_url이 하나 존재하는 경우
			my $a_url = $value;
			my @url_list = extract_urls($config_file, $encoding, $render_js, $a_url, $item_capture_script);
			push @$total_list, @url_list;
		}
	}
}


sub print_usage
{
	print "usage:\t$PROGRAM_NAME\t<config file>\n";
	print "\n";
}


sub main
{
	#print "# main()\n";

	if (scalar @ARGV < 1) {
		print_usage();
		return -1;
	}
	my $config_file = $ARGV[0];
	my @total_list = ();

	# configuration
	my $config = ();
	if (not read_config($config_file, \$config)) {
		confess "Error: can't read configuration!,";
		return -1;
	}

	my $encoding = get_config_value($config, 0, ("collection", "encoding"));
	if (not defined $encoding or $encoding eq "") {
		$encoding = "utf8";
	} else {
		if ($encoding !~ m!(utf-?8|cp949)!i) {
			confess "Error: can't identify encoding type '$encoding'\n";
			return -1;
		}
	}
	my $render_js = get_config_value($config, 0, ("collection", "render_js"));
	if (defined $render_js and $render_js =~ m!(true|yes)!i) {
		$render_js = 1;
	} else {
		$render_js = 0;
	}

	my $list_url_list = get_config_value($config, 1, ("collection", "list_url_list"));
	if (defined $list_url_list) {
		print "# list_url_list:\n";
		print_all_hash_items($list_url_list, "  - ");
	}

	my $item_capture_script = get_config_value($config, 0, ("collection", "item_capture_script"));
	if (not defined $item_capture_script or $item_capture_script eq "") {
		$item_capture_script = "./capture_item_link_title.pl";
	}
	print "# item_capture_script: $item_capture_script\n";
	my ($item_capture_script_program,) = split /\s+/, $item_capture_script;
	if ($item_capture_script_program and not -x $item_capture_script_program) {
		confess "Error: can't execute '$item_capture_script_program',";
		return -1;
	}

	# collect items from specified url list
	print "# collecting items from specified url list...\n";
	compose_url_list($config_file, $encoding, $render_js, $list_url_list, $item_capture_script, \@total_list);

	foreach my $item (@total_list) {
		print $item . "\n";
	}

	return 0;
}


main();
