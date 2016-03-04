#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from novaclient.v1_1 import client as nvclient

def extract_hash(server):
    if server.metadata:
        for key in server.metadata:
            value = server.metadata[key]
    else:
        value = None
    return value

def getVMByName(name, hash=None):
    server_list = []
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    # Find all VMs whose name matches
    servers = nova.servers.list(search_opts={'name': name})
    # servers = nova.servers.list()
    # Filter out the VMs with correct hash
    for server in servers:
        val = extract_hash(server)
        if val == hash:
            server_list.append(server)
    return server_list

def getVMById(id):
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    return nova.servers.get(id)
