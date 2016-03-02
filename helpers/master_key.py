#!/usr/bin/python
import os
from novaclient.v1_1 import client as nvclient
from subprocess import Popen, PIPE

def register_key(key, master_name, verbose):
    try:
        nova = nvclient.Client(username=os.environ['OS_USERNAME'],
          project_id=os.environ['OS_TENANT_NAME'],
          api_key=os.environ['OS_PASSWORD'],
          auth_url=os.environ['OS_AUTH_URL'],
          insecure=True)

        key_name = master_name
        nova.keypairs.create(name=key_name, public_key=key)
        return key_name
    except (ValueError, OSError) as err:
        if verbose:
            print(err)
        print("\nERROR: Could not communicate with master\n")
        exit()
    except:
        print("Unknown error Occured")
        raise

def delete_key(master_name):
    try:
        nova = nvclient.Client(username=os.environ['OS_USERNAME'],
          project_id=os.environ['OS_TENANT_NAME'],
          api_key=os.environ['OS_PASSWORD'],
          auth_url=os.environ['OS_AUTH_URL'],
          insecure=True)

        nova.keypairs.delete(master_name)
    except:
        print("Could not find or delete keypair: " + master_name)
