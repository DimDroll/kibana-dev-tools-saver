import shutil
import os
import plyvel
import json
import argparse
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default values
KIBANA_URLS = [
    "https://kibana1-example.com",
    "https://kibana2-example.com",
]
SOURCE_DIR = "/mnt/c/Users/<user>/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb/"
TEMP_DIR = "/tmp/kibana-dev-tools-saver/"
DEFAULT_FOLDER = None
DEFAULT_PREFIX = ""
DEFAULT_TIME = None

# Argument parsing
parser = argparse.ArgumentParser(description="Extract and save Kibana's console data from Chrome's localStorage.")
parser.add_argument("-sd", "--source-dir", type=str, default=SOURCE_DIR, help="Source directory of Chrome's LevelDB.")
parser.add_argument("-td", "--temp-dir", type=str, default=TEMP_DIR, help="Temporary directory to copy LevelDB for processing.")
parser.add_argument("-sf", "--save-folder", type=str, default=DEFAULT_FOLDER, help="Target folder to save the console outputs.")
parser.add_argument("-p", "--prefix", type=str, default=DEFAULT_PREFIX, help="Prefix to prepend to saved filenames.")
parser.add_argument("-t", "--time", type=int, default=DEFAULT_TIME, help="Time in seconds to wait between reruns of the script.")
parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output if saving to a file.")
parser.add_argument("-ku", "--kibana-urls", type=str, default=",".join(KIBANA_URLS), help="Comma-separated list of Kibana URLs to extract data from.")
args = parser.parse_args()
KIBANA_URLS = [url.strip() for url in args.kibana_urls.split(",")]

def copy_to_temp_dir():
    if not os.path.exists(args.source_dir):
        logging.error(f"The specified source directory {args.source_dir} does not exist.")
        logging.info("Please specify the correct Chrome LevelDB directory using --source-dir argument.")
        exit(1)

    if os.path.exists(args.temp_dir):
        user_input = input(f"Temporary directory {args.temp_dir} already exists. Do you want to delete it? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            try:
                shutil.rmtree(args.temp_dir)
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
        shutil.copytree(args.source_dir, args.temp_dir, ignore=shutil.ignore_patterns('LOCK'))
    except Exception as e:
        logging.error(f"Error copying LevelDB to temporary directory: {e}")
        raise

def delete_temp_dir():
    if os.path.exists(args.temp_dir):
        try:
            shutil.rmtree(args.temp_dir)
        except Exception as e:
            logging.error(f"Error deleting temporary directory: {e}")
            raise

def extract_console_data_from_leveldb():
    db = plyvel.DB(args.temp_dir, create_if_missing=False)
    for key, value in db.iterator():
        for origin in KIBANA_URLS:
            if origin in key.decode('utf-8') and "sense:console_local_text-object_" in key.decode('utf-8'):
                try:
                    # Removing the first character which is a non-JSON character.
                    clean_value = value[1:].decode('utf-8')
                    json_data = json.loads(clean_value)
                    text_content = json_data.get('text', '').replace('\\n', '\n').replace('\\r', '\r')
                    yield origin, text_content
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON for key {key}. Raw value: {value}")
    db.close()

def main():
    copy_to_temp_dir()
    data_found = False  # flag to check if any KIBANA_URL was found
    for origin, text_content in extract_console_data_from_leveldb():
        data_found = True  # set the flag to True when data is found
        if not args.quiet:
          logging.info(f"Kibana: \"{origin}\"")

        if args.save_folder:
            if not os.path.exists(args.save_folder):
                os.makedirs(args.save_folder)
            file_name = f"{args.prefix}{origin.replace('https://', '').replace('/', '_')}.console"
            full_path = os.path.join(args.save_folder, file_name)
            with open(full_path, 'w') as f:
                f.write(text_content)
            if not args.quiet:
                logging.info(f"Saving {origin} to {full_path}...")
        else:
            print(text_content)
    delete_temp_dir()

    if not data_found:  # if no relevant data was found
        logging.warning(f"No data found for the provided Kibana URLs: {', '.join(KIBANA_URLS)}")

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
            delete_temp_dir()
    else:
        main()

