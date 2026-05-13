import shutil
import os
import sqlite3
import json
import argparse
import logging
import time

try:
    import snappy
    import plyvel
except ImportError as e:
    print(f"Error: Missing required dependency — {e}")
    print("Please set up the virtual environment and install dependencies:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate    # Windows: venv\\Scripts\\activate")
    print("  pip install -r requirements.txt")
    exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default values
KIBANA_URLS = [
    "https://kibana1-example.com",
    "https://kibana2-example.com",
]
SOURCE_DB_PATH = None  # Set your path here, or use --source-db-path
TEMP_PATH = "/tmp/kibana-dev-tools-saver/"
SAVE_FOLDER = None
DEFAULT_PREFIX = ""
DEFAULT_TIME = None

# Argument parsing
parser = argparse.ArgumentParser(description="Extract and save Kibana's console data from Chrome's or Firefox's localStorage.")
parser.add_argument("-sdp", "--source-db-path", type=str, default=SOURCE_DB_PATH, help="Path to browser storage: a directory for Chrome (LevelDB) or a file for Firefox (data.sqlite). Browser is detected automatically.")
parser.add_argument("-tp", "--temp-path", type=str, default=TEMP_PATH, help="Temporary directory to copy browser storage for processing.")
parser.add_argument("-sf", "--save-folder", type=str, default=SAVE_FOLDER, help="Target folder to save the console outputs.")
parser.add_argument("-p", "--prefix", type=str, default=DEFAULT_PREFIX, help="Prefix to prepend to saved filenames.")
parser.add_argument("-t", "--time", type=int, default=DEFAULT_TIME, help="Time in seconds to wait between reruns of the script.")
parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output if saving to a file.")
parser.add_argument("-ku", "--kibana-urls", type=str, default=",".join(KIBANA_URLS), help="Comma-separated list of Kibana URLs to extract data from (Chrome mode only).")
args = parser.parse_args()
KIBANA_URLS = [url.strip() for url in args.kibana_urls.split(",") if url.strip()]

# Argument validation
if not args.source_db_path:
    parser.print_help()
    print("\nError: No source configured.")
    print("  --source-db-path  Chrome:  path to the LevelDB directory")
    print("                    Firefox: path to the data.sqlite file")
    exit(1)

if args.time is not None and args.time <= 0:
    logging.error("--time must be a positive integer.")
    exit(1)

if args.quiet and not args.save_folder:
    logging.warning("--quiet has no effect without --save-folder.")

def copy_to_temp(source_path):
    if os.path.exists(args.temp_path):
        user_input = input(f"Temporary directory {args.temp_path} already exists. Do you want to delete it? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            try:
                shutil.rmtree(args.temp_path)
            except Exception as e:
                logging.error(f"Error removing existing temporary directory: {e}")
                raise
        elif user_input in ['n', 'no']:
            logging.info("Exiting without making changes.")
            exit(0)
        else:
            logging.error("Invalid choice. Exiting.")
            exit(1)

    try:
        if os.path.isfile(source_path):              # Firefox SQLite
            os.makedirs(args.temp_path)
            temp_db = os.path.join(args.temp_path, "data.sqlite")
            shutil.copy2(source_path, temp_db)
            # Copy WAL and SHM files if present for a consistent snapshot
            for suffix in ["-wal", "-shm"]:
                if os.path.exists(source_path + suffix):
                    shutil.copy2(source_path + suffix, temp_db + suffix)
            return temp_db
        else:                                        # Chrome LevelDB directory
            shutil.copytree(source_path, args.temp_path, ignore=shutil.ignore_patterns('LOCK'))
            return args.temp_path
    except Exception as e:
        logging.error(f"Error copying browser storage to temporary directory: {e}")
        raise

def delete_temp_path():
    if os.path.exists(args.temp_path):
        try:
            shutil.rmtree(args.temp_path)
        except Exception as e:
            logging.error(f"Error deleting temporary directory: {e}")
            raise

def extract_console_data_from_leveldb(temp_path):
    db = plyvel.DB(temp_path, create_if_missing=False)
    for key, value in db.iterator():
        try:
            key_utf8 = key.decode('utf-8')
        except UnicodeDecodeError:
            logging.warning(f"Key cannot be decoded as UTF-8: {key}")
            continue

        for origin in KIBANA_URLS:
            if origin in key_utf8 and "sense:console_local_text-object_" in key_utf8:
                try:
                    # Removing the first character which is a non-JSON character.
                    clean_value = value[1:].decode('utf-8')
                    json_data = json.loads(clean_value)
                    text_content = '\n'.join(json_data.get('text', '').splitlines()) # fix windows like characters (^M)
                    yield origin, text_content
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON for key {key}. Raw value: {value}")
    db.close()

def extract_console_data_from_sqlite(db_path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute("SELECT origin FROM database LIMIT 1")
        row = cur.fetchone()
        origin = row[0] if row else "unknown"

        cur.execute(
            "SELECT value, compression_type FROM data "
            "WHERE key LIKE 'sense:console_local_text-object_%'"
        )
        for value_blob, compression_type in cur.fetchall():
            try:
                raw = snappy.decompress(value_blob) if compression_type == 1 else value_blob
                json_data = json.loads(raw.decode('utf-8'))
                text_content = '\n'.join(json_data.get('text', '').splitlines())
                yield origin, text_content
            except Exception as e:
                logging.warning(f"Failed to decode console data from {db_path}: {e}")
    finally:
        conn.close()

def main():
    source = args.source_db_path
    data_found = False

    def handle_result(origin, text_content):
        nonlocal data_found
        data_found = True
        if not args.quiet:
            logging.info(f"Kibana: \"{origin}\"")
        if args.save_folder:
            os.makedirs(args.save_folder, exist_ok=True)
            file_name = f"{args.prefix}{origin.replace('https://', '').replace('/', '_')}.console"
            full_path = os.path.join(args.save_folder, file_name)
            with open(full_path, 'w') as f:
                f.write(text_content)
            if not args.quiet:
                logging.info(f"Saving {origin} to {full_path}...")
        else:
            print(text_content)

    if not os.path.exists(source):
        logging.error(f"Path does not exist: {source}")
        exit(1)

    temp_path = copy_to_temp(source)

    if os.path.isfile(source):                      # Firefox
        extractor = extract_console_data_from_sqlite(temp_path)
        no_data_msg = "No console data found in the specified SQLite file."
    else:                                           # Chrome
        extractor = extract_console_data_from_leveldb(temp_path)
        no_data_msg = f"No data found for the provided Kibana URLs: {', '.join(KIBANA_URLS)}"

    for origin, text_content in extractor:
        handle_result(origin, text_content)

    delete_temp_path()
    if not data_found:
        logging.warning(no_data_msg)

if __name__ == "__main__":
    if args.time:
        try:
            while True:
                main()
                if not args.quiet:
                    logging.info(f"Sleeping for {args.time} seconds...")
                time.sleep(args.time)
        except KeyboardInterrupt:
            logging.info("Interrupted by user. Cleaning up...")
            delete_temp_path()
    else:
        main()
