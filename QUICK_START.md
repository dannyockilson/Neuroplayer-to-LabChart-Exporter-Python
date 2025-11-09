# Quick Start Guide

This guide will help you convert your EEG data files from Neuroplayer (NDF format) into a format that LabChart can import and analyze. No programming experience is required.

## Step 1: Install Python

Python is the programming language this tool uses. You won't need to write any code, just run simple commands.

### For Windows Users

**Easiest method - Microsoft Store:**
1. Open the Microsoft Store app
2. Search for "Python"
3. Click on "Python 3.11" (or the latest version shown)
4. Click "Install"
5. Wait for installation to complete - that's it!

**Alternative method - Direct download:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the yellow "Download Python" button
3. Run the downloaded installer
4. **Important**: Check the box that says "Add Python to PATH" during installation
5. Click "Install Now"

### For Mac Users

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the yellow "Download Python" button
3. Open the downloaded .pkg file
4. Follow the installation steps
5. Python will be installed and ready to use

### Test Your Installation

Open a command prompt (instructions below) and type:

```
python --version
```

You should see something like "Python 3.11.0" or similar. If you get an error, try `python3 --version` instead.

## Step 2: Learn the Command Line Basics

The command line (also called terminal or command prompt) is where you'll run the conversion tools.

### Opening the Command Line

**Windows:**
- Press `Windows key + R`, type `cmd`, and press Enter
- OR: Click Start menu, type "Command Prompt", and press Enter

**Mac:**
- Press `Cmd + Space`, type "Terminal", and press Enter
- OR: Go to Applications → Utilities → Terminal

### Navigating to Your Files

You need to tell the command line where your files are located. Use the `cd` (change directory) command:

**Example for Windows:**
```
cd C:\Users\YourName\Documents\eeg-data
```

**Example for Mac:**
```
cd /Users/YourName/Documents/eeg-data
```

**Tip:** On Windows, you can hold Shift and right-click in a folder, then select "Open PowerShell window here" or "Open command window here" to open the command line in that location.

### Running Python Commands

Once you're in the right folder, you'll run commands that start with `python` (or `python3` on some systems). The format is always:

```
python script_name.py [options]
```

## Step 3: Set Up Your Workspace

1. Download or copy all the tool files to a folder on your computer
    a. For users familiar with git, clone this repository
    b. Alternatively use the "Code" button on github and select "Download ZIP". You will then need to extract files to a folder to begin working with them.
2. Create a folder for your NDF files (e.g., "my-ndf-files")
3. Copy your EEG data files (.ndf files) into that folder

Your folder structure should look like:
```
your-workspace/
├── ndf_to_text_converter.py
├── bulk_converter.py
├── labchart_exporter.py
├── ndf_reader.py
├── my-ndf-files/
│   ├── recording1.ndf
│   ├── recording2.ndf
│   └── recording3.ndf
```

### Already converted files via Neuroplayer to txt?

You will still need to download or copy all the tool files to a folder on your computer (as above) but instead of copying your NDF files, create a folder and copy in your .txt files instead (e.g., "my-text-files").

You can then skip step 4.a below and move directly to the conversion to LabChart supported formats.

## Step 4: Convert Your Data

The conversion process involves two steps:

### Step A: Convert NDF files to readable text

First, we'll convert your NDF files into a text format that's easier to work with.

Open the command line in your workspace folder and run this command:

```
python ndf_to_text_converter.py my-ndf-files
```

This will:
- Read all the .ndf files in your "my-ndf-files" folder
- Extract the EEG data from each file
- Create a folder called "my-ndf-files_text" with subdirectories for each NDF file
- Each subdirectory contains E1.txt, E2.txt, etc. for each channel

**What happens:** The tool finds all your recording files and extracts the brain signal data from each one. For each NDF file (like M1555404530.ndf), it creates a matching subdirectory (M1555404530/) with separate channel files (E0.txt, E1.txt, E2.txt, etc.).

**Important note on channels:**
- Channel 0: Clock signal (128 Hz) - used for timing synchronization
- Channels 1-15: EEG data channels (512 Hz) - your brain activity recordings

The tool automatically detects and uses the correct rate for each channel type.

#### Performance Notes

The NDF conversion step processes about **110MB per minute** on typical hardware. Here are some time estimates:

- **Small dataset** (1-5 files, ~80MB): 1-2 minutes
- **Medium dataset** (10-20 files, ~200MB): 3-5 minutes
- **Large dataset** (50+ files, ~500MB): 8-12 minutes
- **Full day recording** (100+ files, ~1GB): 15-20 minutes

**Tips for large datasets:**
- The tool shows progress as it processes each file
- You can safely interrupt with Ctrl+C and restart - it will skip already converted files
- Consider converting overnight for very large datasets (500+ files)
- Step B (text to LabChart) is much faster and typically takes under 1 minute

### Step B: Convert text files to LabChart format

Next, we'll convert those text files into the specific format that LabChart expects.

Run this command:

```
python bulk_converter.py my-ndf-files_text --range 120
```

This will:
- Read all the subdirectories from the previous step
- Combine all channels from each subdirectory into a single unified file
- Create the final files in "my-ndf-files_text_labchart"

**What happens:** The tool processes each subdirectory (representing one NDF file) and combines all its channels (E1.txt, E2.txt, etc.) into a single LabChart file with all channels as columns separated by tabs. This means you get one LabChart file per original NDF file, with all channels included in that single file.

## Step 5: Import into LabChart

Your converted files are now in the "my-ndf-files_text_labchart" folder. Each file is named after the original NDF file (e.g., M1555404530.txt) and contains all channels from that recording in a single file.

To import them into LabChart:
1. Open LabChart
2. Go to File → Open or Import
3. Navigate to your "my-ndf-files_text_labchart" folder
4. Select the .txt file(s) you want to analyze (e.g., M1555404530.txt)
5. Follow LabChart's import wizard

**Note:** Each file contains all channels as separate columns, so you'll see all your EEG channels in a single LabChart document once imported.

## Common Situations

### If you only want specific channels

Sometimes you only need certain EEG channels. Add `--channels` followed by the channel numbers you want:

```
python ndf_to_text_converter.py my-ndf-files --channels 0 1 2
```

This example only extracts channels 0, 1, and 2 from your files.

### If you're working with AC transmitters

Different EEG transmitters have different voltage ranges. If you're using AC transmitters (like the A3028), use a different range setting:

```
python bulk_converter.py my-ndf-files_text --range 30
```

The most common settings are:
- `--range 120` for DC transmitters (most common)
- `--range 30` for AC transmitters

### If you need help with any command

You can always get help by adding `--help` to any command:

```
python ndf_to_text_converter.py --help
python bulk_converter.py --help
```

## Troubleshooting

### "Python is not recognized" error

This usually means Python isn't installed correctly or isn't added to your PATH. Try:
1. Restart your command prompt
2. Try `python3` instead of `python`
3. Reinstall Python and make sure to check "Add Python to PATH"

### "No such file or directory" error

This means the command line can't find your files. Make sure:
1. You're in the right folder (`cd` to your workspace)
2. The file names match exactly (including .ndf extension)
3. The folder names don't have spaces or special characters

### Files seem to be processing but no output

Make sure:
1. Your NDF files aren't empty or corrupted
2. You have enough free disk space
3. You have write permissions in the folder

### Getting different results than expected

Check:
1. Are you using the right `--range` setting for your transmitter type?
2. Are you extracting the right channels?
3. Do your original NDF files contain the expected data?

## Need More Help?

For advanced features and detailed technical information, see the complete `README.md` file. If you're comfortable with more technical details, the README contains comprehensive documentation about all available options and features.

Remember: this process converts your research data files - always keep backups of your original NDF files!