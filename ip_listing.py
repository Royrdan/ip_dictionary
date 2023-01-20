#####################################   DONT RUN UNDER SUDO  ###################################################

import subprocess
import json
import yaml
import sys
import os
import requests


##########################   CONFIG   #########################################
debug = True
command = "sudo /usr/sbin/arp-scan 192.168.30.0/24" # Set command
ip_file_dir = "device_ips.yaml"
errors_file = 'errors.txt'
errors = []

################################################################################

def save_errors_exit():
    with open(errors_file, 'a+') as myfile:
        myfile.write("\n".join(errors))
        sys.exit()

def open_ip_file():
    try:
        with open(ip_file_dir, 'r+') as myfile:
            read_string = myfile.read()
            if len(read_string) == 0:
                return {}
            else:
                return yaml.safe_load(read_string)
    except:
        print("Failed to open ip file")
        errors.append(f"Failed to open {ip_file_dir} for ip_listing.py")
        save_errors_exit()

def get_devices():
    try:
        ip_uncoded_data = subprocess.check_output(command, shell=True, timeout=15) # Run ssh command
        ip_data = ip_uncoded_data.strip().decode('utf-8') # Encode the output
        ip_list = ip_data.split("\n") # Split into list
        ip_dict = {} # Start empty dictionary

        for item in ip_list: # Iterate each ip into the dictionary
            if "192.168.30." not in item: continue
            ip_split = item.split()
            ip_address = ip_split[0]
            mac = ip_split[1].upper()
            ip_dict[mac] = ip_address

        return ip_dict

    except subprocess.CalledProcessError:
        print(f"Command \"{command}\" failed to execute for ip_listing.py")
        errors.append(f"Command \"{command}\" failed to execute for ip_listing.py")
        save_errors_exit()
    except subprocess.TimeoutExpired:
        print(f"Command \"{command}\" timed out for ip_listing.py")
        errors.append(f"Command \"{command}\" timed out for ip_listing.py")
        save_errors_exit()

def write_ip_file(ip_file_write):
    if os.path.isfile(ip_file_dir):
        try:
            with open(ip_file_dir, 'w+') as myfile:
                write_string = yaml.dump(ip_file_write, Dumper=yaml.Dumper, default_flow_style=False)
                myfile.write(write_string)
        except:
            print("Writing ip file failed")
            errors.append(f"Failed to write to {ip_file_dir} for ip_listing.py")
    else:
        print(f"File {ip_file_dir} does not exist for ip_listing.py")
        errors.append(f"File {ip_file_dir} does not exist for ip_listing.py")



ip_file = open_ip_file()
router_dict = get_devices()

#print(json.dumps(router_dict,  sort_keys=True, indent=4)) # Format the dictionary

print(str(len(ip_file)) + " configured devices")
print(str(len(router_dict)) + " connected devices\n")

non_connected_devices = list(ip_file.keys())

for router_mac in router_dict:
    exists = False
    for device in ip_file:
        # Cycle through each item of the unknown devices and remove it if its connected to make up the non connected devices
        if ip_file[device]['mac'] == router_mac:
            #print(router_mac + " matches " + device)
            exists = True
            non_connected_devices.remove(device) # Remove the item as it is connected
            if not router_dict[router_mac] == ip_file[device]['ip']: # If IP doesnt match then change it
                print(f"IP doesnt match for {device}. Changing {ip_file[device]['ip']} to {router_dict[router_mac]}")
                ip_file[device]['ip'] = router_dict[router_mac]
            break
    if not exists:
        print("Couldnt find " + router_mac)
        # Search for MAC company name
        try:
            r = json.loads(requests.get('http://macvendors.co/api/' + router_mac).text)
            mac_company = r['result']['company']
        except:
            mac_company = router_mac.replace(":", "")

        ip_file[mac_company] = {"ip":router_dict[router_mac], "mac":router_mac}

print("Non connected devices:")
for x in non_connected_devices:
    print(f"  {x}")

write_ip_file(ip_file)

save_errors_exit()
