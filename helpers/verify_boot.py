#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import time
from novaclient.v1_1 import client as nvclient

def verify_all(servers):
    addresses = []
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    for instance in servers:
        timeout = 0
        status = instance.status
        while status == 'BUILD':
            time.sleep(5)
            timeout = timeout + 5
            if timeout > 1200:
                print("OBS! taking more than 10 minutes...\n")
                print("Something is Wrong, debug or contact support.\n")
                exit()
            # Retrieve the instance again so the status field updates
            instance = nova.servers.get(instance.id)
            status = instance.status
        print(instance.name + " booted with ip: " +
              # str(instance.addresses["private"][0]["addr"]))
              str(instance.addresses["TestAPI-run"][0]["addr"]))
        # addresses.append(str(instance.addresses["private"][0]["addr"]))
        addresses.append(str(instance.addresses["TestAPI-run"][0]["addr"]))
    return addresses
