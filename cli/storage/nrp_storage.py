#!/usr/bin/env python3

from enum import Enum
from dataclasses import dataclass
import argparse
import re

from rclone_helper import RcloneHelper
from k8s_helper import K8sHelper

class NrpStorageType(str, Enum):
    """Storage types on NRP platform."""
    LOCAL = "local"
    S3 = "s3"
    PVC = "pvc"

    def __str__(self):
        return self.value

    def get_regex(self):
        """Get the prefix for this storage type."""
        # Note: regex group 1 is for the whole path after protocol url prefix;
        #   subsequent groups are the different parts, e.g. bucket/PVC name and path.
        match self.value:
            case NrpStorageType.LOCAL:
                return re.compile(r'^((\/?(?:[\w.-]+\/)*(?:[\w.-]+)?))$')
            case NrpStorageType.S3:
                return re.compile(r'^s3://(([\w.-]+):([\w.-]+(?:\/[\w.-]+)*\/?))$')
            case NrpStorageType.PVC:
                return re.compile(r'^pvc://(([\w.-]+):([\w.-]+(?:\/[\w.-]+)*\/?))$')
            case _:
                raise NotImplementedError()

    @staticmethod
    def get_ordered_list():
        """Get an ordered list to test again their prefixes."""
        return [
            NrpStorageType.S3,
            NrpStorageType.PVC,
            NrpStorageType.LOCAL,
        ]

@dataclass
class NrpStoragePath:
    """Represent a storage path on NRP, including its type and path."""
    type: NrpStorageType
    path: str
    paths: list[str]

class NrpStorage:
    """An NRP storage client."""
    def __init__(self):
        self.src_path = None
        self.dst_path = None
        print("Initialize storage provider helpers ...")
        self.rclone = RcloneHelper()
        self.k8s = K8sHelper()

    def _parse_path(self, path: str) -> NrpStoragePath:
        """Parse a storage path."""
        for storage_type in NrpStorageType.get_ordered_list():
            match = storage_type.get_regex().match(path)
            if match:
                return NrpStoragePath(storage_type, match.group(1), match.groups()[1:])
        raise ValueError(f'Unable to parse path "{path}"')

    def _sync(self):
        src_type = self.src_path.type
        dst_type = self.dst_path.type
        if src_type == dst_type:
            match src_type:
                case NrpStorageType.LOCAL:
                    print('Syncing between local paths via rclone ...')
                    self.rclone.sync(self.src_path.path, self.dst_path.path)
                case NrpStorageType.S3:
                    print('Syncing between S3 paths via rclone ...')
                    self.rclone.sync(self.src_path, self.dst_path)
                case NrpStorageType.PVC:
                    print('Syncing between PVC paths via k8s job ...')
                    self.k8s.sync_pvc_to_pvc(self.src_path.path, self.dst_path.path)
        else:
            storage_types = set([src_type, dst_type])
            if storage_types == { NrpStorageType.LOCAL, NrpStorageType.S3 }:
                print('Syncing between local and S3 path via rclone ...')
                self.rclone.sync(self.src_path.path, self.dst_path.path)
            elif storage_types == { NrpStorageType.LOCAL, NrpStorageType.PVC }:
                print('Syncing between local and PVC path via temporary S3 bucket (rclone + k8s job) ...')
                print('Creating temporary S3 bucket to transfer between local and PVC volume ...')
                (s3_endpoint, s3_bucket_name) = self.rclone.create_bucket()
                s3_path = f'{s3_endpoint}:{s3_bucket_name}'
                if src_type == NrpStorageType.LOCAL:
                    # local -> temp s3 -> pvc
                    print('Syncing from local path to temp s3 bucket ...')
                    self.rclone.sync(self.src_path.path, s3_path)
                    print('Syncing from temp s3 bucket to PVC path ...')
                    self.k8s.sync_s3_to_pvc(s3_path, self.dst_path.path, self.rclone.get_size(s3_path))
                else:
                    # pvc -> temp s3 -> local
                    print('Syncing from PVC path to temp s3 bucket ...')
                    self.k8s.sync_pvc_to_s3(self.src_path.path, s3_path)
                    print('Syncing from temp s3 bucket to local path ...')
                    self.rclone.sync(s3_path, self.src_path.path)
                print('Deleting temporary S3 bucket ...')
                self.rclone.delete_bucket(s3_endpoint, s3_bucket_name)
            elif storage_types == { NrpStorageType.S3, NrpStorageType.PVC }:
                print('Syncing between S3 and PVC path via k8s job ...')
                if src_type == NrpStorageType.S3:
                    self.k8s.sync_s3_to_pvc(self.src_path.path, self.dst_path.path,
                                            self.rclone.get_size(self.src_path.path))
                else:
                    self.k8s.sync_pvc_to_s3(self.src_path.path, self.dst_path.path)
            else:
                raise NotImplementedError('Unhandled cases')
        print('Sync completed')

    def sync(self, src_path: str, dst_path: str):
        """Sync src to dst."""
        self.src_path = self._parse_path(src_path)
        self.dst_path = self._parse_path(dst_path)
        self._sync()

def parse_args():
    """Parse script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='Source path')
    parser.add_argument('dst', help='Destination path')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    storage = NrpStorage()
    storage.sync(args.src, args.dst)

if __name__ == '__main__':
    main()
