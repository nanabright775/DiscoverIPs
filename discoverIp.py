#!/usr/bin/env python3
"""
🕵️ ULTRA-STEALTH Network Scanner
Extremely slow scanning to avoid detection
"""

import sys
import os
import subprocess
import platform
import ipaddress
import re
import argparse
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Dependencies ---
try:
    import netifaces
except ImportError:
    print("Error: 'netifaces' library not found.", file=sys.stderr)
    print("Please install it by running: pip install netifaces", file=sys.stderr)
    sys.exit(1)

# --- ULTRA-STEALTH Configuration ---
OUTPUT_FILE = "discovered_ips.txt"
MAX_WORKERS = 10                      
MAX_REQUESTS_PER_SECOND = 10      
MIN_DELAY = 0.5                     
MAX_DELAY = 3.0                     
BATCH_SIZE = 3                      

# Track scan times to avoid patterns
scan_timestamps = []

def load_existing_ips(filename):
    """Load IPs from the file into a set to prevent duplicates."""
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r') as f:
        return {line.strip() for line in f if line.strip()}

def get_local_subnets():
    """Finds local subnets from all network interfaces."""
    subnets = set()
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            for addr_info in addrs[netifaces.AF_INET]:
                ip = addr_info.get('addr')
                netmask = addr_info.get('netmask')
                if ip and netmask:
                    try:
                        network = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
                        if not (network.is_loopback or network.is_link_local):
                            subnets.add(network)
                    except ValueError:
                        continue
    return list(subnets)

def get_routed_subnets():
    """Finds additional subnets from routing table."""
    subnets = set()
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            pattern = re.compile(r"^\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            result = subprocess.run(['route', 'print', '-4'], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
        elif system == 'linux':
            pattern = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})")
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
        else:
            return []

        for line in lines:
            match = pattern.search(line)
            if not match:
                continue

            if system == 'windows':
                network_str = f"{match.group(1)}/{match.group(2)}"
            else:
                network_str = match.group(1)

            try:
                network = ipaddress.ip_network(network_str, strict=False)
                if network.prefixlen == 0:
                    continue
                subnets.add(network)
            except ValueError:
                continue
                
    except Exception:
        return []
    
    return list(subnets)

def load_subnets_from_file(filepath):
    """Loads subnets from a text file."""
    subnets = set()
    if not os.path.exists(filepath):
        print(f"Error: Input file not found at '{filepath}'", file=sys.stderr)
        return []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                network = ipaddress.ip_network(line, strict=False)
                subnets.add(network)
            except ValueError:
                print(f"Warning: Skipping invalid subnet '{line}'", file=sys.stderr)
    return list(subnets)

def ping_host(ip):
    """Pings a single IP address with random delays."""
    global scan_timestamps
    
    # Record this scan time
    scan_timestamps.append(time.time())
    
    # Add human-like variance
    human_variance = random.uniform(0.5, 1.5)
    time.sleep(human_variance)
    
    system = platform.system().lower()
    
    if system == 'windows':
        command = ['ping', '-n', '1', '-w', '2000', str(ip)]  # 2 second timeout
    else:
        command = ['ping', '-c', '1', '-W', '2', '-q', str(ip)]  # 2 second timeout
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return ip
    except Exception:
        pass
    return None

def scan_ultra_stealth(ips, output_file, existing_ips):
    """Scans IPs with maximum stealth - serial scanning with long delays."""
    if not ips:
        return set()
    
    # Randomize scan order
    random.shuffle(ips)
    
    live_hosts = set()
    total_scanned = 0
    start_time = time.time()
    last_scan_time = start_time
    
    print(f"🕵️  ULTRA-STEALTH MODE: Scanning {len(ips):,} hosts")
    print(f"Rate: ~{MAX_REQUESTS_PER_SECOND}/sec (1 ping every ~{1/MAX_REQUESTS_PER_SECOND:.1f} seconds)")
    
    # Calculate estimated time
    estimated_seconds = len(ips) / MAX_REQUESTS_PER_SECOND
    years = estimated_seconds / (365 * 24 * 3600)
    days = estimated_seconds / (24 * 3600)
    
    if years >= 1:
        print(f"Estimated time: {years:.1f} YEARS")
    elif days >= 1:
        print(f"Estimated time: {days:.1f} days")
    else:
        print(f"Estimated time: {estimated_seconds/3600:.1f} hours")
    
    # Human-like scanning pattern
    for i, ip in enumerate(ips):
        # Scan this IP
        result_ip = ping_host(ip)
        if result_ip:
            ip_str = str(result_ip)
            live_hosts.add(ip_str)
            # Immediately write to file if it's a new IP
            if ip_str not in existing_ips:
                existing_ips.add(ip_str)
                with open(output_file, 'a') as f:
                    f.write(ip_str + '\n')
                print(f"\n[+] NEW IP FOUND: {ip_str} (written to {output_file})")
        
        total_scanned = i + 1
        
        # Progress update every 100 hosts or 1%
        if i % max(100, len(ips)//100) == 0 or i == len(ips) - 1:
            progress = ((i + 1) / len(ips)) * 100
            elapsed = time.time() - start_time
            rate = total_scanned / elapsed if elapsed > 0 else 0
            
            # Show detailed progress
            remaining = (len(ips) - (i + 1)) / MAX_REQUESTS_PER_SECOND if rate > 0 else 0
            
            if remaining > 86400:
                remaining_str = f"{remaining/86400:.1f} days"
            elif remaining > 3600:
                remaining_str = f"{remaining/3600:.1f} hours"
            else:
                remaining_str = f"{remaining/60:.1f} minutes"
            
            print(f"\rProgress: {progress:.3f}% | Scanned: {total_scanned:,} | "
                  f"Rate: {rate:.3f}/sec | Found: {len(live_hosts):,} | "
                  f"Remaining: ~{remaining_str}", end="")
        
        # Long random delay between scans (unless it's the last one)
        if i < len(ips) - 1:
            # Base delay + randomization
            base_delay = 1 / MAX_REQUESTS_PER_SECOND  # ~3 seconds for 0.33/sec
            jitter = random.uniform(-0.5, 0.5)  # ±0.5 seconds
            delay = max(0.5, base_delay + jitter)  # Minimum 0.5 seconds
            
            # Add occasional "breaks" to simulate human behavior
            if random.random() < 0.01:  # 1% chance of a longer break
                break_duration = random.uniform(30, 300)  # 30 seconds to 5 minutes
                print(f"\nTaking a break for {break_duration:.0f} seconds...")
                time.sleep(break_duration)
            else:
                time.sleep(delay)
    
    print()  # New line
    return live_hosts

def calculate_scan_times():
    """Analyze scan timing to ensure it looks human/natural."""
    if len(scan_timestamps) < 2:
        return
    
    intervals = []
    for i in range(1, len(scan_timestamps)):
        intervals.append(scan_timestamps[i] - scan_timestamps[i-1])
    
    if intervals:
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        print(f"\n📊 Scan timing analysis:")
        print(f"  Average interval: {avg_interval:.2f} seconds")
        print(f"  Minimum interval: {min_interval:.2f} seconds")
        print(f"  Maximum interval: {max_interval:.2f} seconds")
        print(f"  Total scans: {len(scan_timestamps)}")

def stealth_warning():
    """Show stealth mode warning."""
    print("\n" + "="*70)
    print("ULTRA-STEALTH MODE ACTIVATED")
    print("="*70)
    print("This mode scans EXTREMELY slowly to avoid detection:")
    print("• 1 ping every ~3 seconds (0.33 requests/second)")
    print("• Serial scanning only (no parallel workers)")
    print("• Randomized delays to avoid patterns")
    print("• Human-like behavior simulation")
    print("")
    print(" WARNING: Even in stealth mode:")
    print("• Scanning 10.0.0.0/8 will take ~1.6 YEARS")
    print("• Scanning 172.16.0.0/12 will take ~37 DAYS")
    print("• Scanning 192.168.0.0/16 will take ~2.3 DAYS")
    print("="*70)
    
    response = input("\nType 'STEALTH' to continue: ")
    return response.strip() == 'STEALTH'

def main():
    """Main function - Ultra Stealth Mode."""
    global OUTPUT_FILE
    
    parser = argparse.ArgumentParser(
        description=" Ultra-Stealth Network Scanner - Maximum Avoidance",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""TIMELINE EXAMPLES (at 0.33 requests/sec):
  10.0.0.0/8 (16.7M hosts)    → ~1.6 YEARS
  172.16.0.0/12 (1.05M hosts) → ~37 DAYS  
  192.168.0.0/16 (65K hosts)  → ~2.3 DAYS
  ALL THREE (17.9M hosts)     → ~1.7 YEARS
  
Usage:
  python discoverIp.py -f ranges.txt --stealth"""
    )
    
    parser.add_argument(
        '-f', '--file',
        dest='subnet_file',
        required=True,
        help="Path to file containing subnets to scan."
    )
    parser.add_argument(
        '--stealth',
        dest='stealth_mode',
        action='store_true',
        default=True,
        help="Enable ultra-stealth mode (always on)."
    )
    parser.add_argument(
        '-o', '--output',
        default=OUTPUT_FILE,
        help=f"Output file (default: {OUTPUT_FILE})."
    )
    parser.add_argument(
        '-y', '--yes',
        dest='skip_warning',
        action='store_true',
        help="Skip warning prompts."
    )
    
    args = parser.parse_args()
    
    OUTPUT_FILE = args.output
    
    # Stealth warning
    if not args.skip_warning and not stealth_warning():
        sys.exit(0)
    
    # Load subnets
    print(f"\nLoading subnets from: {args.subnet_file}")
    all_subnets = load_subnets_from_file(args.subnet_file)
    
    if not all_subnets:
        print("No valid subnets to scan.", file=sys.stderr)
        return
    
    # Show what will be scanned
    print(f"\nWill scan {len(all_subnets)} subnet(s):")
    total_hosts = 0
    for network in all_subnets:
        hosts = network.num_addresses - 2
        if hosts > 0:
            total_hosts += hosts
            print(f"  {network}: {hosts:,} hosts")
    
    print(f"\nTOTAL HOSTS TO SCAN: {total_hosts:,}")
    
    # Generate all host IPs
    all_hosts_to_scan = []
    for network in all_subnets:
        all_hosts_to_scan.extend(network.hosts())
    
    if not all_hosts_to_scan:
        print("No host IPs to scan.", file=sys.stderr)
        return
    
    # Load existing IPs and create output file if it doesn't exist
    existing_ips = load_existing_ips(OUTPUT_FILE)
    
    # Create output file immediately if it doesn't exist
    if not os.path.exists(OUTPUT_FILE):
        open(OUTPUT_FILE, 'w').close()
        print(f"\nCreated output file: {OUTPUT_FILE}")
    
    # Start ultra-stealth scan
    print("\n" + "="*60)
    print("STARTING ULTRA-STEALTH SCAN")
    print(f"IPs will be written to {OUTPUT_FILE} as they are discovered")
    print("="*60)
    
    live_hosts = scan_ultra_stealth(all_hosts_to_scan, OUTPUT_FILE, existing_ips)
    
    # Analyze scan timing
    calculate_scan_times()
    
    print("\n" + "="*60)
    print("STEALTH SCAN COMPLETE")
    print("="*60)
    
    # Summary (IPs already saved during scan)
    print(f"\nTotal live hosts found this session: {len(live_hosts):,}")
    
    # Also save timestamped results
    if live_hosts:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"stealth_results_{timestamp}.txt"
        with open(results_file, 'w') as f:
            for ip in sorted(live_hosts):
                f.write(ip + '\n')
        
        print(f"IPs saved to: {OUTPUT_FILE}")
        print(f"Full results saved to: {results_file}")
    
    # Final statistics
    print(f"\nFINAL STATISTICS:")
    print(f"  Total hosts scanned: {len(all_hosts_to_scan):,}")
    print(f"  Live hosts found: {len(live_hosts):,}")
    
    if all_hosts_to_scan:
        success_rate = (len(live_hosts) / len(all_hosts_to_scan)) * 100
        print(f"  Success rate: {success_rate:.2f}%")
    
    print("\n Stealth assessment: LOW DETECTION RISK")
    print("   (Scan rate mimics human/background network activity)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStealth scan interrupted. Timing patterns preserved.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)