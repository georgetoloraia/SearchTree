import os
import pickle
import logging
from concurrent.futures import ThreadPoolExecutor
from main1 import private_key_to_hash160

# Constants
# MIN_KEY = 73786976294838206464
# MAX_KEY = 147573952589676412927
# STEP_SIZE = 1234567890
FILES_DIR = "key_ranges"

# for example
MIN_KEY = 737731
MAX_KEY = 14752454
STEP_SIZE = 10

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Create a directory for storing files
os.makedirs(FILES_DIR, exist_ok=True)

# Step 1: Save ranges to files
def save_ranges_to_files(min_key, max_key, step_size):
    current_key = min_key
    file_index = 1

    while current_key <= max_key:
        range_end = min(current_key + step_size - 1, max_key)
        file_name = os.path.join(FILES_DIR, f"range_{file_index}.pkl")
        
        # Save range metadata
        with open(file_name, "wb") as f:
            pickle.dump({"range": (current_key, range_end)}, f)
        
        logging.info(f"Saved range {current_key} to {range_end} in {file_name}")
        current_key += step_size
        file_index += 1

    logging.info(f"Saved {file_index - 1} files in {FILES_DIR} directory.")

# Step 2: Process each file
def process_file(file_path, target_hash160, process_function):
    logging.info(f"Processing file: {file_path}")
    with open(file_path, "rb") as f:
        data = pickle.load(f)
        start, end = data["range"]

    # Process the range
    for key in range(start, end + 1):
        if process_function(key, target_hash160):
            logging.info(f"Found matching key: {key}")
            return key

    # Delete file after processing
    os.remove(file_path)
    logging.info(f"Deleted processed file: {file_path}")
    return None

# Parallel processing of files
def process_files_parallel(target_hash160, process_function, max_workers=8):
    file_paths = [os.path.join(FILES_DIR, file) for file in os.listdir(FILES_DIR)]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda path: process_file(path, target_hash160, process_function), file_paths)

    for result in results:
        if result:  # Found the key
            logging.info(f"Found matching key: {result}")
            break
    else:
        logging.info("Search completed, target not found.")

# Example process function
def example_process_function(key, target_hash160):
    # Replace this stub with the actual hash160 computation
    hash160 = private_key_to_hash160(key)  # Implement this function!
    return hash160 == target_hash160

# Main Execution
if __name__ == "__main__":
    # Step 1: Save ranges to files
    save_ranges_to_files(MIN_KEY, MAX_KEY, STEP_SIZE)

    # Step 2: Process files to find the key
    # target_hash = "739437bb3dd6d1983e66629c5f08c70e52769371"

    #for example
    target_hash = "3f08b882e3f892c572a7c90505e2904829f51a7c"
    process_files_parallel(target_hash, example_process_function, max_workers=8)
