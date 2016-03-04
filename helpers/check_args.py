#!/usr/bin/python
import os, sys
from novaclient.v1_1 import client as nvclient

def checkArgs_for_launch(args):
    try:
        args.flavor = str(args.flavor)

        if args.num_slaves is None:
            print("\nERROR: Please specify the number of slaves")
            raise ValueError

        else:
            args.num_slaves = int(args.num_slaves)

        if args.keyname is None:
            print("\nERROR: Please specify your nova public key")
            raise ValueError

        else:
            args.keyname = str(args.keyname)

        if args.cluster_name is None:
            print("\nERROR: Please specify a cluster name")
            raise ValueError

        else:
            args.cluster_name = str(args.cluster_name)

        if len(args.cluster_name) > 15:
            print("\nERROR: Cluster Name too long.. Max 10 chars")
            raise ValueError

               # check that there are any slaves to create
        if args.num_slaves < 1:
            print("\nERROR: There are no slaves to create...")
            raise ValueError

        # double check that more than 10 slaves is not a typo
        if args.num_slaves > 10:
            input = raw_input("Are you sure you want to create "
                              + str(args.num_slaves)
                              + " Slaves? (y/n): ")
            if input != 'y':
                print("OK, Give it another try")
                sys.exit(0)

        nova = nvclient.Client(username=os.environ['OS_USERNAME'],
          project_id=os.environ['OS_TENANT_NAME'],
          api_key=os.environ['OS_PASSWORD'],
          auth_url=os.environ['OS_AUTH_URL'],
          insecure=True)

        if not nova.images.findall(id=args.image):
            print("Given Image " + args.image + " not found in Nova")
            raise ValueError

        if not nova.flavors.findall(name=args.flavor):
            print("Given Flavor " + args.flavor + " not registered in Nova")
            raise ValueError

        if not nova.keypairs.findall(name=args.keyname):
            print("Given Keypair " + args.keyname + " not found in Nova")
            raise ValueError
        if nova.keypairs.findall(name=args.cluster_name + "-key"):
            print("Cannot continue.. Please delete the offending key:"
                  + args.cluster_name + "-key")
            raise ValueError
        return args

    except (OSError, ValueError) as err:
        print(err)
        print("Please recheck your arguments\n")
        sys.exit(0)


def checkArgs_for_destroy(args):
    master = args.cluster_name
        
    if master is None:
        print("Please specify a master for deleting the cluster")
        sys.exit(0)
    else:
        return master
