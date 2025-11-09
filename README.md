# Neuroplayer to LabChart Exporter (Python)

Python conversion of the LabChart Exporter from the [Neuroplayer Processor Library](https://www.opensourceinstruments.com/Electronics/A3018/Processor_Library.html).

## Overview

This tool converts EEG data from Neuroplayer's NDF (Neuroscience Data Format) files into text format suitable for import into LabChart software. The output format follows the LabChart specification with proper headers and time-voltage pairs.

If you just want to get started follow the [Quick Start Guide](QUICK_START.md)

## Why Python Instead of TCL?

While Open Source Instruments provides excellent TCL scripts for LabChart export, this Python implementation addresses several practical challenges:

**Accessibility and Familiarity**
- TCL usage can be unfamiliar to many users, making debugging or extension more challenging
- Python's widespread adoption in research communities makes the tool more approachable
- Clearer error messages and debugging capabilities for non-expert users

**Installation and Deployment**
- Installation on heavily controlled environments (such as university-owned machines) can be non-trivial with TCL
- Python is commonly pre-installed or easily installed on most research systems
- Simpler dependency management and distribution

**Usability Improvements**
- Usage of existing TCL tooling requires copy/paste of individual scripts to files
- This Python version provides ready-to-run command-line tools
- Bulk processing capabilities for handling multiple files efficiently

**Research-Specific Focus**
- This implementation focuses specifically on LabChart export workflows
- The original TCL toolkit includes many additional analysis tools not covered here
- This Python version expands the LabChart conversion features with bulk processing and multiple output formats

This Python version maintains full compatibility with the original TCL output while providing a more accessible and extensible platform for EEG data processing.

## Files

### Core Tools
- **`labchart_exporter.py`** - Main exporter class with LabChart format generation
- **`ndf_reader.py`** - Helper classes for reading signal data from NDF files
- **`bulk_converter.py`** - Command-line tool for bulk conversion of text files to LabChart
- **`ndf_to_text_converter.py`** - Command-line tool for converting NDF files to readable text format

### Documentation
- **`README.md`** - Complete technical documentation and usage guide
- **`QUICK_START.md`** - User-friendly guide for non-technical users
- **`CONTRIBUTING.md`** - Guidelines for contributing to the project

### Sample Data
- **`mock-inputs/`** - Sample EEG text files for testing conversion workflow

### Configuration
- **`.gitignore`** - Git ignore file for clean repository management

## Features

The exporter supports all the configuration options from the original TCL script:

- **Sample rate configuration** - Set the sampling frequency (default: 512 Hz)
- **Dynamic range** - Configure the input range in mV (default: 120 mV for DC transmitters)
- **Time format** - Output in seconds or milliseconds
- **Voltage format** - Output in millivolts or microvolts
- **Time reference** - Absolute UNIX time or relative time from start
- **European format** - Use commas instead of decimal points
- **Glitch filtering** - Remove single-sample spikes (configurable threshold)

## Installation

The core library uses only Python standard library, but some examples require additional packages.

### Basic Installation

```bash
# Simply copy the files to your working directory
# Requires Python 3.6+
```

### For Examples and Advanced Features

```bash
# Install numpy for synthetic data generation examples
pip install numpy

# Numpy is used in:
# - labchart_exporter.py example_usage()
# - ndf_reader.py example_with_synthetic_data()
# - Some documentation examples with synthetic signals
```

**Note**: Numpy is optional and only needed if you plan to run the included examples or generate synthetic test data. The main conversion tools (`ndf_to_text_converter.py`, `bulk_converter.py`) work with standard Python only.

## Workflows

### Complete NDF to LabChart Workflow (Recommended for Real Data)

For processing real Neuroplayer NDF files:

```bash
# Step 1: Convert NDF files to readable text format (creates subdirectories per NDF file)
python ndf_to_text_converter.py raw_ndf_files/ --output readable_text/

# Step 2: Convert subdirectories to unified LabChart format (one file per NDF source)
python bulk_converter.py readable_text/ --output labchart_files/ --range 120
```

**Output Structure:**

After Step 1, you'll have:
```
readable_text/
├── M1555404530/
│   ├── E1.txt
│   ├── E2.txt
│   └── E15.txt
└── M1555404531/
    ├── E1.txt
    └── E2.txt
```

After Step 2, you'll have unified LabChart files:
```
labchart_files/
├── M1555404530.txt  (contains all channels in tab-separated columns)
└── M1555404531.txt  (contains all channels in tab-separated columns)
```

### Direct Text to LabChart Conversion

For directories containing E{channel}.txt files:

```bash
# Convert all channel directories to unified LabChart files
python bulk_converter.py input_folder

# Custom output directory
python bulk_converter.py input_folder output_folder

# With custom settings
python bulk_converter.py input_folder output_folder --sample-rate 512 --range 120
```

**Note:** The bulk converter now expects a directory structure with subdirectories containing E{channel}.txt files (e.g., E1.txt, E2.txt). Each subdirectory is converted into a single unified LabChart file with all channels as tab-separated columns.

#### Bulk Converter Options

```bash
python bulk_converter.py [input_dir] [output_dir] [options]

Options:
  --sample-rate, -sr    Sample rate in Hz (default: 512)
  --range, -r          Input dynamic range in mV (default: 120)
  --interval-length    Length of each interval in seconds (default: 1.0)
  --commas             Use European format (commas for decimals)
  --milliseconds       Express time in milliseconds
  --microvolts         Express voltage in microvolts
  --absolute-time      Use absolute UNIX time
  --glitch-threshold   Glitch filter threshold (default: 500, 0 to disable)
  --verbose, -v        Verbose output
  --help, -h           Show help message
```

#### Bulk Converter Examples

```bash
# Standard DC transmitter processing (processes subdirectories)
python bulk_converter.py ndf_text_output output --range 120

# AC transmitter with different settings
python bulk_converter.py ndf_text_output output --range 30 --sample-rate 1024

# European format with microvolts
python bulk_converter.py ndf_text_output output --commas --microvolts

# High precision timing
python bulk_converter.py ndf_text_output output --milliseconds --absolute-time
```

## NDF File Processing

### NDF to Text Conversion

The `ndf_to_text_converter.py` tool converts Neuroplayer NDF files to readable text format:

```bash
# Convert single NDF file
python ndf_to_text_converter.py data.ndf

# Convert entire directory
python ndf_to_text_converter.py ndf_directory/

# Extract specific channels
python ndf_to_text_converter.py data.ndf --channels 0 1 2 3

# Different output formats
python ndf_to_text_converter.py data.ndf --format detailed --timestamps
python ndf_to_text_converter.py data.ndf --format csv --output csv_files/
```

#### NDF Converter Options

```bash
python ndf_to_text_converter.py [input_path] [options]

Options:
  --output, -o          Output directory (default: input_path + '_text')
  --channels, -c        Specific channels to extract (default: all channels)
  --format, -f          Output format: simple, detailed, csv (default: simple)
  --sample-rate, -sr    Sample rate in Hz (default: 512)
  --timestamps          Include timestamp information
  --no-metadata         Exclude metadata headers
  --verbose, -v         Verbose output
```

#### Output Formats

- **Simple**: One sample value per line (compatible with `bulk_converter.py`). Files are organized in subdirectories named after the source NDF file, with individual E{channel}.txt files for each channel.
- **Detailed**: Includes interval and timing information for analysis
- **CSV**: Comma-separated format for spreadsheet analysis

**Output Structure:** When converting NDF files, the tool creates subdirectories for each source file:
```
output_dir/
├── M1555404530/    (from M1555404530.ndf)
│   ├── E1.txt
│   ├── E2.txt
│   └── E15.txt
└── M1555404531/    (from M1555404531.ndf)
    ├── E1.txt
    └── E2.txt
```

#### NDF File Structure

The NDF reader automatically handles:
- **File Detection**: Finds telemetry data section in NDF files
- **Channel Extraction**: Supports all 16 channels (0-15) from OSI transmitters
- **Message Parsing**: Decodes 8-byte telemetry messages
- **Timing Reconstruction**: Converts timestamps to relative timing
- **Data Validation**: Ensures 16-bit signal compatibility

### Manual Conversion (API Usage)

For programmatic control or single file processing:

#### Basic Example

```python
from labchart_exporter import LabChartExporter

# Create exporter with default settings
exporter = LabChartExporter(
    sample_rate=512.0,
    range_mV=120.0,  # DC transmitter with x25 gain
)

# Example: Export data for channel 1
# signal_values should be a list of 16-bit integers (0-65535)
intervals = [
    (0.0, signal_values_0),   # (start_time, list of sample values)
    (1.0, signal_values_1),   # Next interval
    # ... more intervals
]

output_file = exporter.export_channel(
    output_dir="./output",
    channel_num=1,
    intervals=intervals,
    creation_date="2025-11-03 10:00:00"
)
```

### Configuration Options

```python
exporter = LabChartExporter(
    sample_rate=512.0,        # Sampling rate in Hz
    range_mV=120.0,           # Input dynamic range in mV
    use_commas=False,         # True for European format (commas instead of periods)
    time_in_ms=False,         # True for milliseconds, False for seconds
    value_in_uV=False,        # True for microvolts, False for millivolts
    absolute_time=False,      # True for UNIX time, False for relative time
    glitch_threshold=500      # Glitch filter threshold (0 to disable)
)
```

### Transmitter Dynamic Range Settings

Common settings for different Open Source Instruments transmitters:

```python
# DC transmitter with x25 gain (e.g., A3047 with 3V battery)
range_mV = 120.0

# AC transmitter with typical 30 mV range (e.g., A3028)
range_mV = 30.0

# DC transmitter with x1 gain (e.g., wider range)
range_mV = 300.0
```

### Working with Different Input Formats

#### 1. NDF Files (Real Neuroplayer Data)

```python
from ndf_reader import NDFReader
from labchart_exporter import LabChartExporter

# Read real NDF file
reader = NDFReader('data.ndf')

# Get file information
print(f"Created: {reader.get_creation_date()}")
print(f"Channels: {reader.get_available_channels()}")

# Extract specific channel
intervals = reader.read_channel_data(channel_num=1, sample_rate=512.0)

# Export to LabChart
exporter = LabChartExporter(sample_rate=512.0, range_mV=120.0)
output_file = exporter.export_channel(
    output_dir='./output',
    channel_num=1,
    intervals=intervals,
    creation_date=reader.get_creation_date()
)
```

#### 2. Binary Signal Files

```python
from ndf_reader import SimpleBinarySignalReader

# Read 16-bit binary data
intervals = SimpleBinarySignalReader.read_signal(
    filepath="signal_data.bin",
    sample_rate=512.0,
    interval_length=1.0  # Split into 1-second intervals
)

# Export to LabChart
exporter.export_channel(
    output_dir="./output",
    channel_num=1,
    intervals=intervals
)
```

#### 3. Text Signal Files

```python
from ndf_reader import TextSignalReader

# Read text file (one value per line)
intervals = TextSignalReader.read_signal(
    filepath="signal_data.txt",
    sample_rate=512.0,
    interval_length=1.0
)
```

#### 4. Direct from Arrays

```python
import numpy as np  # pip install numpy

# If you already have your data in arrays
signal = np.array([...])  # Your signal data
signal_values = signal.astype(int).tolist()

# Create single interval
intervals = [(0.0, signal_values)]

# Or multiple intervals
intervals = [
    (0.0, signal_values[0:512]),
    (1.0, signal_values[512:1024]),
    # etc.
]
```

## Output Format

The exporter creates unified LabChart files with all channels in a single file:

### Single-Channel Format (Legacy)

Individual channel files `E{channel_num}.txt` with the following structure:

```
Interval= 0.001953125
DateTime= 2025-11-03 10:00:00
TimeFormat=
ChannelTitle= 1
Range= 120.0
0.000000 0.0915
0.001953 0.0923
0.003906 0.0931
...
```

### Multi-Channel Unified Format (Current)

Unified files with all channels as tab-separated columns:

```
Interval= 0.001953125
DateTime= 2025-11-03 10:00:00
TimeFormat=
ChannelTitle= 1, 2, 15
Range= 120.0
0.000000	0.0915	0.0923	0.0931
0.001953	0.0916	0.0924	0.0932
0.003906	0.0917	0.0925	0.0933
...
```

### Header Fields

- **Interval** - Time between samples (1/sample_rate)
- **DateTime** - Recording creation date
- **TimeFormat** - Reserved (left blank per LabChart spec)
- **ChannelTitle** - Channel identifier(s), comma-separated for multi-channel
- **Range** - Full-scale range in mV or μV

### Data Format

**Single-channel:** Each line after the header contains:
```
<time> <voltage>
```

**Multi-channel:** Each line after the header contains:
```
<time>	<voltage_ch1>	<voltage_ch2>	<voltage_ch3>	...
```

Where:
- `time` - Timestamp in seconds or milliseconds
- `voltage` - Signal amplitude in mV or μV
- Tab character separates columns in multi-channel format

## Glitch Filtering

The exporter includes optional glitch filtering to remove single-sample artifacts:

```python
# Enable glitch filtering (default: 500 counts)
exporter = LabChartExporter(glitch_threshold=500)

# Disable glitch filtering
exporter = LabChartExporter(glitch_threshold=0)
```

The glitch filter detects single samples that differ from both neighbors by more than the threshold and replaces them with the average of the neighboring samples.

## NDF File Integration

The included `NDFReader` class is a template for reading actual NDF files. You'll need to implement the specific NDF parsing based on your file format:

```python
class NDFReader:
    def read_channel_data(self, channel_num, sample_rate):
        # Implement NDF file parsing here
        # 1. Find data section in NDF file
        # 2. Parse telemetry messages
        # 3. Reconstruct signal with timing
        # 4. Handle message loss
        pass
```

## Running the Examples

The package includes several ways to test and run examples:

### Test with Real NDF Data

```bash
# Convert real NDF files to text format (using OSI demo data)
python ndf_to_text_converter.py ECP20_Demo/ --channels 0 1 --output ndf_text/

# Convert text files to LabChart format (note: use --range 30 for A3028B3 transmitters)
python bulk_converter.py ndf_text/ --output labchart_files/ --range 30

# View the results
ls labchart_files/
```

### Test with Mock Data

```bash
# Convert the provided mock EEG files
python bulk_converter.py mock-inputs

# View the results
ls mock-inputs_labchart/
```

### Run Individual Examples

```bash
# NDF to text conversion examples
python ndf_to_text_converter.py --help

# Text to LabChart conversion examples
python bulk_converter.py --help

# Run the basic exporter example
python labchart_exporter.py

# Run the signal reader example with synthetic data
python ndf_reader.py
```

### Sample Data Files

#### Mock Text Files (`mock-inputs/`)

Sample EEG data in text format for testing:

- **`baseline_eeg.txt`** - Quiet background activity
- **`alpha_waves_eeg.txt`** - 10 Hz alpha wave oscillations
- **`theta_waves_eeg.txt`** - 4 Hz theta wave oscillations
- **`artifact_noise_eeg.txt`** - Electrical interference and artifacts
- **`mixed_frequency_eeg.txt`** - Combined frequency bands (delta, theta, alpha, beta)

#### Real NDF Data for Testing (OSI ECP20_Demo Package)

For comprehensive testing with real-world data, Open Source Instruments provides the ECP20_Demo package - a 290 MB demonstration dataset containing twenty-five hours of recordings from mice. These recordings are made with A3028B3 transmitters and include both control and pilocarpine-injected animals.

*Demo data provided by Adrien Zanin and Jean Christophe Poncer, INSERM, Paris, France.*

**What's included:**
- **Real EEG data** for testing your analysis process
- **Event library** with baseline, ictal, spike, and artifact events
- **File characteristics** for practice creating characteristics files
- **Multiple recording sessions** from actual research

**How to get it:**
Download the ECP20_Demo package directly: [ECP20_Demo.zip](https://www.opensourceinstruments.com/SCT/Recordings/ECP20_Demo.zip) (290 MB)

This demonstration data from Open Source Instruments will help you validate your analysis process and conversion to LabChart, ensuring your conversion process is working correctly before applying it to your own research data.

**Using the demo data:**
```bash
# After downloading and extracting the ECP20_Demo package
python ndf_to_text_converter.py ECP20_Demo/ --channels 0 1 2
python bulk_converter.py ECP20_Demo_text/ --range 30
```

*Note: Use `--range 30` for A3028B3 AC transmitters as specified in the demo documentation.*

## Differences from TCL Version

The Python version maintains functional equivalence with the TCL script while providing:

1. **Object-oriented design** - Cleaner API with `LabChartExporter` class
2. **Type hints** - Better documentation and IDE support
3. **Separate concerns** - File I/O separated from data processing
4. **Extensibility** - Easy to add new input readers
5. **Bulk processing** - Command-line tools for processing multiple files
6. **NDF support** - Complete integration with real Neuroplayer data files
7. **Multiple workflows** - Support for both NDF and text input formats
8. **Mock data** - Sample files for testing and validation

## Notes

1. **Signal values** must be 16-bit integers (0-65535) representing ADC counts
2. **Timestamps** should be in seconds (floating point)
3. **File names** follow the pattern `E{channel}.txt` per Neuroplayer convention
4. The exporter **appends** to existing files - delete old files if you want fresh exports
5. **Multi-channel output** combines all channels into a single unified file with tab-separated columns
6. **NDF files** are automatically parsed to extract channel data and metadata
7. **Text conversion** creates subdirectories per NDF file with `E{channel}.txt` files for each channel
8. **Directory structure** is important: bulk_converter expects subdirectories containing E{channel}.txt files

## Troubleshooting

### Issue: Values out of range
```python
# Ensure your values are 16-bit (0-65535)
signal_values = np.clip(signal, 0, 65535).astype(np.uint16).tolist()
```

### Issue: Time synchronization
```python
# Make sure timestamps are consistent across intervals
# Each interval should start where the previous ended
timestamp_n = timestamp_0 + n * interval_length
```

### Issue: Wrong voltage scale
```python
# Check your transmitter's dynamic range
# DC transmitters typically: 120-300 mV
# AC transmitters typically: 30 mV
```

### Issue: NDF files not found or processed
```bash
# Ensure file has .ndf extension and is valid
python ndf_to_text_converter.py --help

# Check available channels in NDF file
python -c "from ndf_reader import NDFReader; r=NDFReader('file.ndf'); print(r.get_available_channels())"
```

### Issue: No telemetry data found
```bash
# The NDF reader automatically searches for data
# If this fails, the file may be corrupted or in a different format
# Check the file size and creation date
```

## References

- [Neuroplayer Processor Library](https://www.opensourceinstruments.com/Electronics/A3018/Processor_Library.html)
- [LabChart Exporter V4 TCL Script](https://www.opensourceinstruments.com/Electronics/A3018/Code/LabChart_Exporter_V4.tcl)
- [Open Source Instruments](https://www.opensourceinstruments.com/)

## License

This code is derived from open source examples provided by Open Source Instruments. Please check their website for license terms.

## Contributing

Please see our [Contributers Guide](CONTRIBUTING.md) for full details on contributing to this project.
