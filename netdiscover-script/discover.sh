import sys
import os
import subprocess
import re
import argparse

# --- Configuration ---
OUTPUT_FILE = "discovered_ips.txt"

def check_root():
    """Exit if the script is not run as root."""
    if os.geteuid() != 0:
        print("This script requires root privileges. Please run with sudo.")
        print(f"Example: sudo python3 {sys.argv[0]} -i eth0")
        sys.exit(1)

def load_existing_ips(filename):
    """Load IPs from the file into a set to prevent duplicates."""
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r') as f:
        # Use a set for efficient checking of existing IPs
        return {line.strip() for line in f if line.strip()}

def main(interface):
    """
    Runs netdiscover and appends new IPs to the output file.
    """
    check_root()

    print(f"Starting discovery on interface: {interface}")
    print(f"Appending new IPs to: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop.")

    # A regular expression to match an IP address at the start of a line
    ip_pattern = re.compile(r"^\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")

    # Load IPs that are already in the file
    discovered_ips = load_existing_ips(OUTPUT_FILE)
    print(f"Loaded {len(discovered_ips)} existing IPs from {OUTPUT_FILE}.")

    # Command to run. -P makes the output parseable.
    command = ["netdiscover", "-i", interface, "-P"]

    try:
        # Open the output file in append mode
        with open(OUTPUT_FILE, 'a') as f:
            # Start the netdiscover process
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read output line by line in real-time
            for line in iter(process.stdout.readline, ''):
                match = ip_pattern.match(line)
                if match:
                    ip = match.group(1)
                    # If the IP is new, print it and save it
                    if ip not in discovered_ips:
                        print(f"New IP found: {ip}")
                        f.write(ip + '\n')
                        f.flush()  # Immediately write to disk
                        discovered_ips.add(ip)

            # Check for errors after the process finishes
            stderr_output = process.stderr.read()
            if stderr_output:
                print("\n--- Errors ---", file=sys.stderr)
                print(stderr_output, file=sys.stderr)

    except FileNotFoundError:
        print("Error: 'netdiscover' command not found.", file=sys.stderr)
        print("Please make sure netdiscover is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDiscovery stopped by user. Exiting.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # Ensure the process is terminated on exit
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()
        print("Discovery finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run netdiscover to find IPs and save them to a file.",
        epilog=f"Example: sudo python3 {sys.argv[0]} -i eth0"
    )
    parser.add_argument("-i", "--interface", required=True, help="Network interface to scan (e.g., eth0, wlan0).")
    args = parser.parse_args()
    
    main(args.interface)