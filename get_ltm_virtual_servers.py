#!/usr/bin/python3
""" This Script is Getting the Virtual Servers of LTM F5 Device Information
Input Parameters:
    Hostname or IP
Input Example:
    python get_ltm_virtual_servers.py --hostname {$device_ip}
Output:
    Example:
        [
            {"device_ip": "10.10.0.2", "name": "VS_80", "ip": "192.168.2.1", "port": "80", "pool_name": "Pool_80"},
            {"device_ip": "10.10.0.2", "name": "VS_443", "ip": "192.168.2.3", "port": "443", "pool_name": "Pool_80"},
            {"device_ip": "10.10.0.2", "name": "Header_test", "ip": "192.168.2.5", "port": "443", "pool_name": "l_http_pool"},
            {"device_ip": "10.10.0.2", "name": "Subdomain_VS_80", "ip": "192.168.25.2", "port": "80", "pool_name": "Pool_8080"}
        ]

Important Note:
    - To connect you need to use non root user.
    - Use it with your own risk.
"""

import sys
import json
import getpass
import optparse
from f5.bigip import ManagementRoot

class LtmVirtualServerModel:
    """ This Model for LTM Virtual Server in F5 Devices """
    def __init__(self, device_ip, name, ip, port, pool_name='', status='', status_reason='', sub_path=''):
        self.device_ip = device_ip
        self.name = name
        self.ip = ip
        self.port = port
        self.pool_name = pool_name
        self.status = status
        self.status_reason = status_reason
        self.sub_path = sub_path

def obj_dict(obj):
    """
    Used to convert list of model to json
    """
    return obj.__dict__

def credential():
    #User name capture
    user = input('Enter Username: ')
    # start infinite loop
    while True:
        # Capture password without echoing 
        pwd1 = getpass.getpass('%s, enter your password: ' % user)
        pwd2 = getpass.getpass('%s, re-Enter Password: ' % user)
        # Compare the two entered password to avoid typo error
        if pwd1 == pwd2:
            # break infinite loop by returning value
            return user, pwd1

def get_ltm_virtual_servers_include_pool_name(hostname, username, password):
    """ This function get the virtual servers and pools from F5 Device """
    try:
        # create empty virtual server list
        vs_list = []

        # connect to F5 device
        mgmt = ManagementRoot(hostname, username, password)
        ltm = mgmt.tm.ltm

        # get virtual servers list from F5
        virtuals = ltm.virtuals.get_collection()

        # extract virtual server name, destination ip, port, subpath and pool from the virtual servers
        for virtual in virtuals:
            dest_str = str(virtual.destination)
            dest_str = dest_str.split("/")
            vs_obj_item = LtmVirtualServerModel(
                device_ip=hostname,
                name=str(virtual.name),
                ip=dest_str[2].split(":")[0],
                port=dest_str[2].split(":")[1]
            )
            if hasattr(virtual, 'subPath'):
                vs_obj_item.sub_path = virtual.subPath
            if hasattr(virtual, 'pool'):
                vs_obj_item.pool_name = virtual.pool.split('/')[2]

            # add the virtual server model to virtual server list
            vs_list.append(vs_obj_item)

        # sort the extracted virtual servers by name
        sorted_vs = sorted(vs_list, key = lambda i: i.name)

        # get the virtual server status and add it to existed virtual server list
        for vs in sorted_vs:
            # check if the virtual server is under sub_path or direct under common partition
            if vs.sub_path != '':
                vip = ltm.virtuals.virtual.load(transform_name=True, name=vs.sub_path + "/" + vs.name , partition="Common")
            else:
                vip = ltm.virtuals.virtual.load(name=vs.name)

            # get virtual server stats
            vipstats = vip.stats.load()
            if vs.sub_path != '':
                state_details = vipstats.entries['https://localhost/mgmt/tm/ltm/virtual/~Common~'+ vs.sub_path +'~'+ vs.name +'/~Common~'+ vs.sub_path +'~'+ vs.name +'/stats']['nestedStats']['entries']
            else:
                state_details = vipstats.entries['https://localhost/mgmt/tm/ltm/virtual/'+ vs.name +'/~Common~'+ vs.name +'/stats']['nestedStats']['entries']
            
            # get virtual server status and the status reason
            if 'status.availabilityState' in state_details:
                vs.status = state_details['status.availabilityState']['description']
            if 'status.statusReason' in state_details:
                vs.status_reason = state_details['status.statusReason']['description']

        # convert the extracted model to json string
        json_string = json.dumps(sorted_vs, default=obj_dict)
        if __name__ == '__main__':
            print(json_string)
        
        # used when calling the script from another python script
        return sorted_vs
        
    except Exception as ex_error:
        print(ex_error)
        exit(1)

if __name__ == '__main__':
    # Define a new argument parser
    parser=optparse.OptionParser()

    # import options
    parser.add_option('--hostname', help='Pass the F5 Big-ip hostname or IP')

    # Parse arguments
    (opts,args) = parser.parse_args()

    # Check if --hostname argument populated or not
    if not opts.hostname:
        print('--hostname argument is required.')
        exit(1)

    username, password = credential()
    get_ltm_virtual_servers_include_pool_name(opts.hostname, username, password)
