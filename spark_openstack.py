#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import with_statement
import sys, paramiko

try:
    from fabric.api import *
    from fabric.contrib.files import exists
except ImportError as e:
    print("Could not import fabric, make sure it is installed")
    sys.exit(1)

import argparse
import hashlib
from datetime import datetime
from time import sleep
try:
    from helpers.check_args import checkArgs_for_launch
    from helpers.check_args import checkArgs_for_destroy
    from helpers.launcher import bootVM
    from helpers.destroy import destroy_cluster
    from helpers.verify_boot import verify_all
    from helpers.floating_ip import addFloatingIP
    from helpers.find_vm import getVMByName, getVMById, extract_hash
    from helpers.find_vm import getVMById
except ImportError as e:
    print("Could not import helpers, MayDay MayDay...")
    sys.exit(1)

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

# fonction de gestion des arguments du programme
def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a Spark Cluster on "
                                     "Cloud OMC/IMA.", epilog="Example Usage: "
                                     "./spark-openstack launch --keyname "
                                     "mykey --slaves 5 --cluster_name \
                                     clusterName")
    parser.add_argument('action', help = "launch|destroy|add-nodes")
    parser.add_argument("-c", "--cluster_name", metavar="",
                        dest="cluster_name",
                        action="store",
                        help="Name for the cluster.")
    parser.add_argument("-s", "--slaves", metavar="", dest="num_slaves",
                        type=int, action="store",
                        help="Number of slave nodes to spawn.")
    parser.add_argument("-k", "--keyname", metavar="", dest="keyname",
                        action="store",
                        help="Your Public Key registered in OpenStack")
    parser.add_argument("-f", "--flavor", metavar="", dest="flavor",
                        action="store", default="t1.standard.medium-1",
                        help="Size of Virtual Machine")
    parser.add_argument("-i", "--image", metavar="", dest="image",
                        action="store", default="c55239d8-0c75-4c81-909e-0dd9debdb50f",
                        help="Image name to boot from")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_true", help="verbose output")
    parser.add_argument("-D", "--dryrun", dest="dryrun",
                        action="store_true", help="Dry run")

    return parser.parse_args()

# fonction du lancement du cluster (master et slave(s))
def launch_cluster(options):
    username = "hduser"
    print("###########################################################\n")
    print("Booting Master... ")
    master_vm = boot_master(opts)
    master_name = master_vm.name
    print("Master booted, Assigning floating ip... ")
    floating_ip = addFloatingIP(master_vm)
    print("Floating IP assigned: " + floating_ip)

    # récupération de la clé publique et privée associées au compte 'hduser'
    sys.sleep(10)
    hdu_pkey(options.keyname, floating_ip, "get")

    print("###########################################################\n")
    print("Launching Slaves...")

    # Now launch the requested number of slaves with masters public key
    hash = extract_hash(master_vm)
    meta = {'slave': hash}

    slave_name = options.cluster_name + "-slave"
    status = bootVM(options.image, options.flavor, master_keyname, slave_name,
                    meta, options.num_slaves, options.num_slaves)

    name = "slave"
    # find all vms whose name contains slave and matches hash
    slaves = getVMByName(name, hash)
    # get private ips of all slaves booted with hash
    slaves_list = verify_all(slaves)
    print("Got slaves list: " + str(slaves_list))
    print("All VMs finished booting")
    print("###########################################################\n")

    # push private key "hduser" on slaves
    for host in slaves_list:
      hdu_pkey(options.keyname, host, "put")
    
    print("Uploading files to master")
    status = upload_files(master_vm, slaves_list, username, floating_ip)
    print("\n")
    print("*********** All Slaves Created *************")
    print("*********** Slaves file Copied to Master *************")
    print("*********** Check that all slaves are RUNNING *************")
    print("*********** Login to Master and run the fabric file *********")
    print("\n")
    print("Login to Master as: ssh -i kspark hduser@" + floating_ip)

    return True

def upload_files(master_id, slaves_list, username, floating_ip):
    # Create a file with master ip
    m_file = "/tmp/masters"
    s_file = "/tmp/slaves"
    master_file = open(m_file, "w")
    master_private_ip = master_id.networks['TestAPI-run'][0]
    master_file.write(master_private_ip + "\n")

    # Create a file with slave ips
    slave_file = open(s_file, "w")
    for host in slaves_list:
        slave_file.write(host + "\n")
    master_file.close()
    slave_file.close()

    # recopie de 3 fichiers sur le master (m_file, s_file et f_file)
    f_file = "helpers/fabfile.py"
    hadoop_conf_dir = "/usr/local/hadoop/etc/hadoop/"

    ssh = ssh_connect("kspark", floating_ip)

    ftp = ssh.open_sftp()
    ftp.put(m_file, hadoop_conf_dir + "masters")
    ftp.put(s_file, hadoop_conf_dir + "slaves")
    ftp.put(f_file, '/home/hduser/')
    ssh.exec_command("chown hduser:hduser " + hadoop_conf_dir + "masters " + hadoop_conf_dir + "slaves ")

    ftp.close()
    ssh.close()

    return True

# fonction de boot de la VM Master avec API Openstack
def boot_master(options):
    # unique hash to identify the cluster
    hash = hashlib.sha1(str(datetime.now())).hexdigest()

    # set metadata for master
    meta = {'master': hash}

    # master_name = "master-" + options.cluster_name
    master_name = options.cluster_name + "-master"

    # Boot Master
    master_vm = bootVM(options.image, options.flavor, options.keyname,
                    master_name, meta)
    master_id = master_vm.id
    while master_vm.status == 'BUILD':
        sleep(5)
        # re get master to refresh status
        master_vm = getVMById(master_id)

    return master_vm

if __name__ == "__main__":
    opts = parse_arguments()
    if str(opts.action) == 'launch':
        args = checkArgs_for_launch(opts)
        print("###########################################################\n")
        print("Arguments Verified... preparing launch sequence")
        if args.dryrun:
            print("\n")
            print("Action: " + str(args.action))
            print("Cluster Name: " + str(args.cluster_name))
            print("Number of Slaves: " + str(args.num_slaves))
            print("Flavor: " + args.flavor)
            print("Image: " + args.image)
            print("Pub Key: " + args.keyname)
            print("\n")
            sys.exit(0)
        else:
            status = launch_cluster(opts)

    elif opts.action == 'destroy':
        master = checkArgs_for_destroy(opts)
        destroy_cluster(master)
    elif opts.action == 'add-nodes':
        print("###########################################################\n")
        print("Adding more nodes")
    
    else:
        print("Invalid command: " + opts.action)
        print("Please choose from launch or destroy")

