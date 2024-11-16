import os
import pickle
import hashlib
import json


class TreeNode:
    def __init__(self, min_key, max_key):
        self.min_key = min_key
        self.max_key = max_key
        self.left = None  # Can be a TreeNode or filename
        self.right = None  # Can be a TreeNode or filename
        self.file_stored = False  # To track if the node is offloaded to disk

    def save_to_file(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f)
        self.file_stored = True
        self.left = None
        self.right = None

    @staticmethod
    def load_from_file(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)

    def delete_file(self, filename):
        if os.path.exists(filename):
            os.remove(filename)


# Function to save progress to a file
def save_progress(min_key, max_key):
    progress = {'min_key': min_key, 'max_key': max_key}
    with open('progress.json', 'w') as file:
        json.dump(progress, file)

# Function to load progress from a file
def load_progress():
    try:
        with open('progress.json', 'r') as file:
            progress = json.load(file)
            return progress['min_key'], progress['max_key']
    except FileNotFoundError:
        return 73786976294838206464, 147573952589676412927  # Default range if no progress file exists


def private_key_to_hash160(private_key):
    pk = private_key.to_bytes(32, byteorder="big")
    prefix = b"\x02" if private_key % 2 == 0 else b"\x03"
    compressed_pubkey = prefix + pk[:32]
    sha256 = hashlib.sha256(compressed_pubkey).digest()
    ripemd160 = hashlib.new("ripemd160", sha256).digest()
    return ripemd160.hex()


def build_tree_with_files(min_key, max_key, depth=0, max_depth=4):
    if min_key > max_key:
        return None

    root = TreeNode(min_key, max_key)
    mid_key = (min_key + max_key) // 2

    # Limit in-memory depth to reduce memory usage
    if depth < max_depth:
        root.left = build_tree_with_files(min_key, mid_key - 1, depth + 1, max_depth)
        root.right = build_tree_with_files(mid_key + 1, max_key, depth + 1, max_depth)
    else:
        # Save subtrees to files
        left_file = f"tree_left_{min_key}_{mid_key - 1}.pkl"
        right_file = f"tree_right_{mid_key + 1}_{max_key}.pkl"
        root.left = left_file
        root.right = right_file
        TreeNode(min_key, mid_key - 1).save_to_file(left_file)
        TreeNode(mid_key + 1, max_key).save_to_file(right_file)

    return root


def search_tree_with_files(root, target_hash160):
    if root is None:
        return None

    if isinstance(root, str):  # Load node from file if needed
        root = TreeNode.load_from_file(root)

    mid_key = (root.min_key + root.max_key) // 2
    try:
        hash160 = private_key_to_hash160(mid_key)
        print(f"Checking key {mid_key}: {hash160}")  # Debug output
        if hash160 == target_hash160:
            return mid_key  # Found the key!
    except Exception as e:
        print(f"Error processing key {mid_key}: {e}")
        return None

    # Search left subtree
    if isinstance(root.left, str):
        left_file = root.left
        found = search_tree_with_files(TreeNode.load_from_file(left_file), target_hash160)
        if found is not None:
            return found
        os.remove(left_file)  # Delete file after use
    else:
        found = search_tree_with_files(root.left, target_hash160)
        if found is not None:
            return found

    # Search right subtree
    if isinstance(root.right, str):
        right_file = root.right
        found = search_tree_with_files(TreeNode.load_from_file(right_file), target_hash160)
        if found is not None:
            return found
        os.remove(right_file)  # Delete file after use
    else:
        found = search_tree_with_files(root.right, target_hash160)
        if found is not None:
            return found

    return None


def search_in_expanding_range(target_hash160, initial_min_key, initial_max_key, step_size):
    min_key = initial_min_key
    max_key = initial_max_key
    found = False

    while not found:
        print(f"Searching in range: {min_key} to {max_key}")
        
        # Search in the current range
        found = search_tree_with_files(build_tree_with_files(min_key, max_key), target_hash160)
        
        if not found:
            print(f"Expanding search range by {step_size}")
            min_key += step_size
            max_key += step_size  # Expand both ends of the range
            save_progress(min_key, max_key)  # Save progress


if __name__ == "__main__":
    # Load the progress from file and start the search
    min_key, max_key = load_progress()

    # Set the initial range and step size
    initial_min_key = min_key
    initial_max_key = max_key
    step_size = 10000000000000000000  # Example step size (you can adjust this)

    # The target hash160 you're searching for (replace with your actual value)
    target_hash160 = "739437bb3dd6d1983e66629c5f08c70e52769371"  # Example hash160

    # Start the expanding search
    search_in_expanding_range(target_hash160, initial_min_key, initial_max_key, step_size)
