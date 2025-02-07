#!/usr/bin/perl
use strict;
use warnings;
use JSON;
use Sys::Filesystem;
use File::Basename;
use Time::Piece;  # For datetime formatting

# Define package Ext4Monitor
package Ext4Monitor;

# Get all ext4 partitions on the system
sub get_ext4_partitions {
    my $fs = Sys::Filesystem->new();
    my @ext4_partitions;

    for my $device ($fs->filesystems()) {
        my $format = $fs->format($device);
        if ($format && $format eq "ext4") {
            push @ext4_partitions, $device;
        }
    }

    return \@ext4_partitions;
}

# Check the status of a single partition
sub check_partition_status {
    my ($partition) = @_;

    # Run fsck (non-destructive check) and handle errors
    my $fsck_output = `sudo fsck -n $partition 2>&1`;
    if ($?) {
        die "Error running fsck on $partition: $fsck_output";
    }
    my $status = ($fsck_output =~ /clean/) ? "Healthy" : "Needs Repair";

    # Get disk usage information and handle errors
    my $usage_output = `df -h $partition`;
    if ($?) {
        die "Error running df on $partition: $usage_output";
    }
    my ($filesystem, $size, $used, $avail, $use_percent) = (split(/\s+/, $usage_output))[0,1,2,3,4];

    # Format the current timestamp
    my $last_checked = localtime->strftime("%Y-%m-%dT%H:%M:%SZ");

    return {
        device => $partition,
        status => $status,
        check_output => $fsck_output,
        disk_usage => {
            size => $size,
            used => $used,
            available => $avail,
            usage_percent => $use_percent
        },
        last_checked => $last_checked
    };
}

# Gather status information for all ext4 partitions
sub gather_ext4_status {
    my @partitions = @{ get_ext4_partitions() };
    my @status_list;

    foreach my $partition (@partitions) {
        push @status_list, check_partition_status($partition);
    }

    return \@status_list;
}

# Switch back to the main script
package main;

# Gather status data for all ext4 partitions
my $ext4_status = Ext4Monitor::gather_ext4_status();

# Format output for human readability and JSON structured response
my $structured_output = {
    timestamp => localtime->strftime("%Y-%m-%dT%H:%M:%SZ"),
    ext4_partitions => $ext4_status
};

# Output formatted JSON
print encode_json($structured_output), "\n";
