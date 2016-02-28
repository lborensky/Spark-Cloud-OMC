#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from novaclient.v1_1 import client as nvclient

from verify_boot import verify_all
from find_vm import getVMByName, extract_hash
from master_key import delete_key

def destroy_cluster(master):
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    try:
        master_id = nova.servers.find(name=master)
        hash = extract_hash(master_id)
        print("wait... finding all associated slaves")
        name = "slave"
        slaves = getVMByName(name, hash)
        for slave in slaves:
            print(slave)
        input = raw_input("Are you sure you want to delete " 
                + master + 
                " ? (y/n): ")
        if input != 'y':
            print("Destruct Sequence Aborted")

        else:
            print("Now deleting: " + master )
            for slave in slaves:
                slave.delete()
            master_id.delete()

    except:
        print("ERROR: MasterNotFound")
