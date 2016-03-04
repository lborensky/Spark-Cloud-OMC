# -*- coding: utf8 -*-
#!/usr/bin/python
import os, time, sys, paramiko
from novaclient.v1_1 import client as nvclient

# vérification de la présence du paramètre (@IP de PunchPlatform)
if len(sys.argv) != 4:
  print("usage: %s vm-name key-name userdata-file") % sys.argv[0]
  print("    vm-name: nom de la VM à instancier")
  print("    key-name-file: nom du fichier relatif à la clé privée d'accès root à la VM")
  print("    userdata-file: fichier de commandes à passer à Cloud-init")
  sys.exit(1)
else:
  vm_name = sys.argv[1]
  key_name = sys.argv[2]
  userdata_file = sys.argv[3]

# connexion aux services de Cloud OMC / IMA (nova)
nova = nvclient.Client(username=os.environ['OS_USERNAME'],
  project_id=os.environ['OS_TENANT_NAME'],
  api_key=os.environ['OS_PASSWORD'],
  auth_url=os.environ['OS_AUTH_URL'],
  insecure=True)

# réseau privé sur Cloud OMC / IMA
net_id="67a3e2c9-424a-463a-8a73-cccde3de4443"
nics = [{"net-id": net_id, "v4-fixed-ip": ''}]

# image de la VM gateway (broker de message et requeteur ELK)
image = nova.images.find(id="4fef4b01-31eb-4cc1-9960-d1dca922e546")

# (petite) VM avec 4Go de RAM
flavor = nova.flavors.find(name="t1.standard.medium-1")

# descripteur du fichier des commandes shell à passer au boot de la VM
ufile = open(userdata_file, 'r')

# nom de la VM
name = vm_name

# instanciation de la VM 
instance = nova.servers.create(name=name, 
  image=image, 
  flavor=flavor, 
  nics=nics,
  userdata=ufile,
  key_name=key_name)

status = instance.status

# attente relative au boot de la VM
sec = 0
while status != 'ACTIVE':
    sec = sec + 1 
    time.sleep(5)
    instance = nova.servers.get(instance.id)
    status = instance.status
    sys.stdout.write(".")
    sys.stdout.flush()

print ""
print "status: %s (boot in %d sec)" % (status, sec * 5)

# récupération d'une adresse IP flottante et association à la VM
floating_ip = nova.floating_ips.create(nova.floating_ip_pools.list()[0].name)
instance.add_floating_ip(floating_ip)
print "IP Internet = %s\n" % floating_ip.ip

# fonction de connexion SSH
def ssh_connect(k, ip):
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  ssh.connect(ip, username='root', key_filename=k)
  return ssh

# fonction de remontée de fichier(s) à la VM
def sendfile(k, ip):
  ssh = ssh_connect(k, ip)

  ftp = ssh.open_sftp()
  ftp.put('config_files.tar.gz', '/tmp/config_files.tar.gz')

  ftp.close()
  ssh.close()

# copie du fichier "config_files.tar.gz" sur la VM de création de la référence image cluster
print("attente de synchro: 30 sec")
time.sleep(30)
sendfile(key_name, floating_ip.ip)

ufile.close()
sys.exit(0)
