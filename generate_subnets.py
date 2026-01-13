import ipaddress

OUTPUT_FILENAME = "subnets_to_scan.txt"

def generate_subnets():
    """
    Generates a list of all possible /24 subnets within RFC 1918 private ranges.
    """
    all_subnets = []

    # 1. Range 10.0.0.0/8
    # This creates subnets like 10.0.0.0/24, 10.0.1.0/24, ..., 10.255.255.0/24
    print("Generating subnets for 10.0.0.0/8...")
    network_10 = ipaddress.ip_network('10.0.0.0/8')
    all_subnets.extend(network_10.subnets(new_prefix=24))

    # 2. Range 172.16.0.0/12
    # This creates subnets like 172.16.0.0/24, ..., 172.31.255.0/24
    print("Generating subnets for 172.16.0.0/12...")
    network_172 = ipaddress.ip_network('172.16.0.0/12')
    all_subnets.extend(network_172.subnets(new_prefix=24))

    # 3. Range 192.168.0.0/16
    # This creates subnets like 192.168.0.0/24, ..., 192.168.255.0/24
    print("Generating subnets for 192.168.0.0/16...")
    network_192 = ipaddress.ip_network('192.168.0.0/16')
    all_subnets.extend(network_192.subnets(new_prefix=24))

    # Write all subnets to the output file
    print(f"\nWriting {len(all_subnets)} subnets to {OUTPUT_FILENAME}...")
    with open(OUTPUT_FILENAME, 'w') as f:
        for subnet in all_subnets:
            f.write(str(subnet) + '\n')
    
    print("Done.")

if __name__ == "__main__":
    generate_subnets()