#!/usr/bin/python3
""" This Script to get the Pools and Members from LTM F5 device
Input Parameters:
    Hostname or IP
Input Example:
    python get_ltm_pools_and_members.py --hostname {$device_ip}
Output:
    Example:
        [
            {
                "pool_name": "app_pool_80",
                "members": [
                    {
                        "member_name": "10.10.60.69:80",
                        "member_address": "10.10.60.69"
                    },
                    {
                        "member_name": "10.10.60.70:80",
                        "member_address": "10.10.60.70"
                    }
                ]
            },
            {
                "pool_name": "another_Pool",
                "members": [
                    {
                        "member_name": "10.10.65.31:2005",
                        "member_address": "10.10.65.31"
                    }
                ]
            },
            {
                "pool_name": "Connect_Pool_443",
                "members": [
                    {
                        "member_name": "10.10.50.10:443",
                        "member_address": "10.10.50.10"
                    },
                    {
                        "member_name": "10.10.50.11:443",
                        "member_address": "10.10.50.11"
                    },
                    {
                        "member_name": "10.10.50.68:443",
                        "member_address": "10.10.50.68"
                    }
                ]
            }
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

class LtmMemberModel:
    """ This Model for LTM Memeber in F5 Devices """
    def __init__(self, member_name, member_address):
        self.member_name = member_name
        self.member_address = member_address
        
class LtmPoolModel:
    """ This Model for LTM Pool in F5 Devices """
    def __init__(self, pool_name, members=[], status='', status_reason='', sub_path=''):
        self.pool_name = pool_name
        self.members = members
        self.status = status
        self.status_reason = status_reason
        self.sub_path = sub_path

def obj_dict(obj):
    """
    Default DOC
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

def get_members_under_pool(pool):
    # Initialize the member collection
    member_collection = []

    # extract member name and address from the selected pool
    for member in pool.members_s.get_collection():
        single_member = LtmMemberModel(
            member_name=member.name,
            member_address=member.address
        )
        member_collection.append(single_member)
    return member_collection

def get_ltm_pools_and_members(hostname, username, password):
    """ This function get the ltm pools and memers from F5 Device
    Output:
        Object
    """
    try:
        # create empty pool list
        pool_list = []

        # connect to F5 device
        mgmt = ManagementRoot(hostname, username, password)
        ltm = mgmt.tm.ltm

        # get pool list from F5
        pools = ltm.pools.get_collection()

        # extract pool name, subPath and member collection from the pools
        for pool in pools:
            member_collection = get_members_under_pool(pool)
            single_pool = LtmPoolModel(
                pool_name=pool.name,
                members=member_collection
            )
            if hasattr(pool, 'subPath'):
                    single_pool.sub_path = pool.subPath
            pool_list.append(single_pool)

        # sort the pools by name
        sorted_pool = sorted(pool_list, key = lambda i: i.pool_name)

        # extract the status and status reason of the pool
        for pp in sorted_pool:
            if pp.sub_path != '':
                sin_pool = ltm.pools.pool.load(transform_name=True, name=pp.sub_path + "/" + pp.pool_name , partition="Common")
            else:
                sin_pool = ltm.pools.pool.load(name=pp.pool_name)

            poolstats = sin_pool.stats.load()
            if pp.sub_path != '':
                state_details = poolstats.entries['https://localhost/mgmt/tm/ltm/pool/~Common~'+ pp.sub_path +'~'+ pp.pool_name +'/~Common~'+ pp.sub_path +'~'+ pp.pool_name +'/stats']['nestedStats']['entries']
            else:
                state_details = poolstats.entries['https://localhost/mgmt/tm/ltm/pool/'+ pp.pool_name +'/~Common~'+ pp.pool_name +'/stats']['nestedStats']['entries']

            if 'status.availabilityState' in state_details:
                pp.status = state_details['status.availabilityState']['description']
            if 'status.statusReason' in state_details:
                pp.status_reason = state_details['status.statusReason']['description']

        # convert the extracted model to json string
        json_string = json.dumps(sorted_pool, default=obj_dict)
        if __name__ == '__main__':
            print(json_string)

        # used when calling the script from another python script
        return sorted_pool
        
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
    get_ltm_pools_and_members(opts.hostname, username, password)

