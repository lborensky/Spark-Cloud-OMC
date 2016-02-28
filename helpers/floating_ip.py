#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from novaclient.v1_1 import client as nvclient

def get_floating_ip():
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    # récupération d'une adresse IP flottante et association à la VM
    return nova.floating_ips.create(nova.floating_ip_pools.list()[0].name)

def addFloatingIP(instance):
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    floating_ip = get_floating_ip()
    instance.add_floating_ip(floating_ip)
    return str(floating_ip.ip)

if __name__ == "__main__":
    print(get_floating_ip())
