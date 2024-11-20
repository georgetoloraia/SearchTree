import logging
import random
from concurrent.futures import ThreadPoolExecutor
from main1 import private_key_to_hash160

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Constants
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
TARGET_HASH160 = "739437bb3dd6d1983e66629c5f08c70e52769371"
TARGET_PREFIX = TARGET_HASH160[:6]  # First 3 bytes (6 hex chars)


# Adaptive Sampling with Prefix Matching
def adaptive_sampling(min_key, max_key, target_prefix, initial_samples=1000, growth_factor=2, max_samples=100000):
    current_samples = initial_samples
    promising_keys = []

    while current_samples <= max_samples:
        logging.info(f"Sampling {current_samples} keys in range [{min_key}, {max_key}].")
        sampled_keys = set()

        for _ in range(current_samples):
            sampled_keys.add(random.randint(min_key, max_key))

        for key in sampled_keys:
            hash160 = private_key_to_hash160(key)
            if hash160.startswith(target_prefix):
                logging.info(f"Prefix match found: Key {key}, Hash160 {hash160}")
                promising_keys.append(key)

        if promising_keys:
            logging.info(f"Found {len(promising_keys)} promising keys. Expanding search.")
            break  # Stop sampling once promising keys are found
        else:
            logging.info("No matches found, increasing sample size.")
            current_samples *= growth_factor

    return promising_keys

# Refining the Search Around Promising Keys
def refine_search(min_key, max_key, promising_keys, target_hash160):
    refined_keys = []
    for key in promising_keys:
        for offset in range(-1000, 1001):  # Narrow search window
            test_key = key + offset
            if min_key <= test_key <= max_key:
                hash160 = private_key_to_hash160(test_key)
                if hash160 == target_hash160:
                    logging.info(f"Exact match found: Key {test_key}, Hash160 {hash160}")
                    return test_key  # Return immediately if found
                elif hash160.startswith(TARGET_PREFIX):
                    refined_keys.append(test_key)
    return None  # No exact match found

# Parallel Sampling for Large Key Ranges
def parallel_sampling(min_key, max_key, target_prefix, workers=4):
    chunk_size = (max_key - min_key) // workers
    ranges = [(min_key + i * chunk_size, min_key + (i + 1) * chunk_size - 1) for i in range(workers)]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(lambda r: adaptive_sampling(r[0], r[1], target_prefix), ranges)
    
    promising_keys = []
    for result in results:
        promising_keys.extend(result)
    return promising_keys

# Main Execution Flow
def main():
    logging.info("Starting adaptive sampling with parallelization...")
    promising_keys = parallel_sampling(MIN_KEY, MAX_KEY, TARGET_PREFIX, workers=4)

    if not promising_keys:
        logging.info("No promising keys found during adaptive sampling.")
        return

    logging.info(f"Refining search for {len(promising_keys)} promising keys.")
    match = refine_search(MIN_KEY, MAX_KEY, promising_keys, TARGET_HASH160)

    if match:
        logging.info(f"Exact match found! Private key: {match}")
    else:
        logging.info("No exact match found after refinement.")

# Entry Point
if __name__ == "__main__":
    main()
