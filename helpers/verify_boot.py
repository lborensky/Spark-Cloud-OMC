#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, paramiko
import time
from novaclient.v1_1 import client as nvclient

# fonction de connexion SSH
def ssh_connect(k, ip):
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  ssh.connect(ip, username='root', key_filename=k)
  return ssh

# fonction de récupération et de diffusion de clés SSH
def hdu_pkey(k, ip, cmd):
  ssh = ssh_connect(k, ip)

  ftp = ssh.open_sftp()
  if cmd == "get":
    ftp.get('/home/hduser/.ssh/id_rsa', 'kspark')
    ftp.get('/home/hduser/.ssh/id_rsa.pub', 'kspark.pub')

  if cmd == "put":
    ssh.exec_command("mkdir -p /home/hduser/.ssh")
    ftp.put('kspark.pub', '/home/hduser/.ssh/id_rsa.pub')
    ssh.exec_command("cat /home/hduser/.ssh/id_rsa.pub > /home/hduser/.ssh/authorized_keys")
    ssh.exec_command("chown hduser:hduser /home/hduser/.ssh/authorized_keys")
    ssh.exec_command("chmod 0600 /home/hduser/.ssh/authorized_keys")
    ssh.exec_command("rm -f /home/hduser/.ssh/id_rsa.pub")

  ftp.close()
  ssh.close()

def verify_and_configure(servers, sname, key):
    addresses = []
    nova = nvclient.Client(username=os.environ['OS_USERNAME'],
      project_id=os.environ['OS_TENANT_NAME'],
      api_key=os.environ['OS_PASSWORD'],
      auth_url=os.environ['OS_AUTH_URL'],
      insecure=True)

    n = 0
    for server in servers:
        timeout = 0
        status = server.status
        while status == 'BUILD':
            time.sleep(5)
            timeout = timeout + 5
            if timeout > 1200:
                print("OBS! taking more than 10 minutes...\n")
                print("Something is Wrong, debug or contact support.\n")
                sys.exit(-1)
            # Retrieve the instance again so the status field updates
            instance = nova.servers.get(server.id)
            status = instance.status

        if status == 'ERROR':
            print("status server (%s) = ERROR" % server.name) 
            sys.exit(-1)

        n = n + 1
        instance = nova.servers.get(server.id)

        # renommage de la VM (slave)
        name = sname + "-%02d" % n
        instance.update(name=name)

        # récupération d'une adresse IP flottante et association à la VM
        floating_ip = nova.floating_ips.create(nova.floating_ip_pools.list()[0].name)
        instance.add_floating_ip(floating_ip)

        # recopie des fichiers PKI à la VM
        hdu_pkey(key, floating_ip.ip, "put")

        # dettachement adresse IP flottante de la VM
        instance.remove_floating_ip(floating_ip.ip)

        # libération de l'adresse IP flottante et retour au pool
        nova.floating_ips.delete(floating_ip.id)

        print(instance.name + " booted with ip: " + str(instance.addresses["TestAPI-run"][0]["addr"]))
        addresses.append(str(instance.addresses["TestAPI-run"][0]["addr"]))
        
    return addresses
