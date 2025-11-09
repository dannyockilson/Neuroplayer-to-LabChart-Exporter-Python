#!/usr/bin/env python3
"""
Bulk Converter for Neuroplayer EEG Data to LabChart Format

Processes subdirectories containing E{channel}.txt files and converts them to
unified LabChart-compatible format with all channels in a single file.

Usage:
    python bulk_converter.py input_folder [output_folder] [options]

Example:
    python bulk_converter.py ndf_files_text output --sample-rate 512 --range 120
"""

import argparse
import glob
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from labchart_exporter import LabChartExporter
from ndf_reader import TextSignalReader


def find_channel_directories(input_dir: str) -> List[str]:
    """
    Find all subdirectories that contain E{channel}.txt files.

    Args:
        input_dir: Parent directory to search

    Returns:
        List of subdirectory paths containing channel files
    """
    subdirs = []

    # Look for all subdirectories
    for entry in os.listdir(input_dir):
        full_path = os.path.join(input_dir, entry)
        if os.path.isdir(full_path):
            # Check if this directory contains any E{channel}.txt files
            channel_files = glob.glob(os.path.join(full_path, "E*.txt"))
            if channel_files:
                subdirs.append(full_path)

    return sorted(subdirs)


def find_channel_files(directory: str) -> Dict[int, str]:
    """
    Find all E{channel}.txt files in a directory.

    Args:
        directory: Directory to search

    Returns:
        Dictionary mapping channel numbers to file paths
    """
    channel_files = {}
    pattern = re.compile(r"E(\d+)\.txt$")

    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            channel_num = int(match.group(1))
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
                channel_files[channel_num] = file_path

    return channel_files


def load_channel_data(
    channel_files: Dict[int, str],
    sample_rate: float,
    interval_length: float = 1.0,
) -> Dict[int, List[Tuple[float, List[int]]]]:
    """
    Load data from all channel files.

    Args:
        channel_files: Dictionary mapping channel numbers to file paths
        sample_rate: Sample rate in Hz
        interval_length: Length of each interval in seconds

    Returns:
        Dictionary mapping channel numbers to their interval data
    """
    channel_data = {}

    for channel_num, file_path in channel_files.items():
        try:
            intervals = TextSignalReader.read_signal(
                filepath=file_path,
                sample_rate=sample_rate,
                interval_length=interval_length,
            )
            if intervals:
                channel_data[channel_num] = intervals
                print(f"  Channel {channel_num}: {len(intervals)} intervals loaded")
            else:
                print(f"  Channel {channel_num}: Warning - no data found")
        except Exception as e:
            print(f"  Channel {channel_num}: Error loading - {e}")

    return channel_data


def convert_directory(
    input_dir: str,
    output_dir: str,
    exporter: LabChartExporter,
    interval_length: float = 1.0,
) -> Optional[str]:
    """
    Convert all channel files in a directory to a single unified LabChart file.

    Args:
        input_dir: Directory containing E{channel}.txt files
        output_dir: Output directory for LabChart file
        exporter: LabChartExporter instance
        interval_length: Length of each interval in seconds

    Returns:
        Path to created LabChart file, or None if failed
    """
    dir_name = os.path.basename(input_dir)
    print(f"\nProcessing: {dir_name}")

    # Find all channel files
    channel_files = find_channel_files(input_dir)

    if not channel_files:
        print(f"  Warning: No E{{channel}}.txt files found in {input_dir}")
        return None

    print(f"  Found {len(channel_files)} channel files: {sorted(channel_files.keys())}")

    # Load all channel data
    channel_data = load_channel_data(
        channel_files=channel_files,
        sample_rate=exporter.sample_rate,
        interval_length=interval_length,
    )

    if not channel_data:
        print(f"  Warning: No valid data loaded from any channels")
        return None

    # Get creation date from directory metadata or first file
    first_file = list(channel_files.values())[0]
    file_mtime = os.path.getmtime(first_file)
    creation_date = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")

    # Create output filename based on directory name
    output_file = os.path.join(output_dir, f"{dir_name}.txt")

    # Export to unified LabChart format
    try:
        exporter.export_multi_channel(
            output_file=output_file,
            channel_data=channel_data,
            creation_date=creation_date,
        )
        print(f"  -> Created {os.path.basename(output_file)}")
        return output_file
    except Exception as e:
        print(f"  Error creating LabChart file: {e}")
        return None


def bulk_convert(
    input_dir: str,
    output_dir: Optional[str] = None,
    sample_rate: float = 512.0,
    range_mV: float = 120.0,
    interval_length: float = 1.0,
    use_commas: bool = False,
    time_in_ms: bool = False,
    value_in_uV: bool = False,
    absolute_time: bool = False,
    glitch_threshold: int = 500,
) -> List[str]:
    """
    Bulk convert all channel directories to unified LabChart format.

    Args:
        input_dir: Input directory containing subdirectories with E{channel}.txt files
        output_dir: Output directory (default: input_dir + '_labchart')
        sample_rate: Sample rate in Hz
        range_mV: Input dynamic range in millivolts
        interval_length: Length of each interval in seconds
        use_commas: Use European format (commas for decimals)
        time_in_ms: Express time in milliseconds
        value_in_uV: Express voltage in microvolts
        absolute_time: Use absolute UNIX time
        glitch_threshold: Glitch filter threshold (0 to disable)

    Returns:
        List of created LabChart file paths
    """
    # Validate input directory
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    # Set default output directory
    if output_dir is None:
        output_dir = input_dir + "_labchart"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all channel directories
    channel_dirs = find_channel_directories(input_dir)
    if not channel_dirs:
        print(f"No subdirectories with E{{channel}}.txt files found in {input_dir}")
        print(f"Expected structure: {input_dir}/[subdirectory]/E1.txt, E2.txt, etc.")
        return []

    print(f"Found {len(channel_dirs)} directories with channel files")
    print(f"Output directory: {output_dir}")

    # Create exporter
    exporter = LabChartExporter(
        sample_rate=sample_rate,
        range_mV=range_mV,
        use_commas=use_commas,
        time_in_ms=time_in_ms,
        value_in_uV=value_in_uV,
        absolute_time=absolute_time,
        glitch_threshold=glitch_threshold,
    )

    # Process each directory
    created_files = []
    for channel_dir in channel_dirs:
        output_file = convert_directory(
            input_dir=channel_dir,
            output_dir=output_dir,
            exporter=exporter,
            interval_length=interval_length,
        )

        if output_file:
            created_files.append(output_file)

    print(f"\nConversion complete!")
    print(f"Successfully converted {len(created_files)} out of {len(channel_dirs)} directories")
    print(f"Output files: {output_dir}")

    return created_files


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description="Bulk convert EEG channel directories to unified LabChart format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion with default settings
  python bulk_converter.py ndf_files_text

  # Custom output directory and sample rate
  python bulk_converter.py ndf_files_text output --sample-rate 1024 --range 30

  # European format with microvolts
  python bulk_converter.py data output --commas --microvolts

  # High precision timing in milliseconds
  python bulk_converter.py data output --milliseconds --absolute-time

Expected Input Structure:
  input_dir/
  ├── M1555404530/
  │   ├── E0.txt
  │   ├── E1.txt
  │   ├── E2.txt
  │   └── E15.txt
  └── M1555404531/
      ├── E0.txt
      ├── E1.txt
      └── E2.txt

Output:
  output_dir/
  ├── M1555404530.txt  (contains all channels in unified format)
  └── M1555404531.txt  (contains all channels in unified format)
        """,
    )

    parser.add_argument(
        "input_dir",
        help="Input directory containing subdirectories with E{channel}.txt files",
    )

    parser.add_argument(
        "output_dir",
        nargs="?",
        help="Output directory (default: input_dir + '_labchart')",
    )

    parser.add_argument(
        "--sample-rate",
        "-sr",
        type=float,
        default=512.0,
        help="Sample rate in Hz (default: 512)",
    )

    parser.add_argument(
        "--range",
        "-r",
        type=float,
        default=120.0,
        help="Input dynamic range in mV (default: 120)",
    )

    parser.add_argument(
        "--interval-length",
        "-il",
        type=float,
        default=1.0,
        help="Length of each interval in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--commas",
        action="store_true",
        help="Use European format (commas for decimals)",
    )

    parser.add_argument(
        "--milliseconds", action="store_true", help="Express time in milliseconds"
    )

    parser.add_argument(
        "--microvolts", action="store_true", help="Express voltage in microvolts"
    )

    parser.add_argument(
        "--absolute-time", action="store_true", help="Use absolute UNIX time"
    )

    parser.add_argument(
        "--glitch-threshold",
        "-gt",
        type=int,
        default=500,
        help="Glitch filter threshold (0 to disable, default: 500)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        created_files = bulk_convert(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            sample_rate=args.sample_rate,
            range_mV=args.range,
            interval_length=args.interval_length,
            use_commas=args.commas,
            time_in_ms=args.milliseconds,
            value_in_uV=args.microvolts,
            absolute_time=args.absolute_time,
            glitch_threshold=args.glitch_threshold,
        )

        if args.verbose:
            print("\nCreated files:")
            for file_path in created_files:
                print(f"  {file_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
