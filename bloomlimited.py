import random
import hashlib
from ecdsa import SigningKey, SECP256k1
from bloom_filter import BloomFilter
import math
from concurrent.futures import ThreadPoolExecutor

# Constants
MIN_KEY = 73786976294838206464
MAX_KEY = 147573952589676412927
STEP_SIZE = 1234567890
PREFIX_LENGTH = 4  # Number of bytes to match in the prefix
BLOOM_FILTER_SIZE = 500  # Reduced number of expected elements
FALSE_POSITIVE_RATE = 0.05  # Increased false positive rate
MAX_WORKERS = 8  # Number of threads for parallel processing
TARGET_HASH160 = "739437bb3dd6d1983e66629c5f08c70e52769371"  # Full hash to match

# Function to generate hash160 from a private key
def private_key_to_hash160(private_key):
    pk_bytes = private_key.to_bytes(32, byteorder="big")
    signing_key = SigningKey.from_string(pk_bytes, curve=SECP256k1)
    verifying_key = signing_key.verifying_key
    compressed_pubkey = (b'\x02' if verifying_key.to_string()[-1] % 2 == 0 else b'\x03') + verifying_key.to_string()[:32]
    sha256 = hashlib.sha256(compressed_pubkey).digest()
    ripemd160 = hashlib.new("ripemd160", sha256).digest()
    return ripemd160.hex()

# Create and initialize a Bloom filter
def create_bloom_filter(size, false_positive_rate):
    return BloomFilter(max_elements=size, error_rate=false_positive_rate)

# Selective expansion within a specific range
def selective_expansion(start_key, end_key, target_prefix):
    print(f"Expanding search in range: {start_key} to {end_key}")
    for key in range(start_key, end_key + 1):
        hash160 = private_key_to_hash160(key)
        if hash160.startswith(target_prefix):  # Prefix match
            print(f"Prefix match found: {key} -> {hash160}")
            if hash160 == TARGET_HASH160:  # Exact match
                print(f"Exact match found: {key} -> {hash160}")
                return key
    return None

# Function to process a single range
def process_range(start, end, target_prefix, bloom_filter):
    # Check Bloom filter for this range
    sample_key = random.randint(start, end)
    hash160_prefix = private_key_to_hash160(sample_key)[:len(target_prefix)]

    if hash160_prefix in bloom_filter:
        print(f"Potential match in range {start} to {end} (prefix: {hash160_prefix})")
        # Perform selective expansion if Bloom filter suggests a match
        return selective_expansion(start, end, target_prefix)
    return None

# Parallel processing of ranges
def search_with_parallelization(target_prefix):
    print(f"Target prefix: {target_prefix}")

    # Step 1: Initialize the Bloom filter
    bloom_filter = create_bloom_filter(size=BLOOM_FILTER_SIZE, false_positive_rate=FALSE_POSITIVE_RATE)

    # Step 2: Preload Bloom filter with random samples
    print("Preloading Bloom filter with random samples...")
    for _ in range(BLOOM_FILTER_SIZE):
        random_key = random.randint(MIN_KEY, MAX_KEY)
        hash160_prefix = private_key_to_hash160(random_key)[:len(target_prefix)]
        bloom_filter.add(hash160_prefix)

    # Step 3: Parallel processing of ranges
    print("Starting parallel search...")
    ranges = [(start, min(start + STEP_SIZE - 1, MAX_KEY)) for start in range(MIN_KEY, MAX_KEY, STEP_SIZE)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(lambda r: process_range(r[0], r[1], target_prefix, bloom_filter), ranges)

    # Step 4: Check results for any found keys
    for result in results:
        if result:
            print(f"Found key: {result}")
            return result

    print("No matching key found.")
    return None

# Usage
if __name__ == "__main__":
    target_prefix = TARGET_HASH160[:PREFIX_LENGTH]  # Example target prefix
    found_key = search_with_parallelization(target_prefix)
    if found_key:
        print(f"Found key: {found_key}")
    else:
        print("Target not found.")
