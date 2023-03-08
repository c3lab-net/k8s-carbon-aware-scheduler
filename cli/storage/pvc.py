#!/usr/bin/env python3

import os
import argparse
import csv
from dataclasses import dataclass
from enum import Enum
from time import sleep
from shlex import quote
import yaml

from util import load_yaml, run_command

@dataclass
class PvcStorageClass:
    """Represents a PVC storage class in Nautilus."""
    storage_class: str
    filesystem_type: str
    region: str
    access_modes: str
    restrictions: str
    storage_type: str
    size: str

def load_pvc_storage_classes_from_config():
    """Load available PVC storage classes from config file."""
    # TSV source: https://ucsd-prp.gitlab.io/userdocs/storage/ceph-posix/
    pvc_storage_classes_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "pvc.storage_classes.tsv")
    pvc_storage_classes = []
    with open(pvc_storage_classes_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        # print('fields:', reader.fieldnames)
        for row in reader:
            if row['Restrictions']:
                continue
            pvc_storage_classes.append(PvcStorageClass(
                storage_class=row['StorageClass'],
                filesystem_type = row['Filesystem Type'],
                region = row['Region'],
                access_modes = row['AccessModes'],
                restrictions = row['Restrictions'],
                storage_type = row['Storage Type'],
                size = row['Size'],
            ))
    return pvc_storage_classes

def get_pvc_storage_class(region: str, filesystem_type: str) -> PvcStorageClass:
    """Get the first matching PVC storage class."""
    try:
        print(PVC_STORAGE_CLASSES)
        return next(filter(lambda pvc:
            pvc.region == region and
            pvc.filesystem_type == filesystem_type and
            not pvc.restrictions, PVC_STORAGE_CLASSES))
    except StopIteration as ex:
        raise ValueError(f'No matching PVC storage class for'
                            f' region="{region}" and'
                            f' filesystem type="{filesystem_type}"') \
            from ex

PVC_STORAGE_CLASSES = load_pvc_storage_classes_from_config()

class Action(str, Enum):
    """Available action in this script."""
    CREATE = 'create'
    DELETE = 'delete'
    LIST = 'list'
    
    def __str__(self):
        return self.value

def parse_args():
    """Parse script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('action', type=Action, choices=list(Action))
    parser.add_argument('name', nargs='?', help='Name of the volume')
    parser.add_argument('size', nargs='?', type=str, help='Size of the volume')
    args = parser.parse_args()
    if args.action in [Action.CREATE, Action.DELETE] and not args.name:
        parser.error('name is required')
    if args.action == Action.CREATE and not args.size:
        parser.error('create requires a size.')
    return args

def get_pvc_template():
    """Get the PVC template file as YAML."""
    pvc_template_filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "pvc.template.yaml")
    return load_yaml(pvc_template_filepath)

def create_pvc_config(name, size, region, filesystem_type):
    """Create a PVC config object from the given parameters and PVC template."""
    pvc_config = get_pvc_template()
    pvc_config['metadata']['name'] = name
    pvc_storage_class = get_pvc_storage_class(region, filesystem_type)
    pvc_config['spec']['storageClassName'] = pvc_storage_class.storage_class
    pvc_config['spec']['accessModes'] = [ pvc_storage_class.access_modes ]
    pvc_config['spec']['resources']['requests']['storage'] = size
    return pvc_config

def get_pvc_status(name):
    """Get the status of PVC using kubectl."""
    return run_command(f'kubectl get pvc {quote(name)} ' +
                            quote('-o=jsonpath={.status.phase}'), print_command=False)

def create_pvc(name, size, region='US West', filesystem_type='CephFS'):
    """Run kubectl command to create a PVC and wait for success creation."""
    print(f'Creating PVC {name} of size {size} in region {region}'
            f' with filesystem type {filesystem_type} ...')
    pvc_config = create_pvc_config(name, size, region, filesystem_type)
    print(run_command('kubectl create -f -', yaml.dump(pvc_config), print_command=True))
    while True:
        pvc_status = get_pvc_status(name)
        print(f'Status: {pvc_status}')
        if pvc_status == 'Bound':
            break
        else:
            wait_seconds = 10
            print(f'Sleeping for {wait_seconds}s ...')
            sleep(wait_seconds)
    print(f'PVC {name} created.')
    print(run_command(f'kubectl get pvc {quote(name)}', print_command=True))

def delete_pvc(name):
    """Run kubectl command to delete a PVC matching the name."""
    print(run_command(f'kubectl delete pvc {quote(name)}', print_command=True))

def list_pvcs():
    """List all available PVCs."""
    print(run_command("kubectl get pvc", print_command=True))

def main():
    """Main function."""
    args = parse_args()
    match args.action:
        case Action.CREATE:
            create_pvc(args.name, args.size)
        case Action.DELETE:
            delete_pvc(args.name)
        case Action.LIST:
            list_pvcs()
        case _:
            raise ValueError(f'Invalid action {args.action}')

if __name__ == '__main__':
    main()
