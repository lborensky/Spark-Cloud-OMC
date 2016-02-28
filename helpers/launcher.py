#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from novaclient.v1_1 import client as nvclient

def bootVM(image, flavor, keyname, hostname, desc, min_count=1, max_count=1):
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    image = nova.images.find(id=image)
    flavor = nova.flavors.find(name=flavor)

    # réseau privé sur Cloud OMC / IMA
    net_id="67a3e2c9-424a-463a-8a73-cccde3de4443"
    nics = [{"net-id": net_id, "v4-fixed-ip": ''}]

    instance = nova.servers.create(name=hostname,
                                   image=image,
                                   flavor=flavor,
                                   meta=desc,
                                   min_count=min_count,
                                   max_count=max_count,
                                   nics=nics,
                                   key_name=keyname)
    return instance

