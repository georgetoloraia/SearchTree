import logging
import random
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
from main1 import private_key_to_hash160

# Constants
TARGET_HASH160 = "739437bb3dd6d1983e66629c5f08c70e52769371"
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
PREFIX_LENGTH = 3  # Number of bytes to match in prefix
INITIAL_SAMPLES = 1000
GROWTH_FACTOR = 2
MAX_SAMPLES = 512000
NUM_THREADS = 8  # Number of parallel threads to use
MATCH_THRESHOLD = 12  # Minimum matching indices to save range
PREFIX_FILE = "prefixes.txt"  # File to store promising key ranges

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Generate random keys using Python's `random` module
def generate_random_keys(min_key, max_key, num_keys):
    return [random.randint(min_key, max_key) for _ in range(num_keys)]


# Check how many indices match between two hash160 values
def count_matching_indices(hash1, hash2):
    return sum(1 for a, b in zip(hash1, hash2) if a == b)

# Check if a key's hash160 matches the target's prefix
def matches_prefix(key, target_prefix):
    hash160 = private_key_to_hash160(key)
    return hash160.startswith(target_prefix), hash160

# Save promising ranges to a file
def save_prefix_range(file_path, key_range):
    with open(file_path, "a") as f:
        f.write(f"{key_range}\n")
    logging.info(f"Saved promising key range: {key_range}")

# Parallel prefix matching with index matching logic
def parallel_matches_prefix(keys, target_prefix, target_hash160, num_threads):
    promising_keys = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(matches_prefix, key, target_prefix): key for key in keys}
        for future in as_completed(futures):
            key = futures[future]
            is_prefix_match, hash160 = future.result()
            if is_prefix_match:
                match_count = count_matching_indices(hash160, target_hash160)
                if match_count > MATCH_THRESHOLD:
                    promising_keys.append(key)
                    save_prefix_range(PREFIX_FILE, (key, hash160))
    return promising_keys

# Adaptive sampling with parallelized prefix matching
def adaptive_sampling(min_key, max_key, target_prefix, target_hash160, initial_samples, growth_factor, max_samples, num_threads):
    current_samples = initial_samples
    while current_samples <= max_samples:
        logging.info(f"Sampling {current_samples} keys in range [{min_key}, {max_key}].")
        sampled_keys = generate_random_keys(min_key, max_key, current_samples)
        promising_keys = parallel_matches_prefix(sampled_keys, target_prefix, target_hash160, num_threads)

        if promising_keys:
            logging.info(f"Found promising keys: {promising_keys}")
            return promising_keys

        logging.info("No matches found, doubling sample size.")
        current_samples *= growth_factor

    logging.info("No promising keys found during adaptive sampling.")
    return []

# Verify if the full hash160 matches the target
def verify_full_match(promising_keys, target_hash160):
    for key in promising_keys:
        hash160 = private_key_to_hash160(key)
        if hash160 == target_hash160:
            logging.info(f"Found private key: {key}")
            return key
    return None

# Continuously search for the private key
def find_private_key(target_hash160, min_key, max_key, initial_samples, growth_factor, max_samples, num_threads):
    target_prefix = target_hash160[:PREFIX_LENGTH * 2]  # Prefix in hex
    attempt = 1

    while True:
        logging.info(f"Attempt {attempt}: Starting adaptive sampling...")
        promising_keys = adaptive_sampling(min_key, max_key, target_prefix, target_hash160, initial_samples, growth_factor, max_samples, num_threads)

        if promising_keys:
            logging.info(f"Verifying promising keys against full hash160: {promising_keys}")
            private_key = verify_full_match(promising_keys, target_hash160)
            if private_key:
                return private_key
            else:
                logging.info("Promising keys did not match the full target hash160.")

        logging.info(f"Attempt {attempt}: No matches found. Continuing search...")
        attempt += 1

# Execution
if __name__ == "__main__":
    private_key = find_private_key(
        TARGET_HASH160, 
        MIN_KEY, 
        MAX_KEY, 
        INITIAL_SAMPLES, 
        GROWTH_FACTOR, 
        MAX_SAMPLES, 
        NUM_THREADS
    )
    if private_key:
        logging.info(f"Success! Private key found: {private_key}")
    else:
        logging.info("Private key not found.")
