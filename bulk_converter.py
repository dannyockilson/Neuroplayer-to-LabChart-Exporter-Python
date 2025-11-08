#!/usr/bin/env python3
"""
Bulk Converter for Neuroplayer EEG Data to LabChart Format

Processes all text files in a directory and converts them to LabChart-compatible format
using the TextSignalReader and LabChartExporter classes.

Usage:
    python bulk_converter.py input_folder [output_folder] [options]

Example:
    python bulk_converter.py mock-inputs output --sample-rate 512 --range 120
"""

import argparse
import glob
import os
import sys
from datetime import datetime
from typing import List, Optional

from labchart_exporter import LabChartExporter
from ndf_reader import TextSignalReader


def find_text_files(input_dir: str) -> List[str]:
    """
    Find all text files in the input directory.

    Args:
        input_dir: Directory to search for text files

    Returns:
        List of text file paths
    """
    # Look for .txt files
    txt_pattern = os.path.join(input_dir, "*.txt")
    txt_files = glob.glob(txt_pattern)

    # Filter out any files that start with # (comments) or are empty
    valid_files = []
    for file_path in txt_files:
        if os.path.getsize(file_path) > 0:
            valid_files.append(file_path)

    return sorted(valid_files)


def convert_file(
    input_file: str,
    exporter: LabChartExporter,
    output_dir: str,
    channel_num: int,
    interval_length: float = 1.0,
) -> Optional[str]:
    """
    Convert a single text file to LabChart format.

    Args:
        input_file: Path to input text file
        exporter: LabChartExporter instance
        output_dir: Output directory
        channel_num: Channel number for this file
        interval_length: Length of each interval in seconds

    Returns:
        Path to created LabChart file, or None if failed
    """
    try:
        print(f"Processing: {os.path.basename(input_file)}")

        # Read signal data using TextSignalReader
        intervals = TextSignalReader.read_signal(
            filepath=input_file,
            sample_rate=exporter.sample_rate,
            interval_length=interval_length,
        )

        if not intervals:
            print(f"  Warning: No data found in {input_file}")
            return None

        # Get creation date (use file modification time)
        file_mtime = os.path.getmtime(input_file)
        creation_date = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")

        # Export to LabChart format
        output_file = exporter.export_channel(
            output_dir=output_dir,
            channel_num=channel_num,
            intervals=intervals,
            creation_date=creation_date,
        )

        print(f"  -> {os.path.basename(output_file)} ({len(intervals)} intervals)")
        return output_file

    except Exception as e:
        print(f"  Error processing {input_file}: {e}")
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
    Bulk convert all text files in input directory to LabChart format.

    Args:
        input_dir: Input directory containing text files
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

    # Find text files
    text_files = find_text_files(input_dir)
    if not text_files:
        print(f"No text files found in {input_dir}")
        return []

    print(f"Found {len(text_files)} text files in {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

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

    # Process each file
    created_files = []
    for i, input_file in enumerate(text_files, 1):
        channel_num = i  # Use file index as channel number

        output_file = convert_file(
            input_file=input_file,
            exporter=exporter,
            output_dir=output_dir,
            channel_num=channel_num,
            interval_length=interval_length,
        )

        if output_file:
            created_files.append(output_file)

    print()
    print(f"Conversion complete!")
    print(f"Successfully converted {len(created_files)} out of {len(text_files)} files")
    print(f"Output files: {output_dir}")

    return created_files


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description="Bulk convert EEG text files to LabChart format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion with default settings
  python bulk_converter.py mock-inputs

  # Custom output directory and sample rate
  python bulk_converter.py mock-inputs output --sample-rate 1024 --range 30

  # European format with microvolts
  python bulk_converter.py data output --commas --microvolts

  # High precision timing in milliseconds
  python bulk_converter.py data output --milliseconds --absolute-time
        """,
    )

    parser.add_argument("input_dir", help="Input directory containing text files")

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
