#!/usr/bin/python3
""" This Script is Getting the Certificares installed on F5 Device Information
Input Parameters:
    Hostname or IP
Input Example:
    python get_certificates.py --hostname {$device_ip}
Output:
    Example:
        [
            {"obj_cat": "sys", "obj_type": "ssl-cert", "obj_name": "websites1.crt",
                "expiration_string": "\"Jan 12 23:59:59 2018 GMT\"", "issuer": "\"CN=Symantec Class 3 Secure Server CA - G4,OU=Symantec Trust Network,O=Symantec Corporation,C=US\"",
                "subject": "\"CN=web1.xyz.com.sa,OU=IT,O=XYZ Company,L=Cairo,ST=Cairo,C=SA\"", "system_path": "Missing"}
        ]

Important Note:
    - To connect you need to use non root user.
    - Use it with your own risk.
Tested Versions:
    - Version 11.0 to 13.6
"""

import sys
import json
import getpass
import optparse
from f5.bigip import ManagementRoot

class CertificateModel:
    """ This Model for Certificate in F5 Devices """
    def __init__(self, obj_cat, obj_type, obj_name, expiration_string, issuer, subject, system_path):
        self.obj_cat = obj_cat
        self.obj_type = obj_type
        self.obj_name = obj_name
        self.expiration_string = expiration_string
        self.issuer = issuer
        self.subject = subject
        self.system_path = system_path

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

def extract_f5_certificates_from_string(str_input):
    """ This function took the result of get_certificates and change it to dict """
    first_obj = str_input.split('}\n')
    json_extraction = []
    for obj in first_obj:
        if '{' in obj:
            second_obj = obj.split('{')
            single_obj = CertificateModel(
                obj_cat=second_obj[0].split(' ')[0].strip(),
                obj_type=second_obj[0].split(' ')[2].strip(),
                obj_name=second_obj[0].split(' ')[3].strip(),
                expiration_string=second_obj[1].split('expiration-string ')[1].split('\n')[0].strip(),
                issuer=second_obj[1].split('issuer ')[1].split('\n')[0].strip(),
                subject=second_obj[1].split('subject ')[1].split('\n')[0].strip(),
                system_path=second_obj[1].split('system-path ')[1].split('\n')[0].strip() if ('system-path ' in second_obj[1]) else 'Missing'
            )
            json_extraction.append(single_obj)
    return json_extraction

def get_ltm_virtual_servers_include_pool_name(hostname, username, password):
    """ This function get the certificates from F5 Device """
    try:
        # create empty certificates list
        certificates = []

        # connect to F5 device
        mgmt = ManagementRoot(hostname, username, password)

        # get certificates list from F5
        returned_obj = mgmt.tm.util.bash.exec_cmd(
            'run', utilCmdArgs='-c "tmsh list sys file ssl-cert recursive"')
        result = str(returned_obj.commandResult)

        certificates = extract_f5_certificates_from_string(str_input=result)

        # convert the extracted model to json string
        json_string = json.dumps(certificates, default=obj_dict)
        if __name__ == '__main__':
            print(json_string)

        return certificates
        
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
