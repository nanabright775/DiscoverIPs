import json
import re

def extract_ips_from_json(input_file, output_file):
    """Extract IP addresses from JSON file and save to output file."""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    ips = []
    for bucket in data.get('buckets', []):
        ip = bucket.get('key', '')
        # Validate it's an IP address
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            ips.append(ip)
    
    # Write IPs to output file
    with open(output_file, 'w') as f:
        f.write('\n'.join(ips))
    
    print(f"Extracted {len(ips)} IP addresses to {output_file}")

if __name__ == "__main__":
    extract_ips_from_json('host.txt', 'ips.txt')
