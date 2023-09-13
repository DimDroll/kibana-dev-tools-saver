# Kibana Dev Tools Saver

## History

Since 2017 the feature to save and manage Dev Tools console commands is still being worked on [https://github.com/elastic/kibana/issues/10095](https://github.com/elastic/kibana/issues/10095).

In the meantime, I have not found any tool that would help to backup consoles queries easily for cases when your browsers data was cleared. So...

## Description

Kibana Dev Tools Saver is a Python script designed to extract and save Kibana's Dev Tools console data from ***Google Chrome's*** `localStorage`. It navigates through the LevelDB storage utilized by Chrome to store web data and filters out Kibana console queries for specified origins. The script offers flexibility in output options, allowing users to save the queries to files or view them directly in the console.

## Features

- **Extract Dev Tools Queries**: Navigate Chrome's underlying LevelDB structure to access `localStorage` data related to Kibana's Dev Tools.
- **Configurable Origins**: Specify which Kibana instances (by origin) you want to extract queries from.
- **Flexible Output**: Choose to print extracted queries to the console or save them to files.
- **Continuous Monitoring**: Option to keep the script running and periodically update the saved queries.
- **Logging & Error Handling**: Comprehensive logging provides insights into the script's operations and any potential issues.
- **Customizable Directories**: Specify source and temporary directories for Chrome's LevelDB.

## Prerequisites

Ensure you have Python3 and the required libraries installed:
```bash
pip3 install plyvel argparse logging
```

## Usage

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kibana-dev-tools-saver.git
cd kibana-dev-tools-saver
```

2. Run the script:
```bash
python3 kibana-dev-tools-saver.py
```


### Arguments:

- `-sd` or `--source-dir`: Specify the source directory of Chrome's LevelDB. (Default set in the script)
- `-td` or `--temp-dir`: Specify a temporary directory to copy LevelDB for processing. (Default set in the script)
- `-sf` or `--save-folder`: Specify a target folder to save the console outputs. (Defaults to console output if not specified)
- `-p` or `--prefix`: Add a prefix to the saved file names. (Optional)
- `-t` or `--time`: Set a time interval (in seconds) for how often the script should rerun and refresh the saved queries. (Optional)
- `-q` or `--quiet`: Suppress certain output logs. Useful when you're saving to a file and don't want to see every update in the console.
- `-ku` or `--kibana-urls`: Specify Kibana URLs separated by a comma to indicate from which origins you'd like to extract data.

### Examples:

As I developed it in Windows 10 WSL v2 Ubuntu Linux the path to Chrome localStorage folder is specified through the mount.

**Specify custom LevelDB directories and Kibana URLs:**
Replace <user> with your Windows username.
```bash
python3 kibana-dev-tools-saver.py -sd "/mnt/c/Users/<user>/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb/" -ku "https://kibana1.example.com,https://kibana2.example.com"
```

**Run continuously every 60 seconds in quite mode and save to specific folder with a prefix using specific temp folder:**
```bash
python3 kibana-dev-tools-saver.py -t 60 -sf /path/to/save -p myprefix_ -td /tmp/kibana-dev-tools-saver -q
```

Instead of using arguments you can specify defaults inside of the script.

## Contribution

Feel free to submit issues/suggestions, or make changes and open pull requests. All contributions are welcome!

## License

This project is open-source and available under the MIT License.

