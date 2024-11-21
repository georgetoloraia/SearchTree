import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def run_keyhunt_rmd160(target_hash160, range_start, range_end, threads=4):
    """
    Runs KeyHunt in rmd160 mode for a specified range.
    """
    command = [
        "./keyhunt", 
        "-m", "rmd160",
        "-f", target_hash160,
        "-s", hex(range_start),
        "-e", hex(range_end),
        "-t", str(threads)
    ]
    
    logging.info(f"Running KeyHunt for range [{hex(range_start)}, {hex(range_end)}].")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"KeyHunt failed: {e.stderr}")
        return None

# Example usage
if __name__ == "__main__":
    target_hash160 = "739437bb3dd6d1983e66629c5f08c70e52769371"
    range_start = 73786976294838206464
    range_end = 73786976294838206464 + 1000000
    threads = 8

    output = run_keyhunt_rmd160(target_hash160, range_start, range_end, threads)
    if output:
        logging.info(f"KeyHunt output:\n{output}")
        if "FOUND" in output:
            logging.info("Private key found!")
