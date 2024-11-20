# import os
import logging
# import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
from main1 import private_key_to_hash160
import random

# Constants
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
TARGET_HASH160 = "739437bb3dd6d1983e66629c5f08c70e52769371"
TARGET_PREFIX = TARGET_HASH160[:4]  # First few bytes of the target hash
INITIAL_SAMPLES = 1000
GROWTH_FACTOR = 2
MAX_SAMPLES = 100000
NUM_THREADS = 8  # Number of threads for parallel processing

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")



# Generate random keys using numpy for efficiency
# def generate_random_keys(min_key, max_key, num_keys):
#     return np.random.randint(min_key, max_key + 1, size=num_keys, dtype=np.uint64)

# Generate random keys using Python's `random` module to avoid NumPy's uint64 limitation
def generate_random_keys(min_key, max_key, num_keys):
    return [random.randint(min_key, max_key) for _ in range(num_keys)]



# Check a batch of keys for matches with the target prefix
def check_keys_for_prefix(keys, target_prefix):
    promising_keys = []
    for key in keys:
        hash160 = private_key_to_hash160(key)
        if hash160.startswith(target_prefix):
            promising_keys.append((key, hash160))
    return promising_keys


# Adaptive sampling with fast random generation and prefix matching
def adaptive_sampling(min_key, max_key, target_prefix, initial_samples, growth_factor, max_samples):
    current_samples = initial_samples

    while current_samples <= max_samples:
        logging.info(f"Sampling {current_samples} keys in range [{min_key}, {max_key}].")

        # Generate a batch of random keys
        sampled_keys = generate_random_keys(min_key, max_key, current_samples)

        # Check for matches with the target prefix
        promising_keys = check_keys_for_prefix(sampled_keys, target_prefix)

        if promising_keys:
            logging.info(f"Found {len(promising_keys)} promising keys. Expanding search.")
            return promising_keys
        else:
            logging.info("No matches found, increasing sample size.")
            current_samples *= growth_factor

    return []


# Parallel verification of promising keys
def verify_keys_parallel(promising_keys, target_hash160, num_threads):
    def verify_key_pair(key_pair):
        key, hash160 = key_pair
        if hash160 == target_hash160:
            return key
        return None

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = executor.map(verify_key_pair, promising_keys)

    for result in results:
        if result is not None:
            logging.info(f"Found matching private key: {result}")
            return result
    return None


# Persistent search loop
def find_private_key_persistent(min_key, max_key, target_hash160, target_prefix, initial_samples, growth_factor, max_samples, num_threads):
    attempt = 0

    while True:
        attempt += 1
        logging.info(f"Attempt {attempt}: Starting adaptive sampling...")

        promising_keys = adaptive_sampling(min_key, max_key, target_prefix, initial_samples, growth_factor, max_samples)

        if promising_keys:
            logging.info(f"Verifying promising keys...")
            matching_key = verify_keys_parallel(promising_keys, target_hash160, num_threads)
            if matching_key:
                logging.info(f"Private key found: {matching_key}")
                return matching_key
        else:
            logging.info("No promising keys found. Retrying adaptive sampling...")

        # Dynamic adjustment: Increase the range slightly to avoid repetition
        time.sleep(1)  # Avoid CPU overheating
        logging.info("Retrying with refreshed key sampling...")

        # Optional: Adjust sample sizes dynamically
        if initial_samples < max_samples // 2:
            initial_samples *= 2  # Increase sampling size for subsequent attempts


# Run the program
if __name__ == "__main__":
    private_key = find_private_key_persistent(
        MIN_KEY, MAX_KEY, TARGET_HASH160, TARGET_PREFIX,
        INITIAL_SAMPLES, GROWTH_FACTOR, MAX_SAMPLES, NUM_THREADS
    )

    if private_key:
        logging.info(f"Private key successfully found: {private_key}")
    else:
        logging.info("Failed to find the private key.")
