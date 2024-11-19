import random
import hashlib
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from main1 import private_key_to_hash160

# Constants
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
PREFIX = "739437"
STEP_SIZE = 1234567890
SAMPLES = 1000  # Number of random samples for initial search
REFINE_STEP_SIZE = STEP_SIZE // 10  # Range for refinement around promising keys
CHECKPOINT_FILE = "search_checkpoint.pkl"

# Function to compute hash160 (replace with real implementation if needed)
# def private_key_to_hash160(key):
#     return hashlib.sha256(str(key).encode()).hexdigest()[:40]  # Mock hash160

# Save checkpoint to file
def save_checkpoint(checkpoint_data):
    with open(CHECKPOINT_FILE, "wb") as f:
        pickle.dump(checkpoint_data, f)
    print(f"Checkpoint saved to {CHECKPOINT_FILE}.")

# Load checkpoint from file
def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "rb") as f:
            checkpoint_data = pickle.load(f)
        print(f"Checkpoint loaded from {CHECKPOINT_FILE}.")
        return checkpoint_data
    return None

# Random Sampling
def search_with_sampling(target_prefix, min_key, max_key, samples=SAMPLES):
    """
    Perform a random search for keys matching the target prefix.
    """
    print(f"Starting random sampling in range [{min_key}, {max_key}] with {samples} samples.")
    promising_keys = []
    for _ in range(samples):
        key = random.randint(min_key, max_key)
        hash160 = private_key_to_hash160(key)
        
        if hash160.startswith(target_prefix):
            print(f"Prefix match found: Key {key}, Hash160 {hash160}")
            promising_keys.append(key)
    return promising_keys

# Refinement Search
def refine_search(start_key, target_prefix, target_hash160=None, range_size=REFINE_STEP_SIZE):
    """
    Refine the search around a specific key, looking for a closer match.
    """
    print(f"Refining search around key {start_key} with range size {range_size}.")
    for key in range(max(start_key - range_size, MIN_KEY), 
                     min(start_key + range_size, MAX_KEY) + 1):
        hash160 = private_key_to_hash160(key)
        
        if hash160.startswith(target_prefix):
            print(f"Refined match: Key {key}, Hash160 {hash160}")
            if target_hash160 and hash160 == target_hash160:
                print(f"Exact match found! Key: {key}")
                return key
    return None

# Parallel Search
def parallel_refine_search(keys, target_prefix, target_hash160=None, max_workers=4):
    """
    Refine search around multiple keys in parallel.
    """
    print(f"Starting parallel refinement for {len(keys)} promising keys with {max_workers} workers.")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda key: refine_search(key, target_prefix, target_hash160),
            keys
        ))
    return [res for res in results if res]

# Main Function
def main():
    checkpoint = load_checkpoint()

    if checkpoint:
        min_key, max_key, sampled_keys = checkpoint["min_key"], checkpoint["max_key"], checkpoint["sampled_keys"]
        print(f"Resuming search from [{min_key}, {max_key}] with {len(sampled_keys)} sampled keys.")
    else:
        sampled_keys = search_with_sampling(PREFIX, MIN_KEY, MAX_KEY)
        save_checkpoint({"min_key": MIN_KEY, "max_key": MAX_KEY, "sampled_keys": sampled_keys})

    results = parallel_refine_search(sampled_keys, PREFIX, target_hash160="739437bb3dd6d1983e66629c5f08c70e52769371")
    
    if results:
        print(f"Found exact matches: {results}")
    else:
        print("No exact matches found.")

# Execute the script
if __name__ == "__main__":
    main()
