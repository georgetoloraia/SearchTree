import os
import random
import psutil
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from main1 import private_key_to_hash160

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("search.log"),
        logging.StreamHandler()
    ]
)

# Constants
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
SEGMENT_SIZE = 12345678
INITIAL_SAMPLES = 100000
GROWTH_FACTOR = 8
MAX_SAMPLES = 1000000
TARGET_PREFIX = "739437"
TARGET_HASH160 = "739437bb3dd6d1983e66629c5f08c70e52769371"  # Replace with your actual target

# # Placeholder for actual hash160 function
# def private_key_to_hash160(private_key):
#     # Simulate hash160 computation
#     return f"{private_key:040x}"[:40]  # Example dummy hash for testing

# Monitoring resources
def monitor_resources():
    """
    Monitor and print current CPU and memory usage.
    """
    memory = psutil.virtual_memory()
    logging.info(f"Memory Usage: {memory.percent}%")
    logging.info(f"CPU Usage: {psutil.cpu_percent()}%")

# Adaptive Sampling
def adaptive_sampling(min_key, max_key, target_prefix, initial_samples=100, growth_factor=2, max_samples=10000):
    """
    Dynamically sample keys from the range without creating large sequences in memory.
    """
    current_samples = initial_samples
    promising_keys = []

    while current_samples <= max_samples:
        logging.info(f"Sampling {current_samples} keys in range [{min_key}, {max_key}].")
        sampled_keys = []
        
        for _ in range(current_samples):
            # Randomly pick a number within the range without creating a huge list
            sampled_keys.append(random.randint(min_key, max_key))
        
        for key in sampled_keys:
            hash160 = private_key_to_hash160(key)
            if hash160.startswith(target_prefix):
                logging.info(f"Prefix match found: Key {key}, Hash160 {hash160}")
                promising_keys.append(key)
        
        if promising_keys:
            logging.info(f"Found {len(promising_keys)} promising keys, increasing sample size.")
            current_samples *= growth_factor
        else:
            logging.info("No matches found, stopping adaptive sampling.")
            break

    return promising_keys


# Segment Refinement
def segment_refinement(min_key, max_key, target_prefix, segment_size, target_hash160=None):
    """
    Split the range into segments and refine each segment without memory overflow.
    """
    logging.info(f"Segmenting range [{min_key}, {max_key}] with segment size {segment_size}.")
    start = min_key

    while start <= max_key:
        end = min(start + segment_size - 1, max_key)
        logging.info(f"Refining segment [{start}, {end}].")
        
        current_key = start
        while current_key <= end:
            hash160 = private_key_to_hash160(current_key)
            if hash160.startswith(target_prefix):
                logging.info(f"Prefix match found: Key {current_key}, Hash160 {hash160}")
                if target_hash160 and hash160 == target_hash160:
                    logging.info(f"Exact match found in segment! Key: {current_key}")
                    return current_key
            current_key += 1
        
        start = end + 1
    return None


# Parallel Refinement
def refine_search(key, target_prefix, target_hash160):
    """
    Check a single key for prefix and exact match.
    """
    hash160 = private_key_to_hash160(key)
    if hash160.startswith(target_prefix):
        logging.info(f"Prefix match found: Key {key}, Hash160 {hash160}")
        if target_hash160 and hash160 == target_hash160:
            logging.info(f"Exact match found! Key: {key}")
            return key
    return None

def async_refinement_with_progress(keys, target_prefix, target_hash160=None):
    """
    Asynchronously refine keys with progress tracking.
    """
    results = []
    chunk_size = 1000  # Process keys in chunks to avoid overloading memory
    with ThreadPoolExecutor() as executor:
        futures = []
        for i in range(0, len(keys), chunk_size):
            chunk = keys[i:i + chunk_size]
            futures.extend(
                executor.submit(refine_search, key, target_prefix, target_hash160) for key in chunk
            )
        
        for future in tqdm(futures, desc="Refining keys"):
            result = future.result()
            if result:
                results.append(result)
                break  # Stop on first match
    return results


# Main Search Process
def search_for_key():
    # Step 1: Adaptive Sampling
    promising_keys = adaptive_sampling(MIN_KEY, MAX_KEY, TARGET_PREFIX, INITIAL_SAMPLES, GROWTH_FACTOR, MAX_SAMPLES)
    
    if not promising_keys:
        logging.info("No promising keys found during adaptive sampling.")
        return

    # Step 2: Parallel Refinement
    logging.info("Starting parallel refinement.")
    results = async_refinement_with_progress(promising_keys, TARGET_PREFIX, TARGET_HASH160)
    
    if results:
        logging.info(f"Search completed. Matching key(s): {results}")
    else:
        logging.info("Search completed. No matching keys found.")

    monitor_resources()

# Run the search
if __name__ == "__main__":
    search_for_key()
