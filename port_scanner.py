import socket
from common_ports import ports_and_services

def get_open_ports(target, port_range, verbose=False):
    open_ports = []
    
    # --- 1. Validate Target and Resolve IP ---
    ip = ""
    is_ip_input = False # Track if the user gave us an IP or a URL

    # Simple check: Does it look like an IP address? (Digits and dots)
    # We try to validate it as an IP first.
    try:
        # inet_aton validates that it is a structurally correct IP string
        socket.inet_aton(target)
        
        # Further check: split by dot and check number ranges (0-255)
        # inet_aton allows some weird formats like "127.1", so manual check helps robustness
        parts = target.split('.')
        if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
            ip = target
            is_ip_input = True
        else:
            raise socket.error # Force it to fail if it looks like IP but numbers are off
    except (socket.error, ValueError):
        # If it failed IP validation, assume it is a Hostname/URL
        # If the input was numeric (like "300.300.300.300"), it failed above.
        # If it contains letters, it fell here immediately.
        
        # If it was meant to be an IP (digits/dots) but failed, return IP error
        if all(c.isdigit() or c == '.' for c in target) and any(c.isdigit() for c in target):
             return "Error: Invalid IP address"
             
        # Otherwise, try to resolve the hostname
        try:
            ip = socket.gethostbyname(target)
        except socket.gaierror:
            return "Error: Invalid hostname"

    # --- 2. Scan Ports ---
    # port_range[1] + 1 ensures the upper limit is included
    for port in range(port_range[0], port_range[1] + 1):
        # Create a socket for IPv4 (AF_INET) using TCP (SOCK_STREAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set a timeout. If too high, tests take forever. If too low, might miss ports.
        s.settimeout(1) 
        
        # connect_ex returns 0 if connection succeeds, otherwise an error code
        if s.connect_ex((ip, port)) == 0:
            open_ports.append(port)
        s.close()

    # --- 3. Return Simple List (if not verbose) ---
    if not verbose:
        return open_ports

    # --- 4. Generate Verbose Output ---
    # We need to determine the hostname for the header
    hostname = ""
    
    if is_ip_input:
        # If input was IP, try to find the domain name (Reverse DNS)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            header = f"Open ports for {hostname} ({ip})"
        except socket.herror:
            # If DNS lookup fails, just print the IP
            header = f"Open ports for {ip}"
    else:
        # If input was a URL, use it directly
        header = f"Open ports for {target} ({ip})"

    # Construct the final string
    # The header for the table requires specific spacing
    output = header + "\nPORT     SERVICE\n"
    
    for port in open_ports:
        # Look up service name, default to empty string or unknown if missing
        service_name = ports_and_services.get(port, "")
        
        # Format: Port is strictly aligned to the left.
        # Based on FCC requirements, the first column width is usually 9 chars.
        output += f"{port:<9}{service_name}\n"

    return output.strip()