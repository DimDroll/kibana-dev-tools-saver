# Kibana Dev Tools Saver

## Introduction 

Since 2017 the feature to save and manage Dev Tools console commands is still being worked on [https://github.com/elastic/kibana/issues/10095](https://github.com/elastic/kibana/issues/10095).

In the meantime, I have not found any tool that would help to backup consoles queries easily for cases when your browsers data was cleared. So...

## Description

Kibana Dev Tools Saver is a Python script designed to extract and save Kibana's Dev Tools console data from ***Google Chrome*** or ***Firefox*** `localStorage`. It navigates through the LevelDB storage used by Chrome (or the SQLite storage used by Firefox) to filter out Kibana console queries for specified origins. The script offers flexibility in output options, allowing users to save the queries to files or view them directly in the console.

## Features

- **Extract Dev Tools Queries**: Access `localStorage` data related to Kibana's Dev Tools from Chrome's LevelDB or Firefox's SQLite storage.
- **Firefox & Chrome Support**: Works with both browsers — browser is detected automatically from the path passed to `--source-db-path`.
- **Configurable Origins**: Specify which Kibana instances (by origin) you want to extract queries from (Chrome mode).
- **Flexible Output**: Choose to print extracted queries to the console or save them to files.
- **Continuous Monitoring**: Option to keep the script running and periodically update the saved queries.
- **Logging & Error Handling**: Comprehensive logging provides insights into the script's operations and any potential issues.
- **Customizable Paths**: Specify source and temporary paths for browser storage.

## Prerequisites

1. Clone the repository:
```bash
git clone https://github.com/DimDroll/kibana-dev-tools-saver.git
cd kibana-dev-tools-saver
```

2. Ensure you have Python 3 installed, then set up a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate        # On Windows (WSL): source venv/bin/activate
                                # On Windows native: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** `plyvel` (for Chrome/LevelDB) requires `libleveldb` to be installed on your system.
> On Ubuntu/Debian: `sudo apt-get install libleveldb-dev`

## Usage

Activate the virtual environment and run the script:
```bash
source venv/bin/activate
python3 kibana-dev-tools-saver.py
```

### Arguments:

| Short | Long               | Required | Browser        | Default | Description |
|-------|--------------------|----------|----------------|---------|-------------|
| `-sdp`| `--source-db-path` | Yes      | Chrome/Firefox | `-` | Path to browser storage. A **directory** for Chrome (LevelDB) or a **file** for Firefox (`data.sqlite`). Browser is detected automatically. |
| `-tp` | `--temp-path`      | No       | Chrome/Firefox | `/tmp/kibana-dev-tools-saver/` | Temporary directory to copy browser storage for processing. |
| `-ku` | `--kibana-urls`    | No       | Chrome         | `https://kibana1-example.com, https://kibana2-example.com` | Specify Kibana URLs separated by a comma to indicate from which origins you'd like to extract data. |
| `-sf` | `--save-folder`    | No       | Chrome/Firefox | `-` (print to console) | Specify a target folder to save the console outputs. |
| `-p`  | `--prefix`         | No       | Chrome/Firefox | `""` | Add a prefix to the saved file names. |
| `-t`  | `--time`           | No       | Chrome/Firefox | `-` (run once) | Set a time interval (in seconds) for how often the script should rerun and refresh the saved queries. |
| `-q`  | `--quiet`          | No       | Chrome/Firefox | `False` | Suppress certain output logs. Useful when you're saving to a file and don't want to see every update in the console. |


### Examples:

As I developed it in Windows 10 WSL v2 Ubuntu Linux the paths to browser data folders are specified through the WSL mount point `/mnt/c/`.

#### Chrome

Replace `<user>` with your Windows username.

**Specify LevelDB path and Kibana URLs:**
```bash
python3 kibana-dev-tools-saver.py \
  -sdp "/mnt/c/Users/<user>/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb/" \
  -ku "https://kibana1.example.com,https://kibana2.example.com"
```

**Run continuously every 60 seconds in quiet mode, save to a folder with a prefix:**
```bash
python3 kibana-dev-tools-saver.py \
  -sdp "/mnt/c/Users/<user>/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb/" \
  -t 60 -sf /path/to/save -p myprefix_ -tp /tmp/kibana-dev-tools-saver -q
```

#### Firefox

Firefox stores one `data.sqlite` file per origin inside the profile directory at:
```
<profile>/storage/default/https+++<kibana-hostname>/ls/data.sqlite
```

Replace `<user>` and `<profile>` with your Windows username and Firefox profile folder name.

**Extract and print to console:**
```bash
python3 kibana-dev-tools-saver.py \
  -sdp "/mnt/c/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/<profile>/storage/default/https+++<kibana-hostname>/ls/data.sqlite"
```

**Save to a folder with a prefix:**
```bash
python3 kibana-dev-tools-saver.py \
  -sdp "/mnt/c/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/<profile>/storage/default/https+++<kibana-hostname>/ls/data.sqlite" \
  -sf /path/to/save -p firefox_
```

**Run continuously every 60 seconds in quiet mode:**
```bash
python3 kibana-dev-tools-saver.py \
  -sdp "/mnt/c/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/<profile>/storage/default/https+++<kibana-hostname>/ls/data.sqlite" \
  -t 60 -sf /path/to/save -q
```

Instead of using arguments you can specify defaults inside of the script.

## Troubleshooting

### CorruptionError (Chrome only)

Sometimes the script copies LevelDB while Chrome is writing to it, which results in the script's **copy** of this DB stored in temp to become corrupted.
Re-run the script a few more times to see if the problem disappears, or else open an issue and provide information about your env.
```bash
Traceback (most recent call last):
  File "kibana-dev-tools-saver.py", line 198, in <module>
    main()
  File "kibana-dev-tools-saver.py", line 174, in main
    for origin, text_content in extractor:
  File "kibana-dev-tools-saver.py", line 113, in extract_console_data_from_leveldb
    db = plyvel.DB(temp_path, create_if_missing=False)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "plyvel/_plyvel.pyx", line 247, in plyvel._plyvel.DB.__init__
  File "plyvel/_plyvel.pyx", line 91, in plyvel._plyvel.raise_for_status
plyvel._plyvel.CorruptionError: b'Corruption: 1 missing files; e.g.: /tmp/kibana-dev-tools-saver//000446.ldb'
```

## Disclaimer

This tool is provided "as is" without any warranties or guarantees of any kind. Users should use Kibana Dev Tools Saver responsibly and at their own risk. Always make sure to have backups of important data. The author or contributors are not responsible for any loss of data, adverse effects, or any other negative impacts resulting from the use of this script. Make sure to always review the code and understand its operations before executing it in a live environment.


## Contribution

Feel free to submit issues/suggestions, or make changes and open pull requests. All contributions are welcome!

## License

This project is open-source and available under the MIT License.
