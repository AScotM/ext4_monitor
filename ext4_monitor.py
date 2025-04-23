#!/usr/bin/env python3
import os
import subprocess
import json
from datetime import datetime
import psutil  # To list partitions and their file system types

class Ext4Monitor:
    @staticmethod
    def get_ext4_partitions():
        """
        Get all ext4 partitions on the system.
        """
        ext4_partitions = []
        for partition in psutil.disk_partitions():
            if partition.fstype == 'ext4':
                ext4_partitions.append(partition.device)
        return ext4_partitions

    @staticmethod
    def check_partition_status(partition):
        """
        Check the health and usage status of a specific partition.
        """
        # Run fsck (non-destructive check) and handle errors
        try:
            fsck_output = subprocess.check_output(
                ['sudo', 'fsck', '-n', partition],
                stderr=subprocess.STDOUT,
                text=True
            )
            status = "Healthy" if "clean" in fsck_output else "Needs Repair"
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running fsck on {partition}: {e.output}")

        # Get disk usage information and handle errors
        try:
            usage_output = subprocess.check_output(
                ['df', '-h', partition],
                stderr=subprocess.STDOUT,
                text=True
            )
            lines = usage_output.strip().split('\n')
            # Skip the header line and parse the actual usage data
            _, size, used, avail, use_percent, *_ = lines[1].split()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running df on {partition}: {e.output}")

        # Format the current timestamp
        last_checked = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "device": partition,
            "status": status,
            "check_output": fsck_output,
            "disk_usage": {
                "size": size,
                "used": used,
                "available": avail,
                "usage_percent": use_percent
            },
            "last_checked": last_checked
        }

    @staticmethod
    def gather_ext4_status():
        """
        Gather status information for all ext4 partitions.
        """
        partitions = Ext4Monitor.get_ext4_partitions()
        status_list = []
        for partition in partitions:
            status_list.append(Ext4Monitor.check_partition_status(partition))
        return status_list


if __name__ == "__main__":
    # Gather status data for all ext4 partitions
    ext4_status = Ext4Monitor.gather_ext4_status()

    # Format output for human readability and JSON structured response
    structured_output = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ext4_partitions": ext4_status
    }

    # Output formatted JSON
    print(json.dumps(structured_output, indent=4))
