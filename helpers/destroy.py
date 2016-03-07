#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from novaclient.v1_1 import client as nvclient

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

            # dettachement adresse IP flottante de la VM Master
            networks = master_id.networks
            ipf = networks['TestAPI-run'][1]
            master_id.remove_floating_ip(ipf)

            # libération de l'adresse IP flottante et retour au pool
            floating_ips = nova.floating_ips.list()
            for ips in floating_ips:
                if ips.ip == ipf:
                    nova.floating_ips.delete(ips)

            # suppression de la VM Master
            master_id.delete()

    except:
        print("ERROR: MasterNotFound")
