import os
import time
import threading
import tarfile
from typing import Union, Dict
from metaflow import S3
from metaflow.metaflow_config import DATATOOLS_S3ROOT


class DirectorySyncManager:
    def __init__(self, root, s3_root=None, run=None, interval=5, node_index=None):
        self.root = os.path.relpath(path=root, start=os.getcwd())
        self.interval = interval
        self.s3_root = s3_root
        self.run = run
        self.node_index = node_index
        self.file_registry = {}
        self.stop_event = threading.Event()

    def _check_directory_last_update(self) -> bool:
        """
        Recursively check the last update time for any file of the directory.
        Rule: If any file has changed since last check, then restart the process.
        """
        modified_since_last_check = False
        if not os.path.exists(self.root):
            return False

        def _check_file_in_registry(file_path):
            modification_time = os.path.getmtime(file_path)
            last_update = None

            # case 1: new file
            if file_path not in self.file_registry:
                self.file_registry[file_path] = modification_time
                return True

            # case 2: updated file
            last_update = self.file_registry[file_path]
            if modification_time > last_update:
                self.file_registry[file_path] = modification_time
                return True
            else:  # case 3: unchanged file
                return False

        modified_since_last_check = _check_file_in_registry(self.root)
        for root, dirs, files in os.walk(self.root):
            for file in files:
                file_path = os.path.join(root, file)
                file_updated = _check_file_in_registry(file_path)
                modified_since_last_check = modified_since_last_check or file_updated

        return modified_since_last_check

    def _get_tar_bytes(self):
        "Zip from the root of the directory and return the bytes of the tar file."
        with tarfile.open(f"{self.root}.tar.gz", "w:gz") as tar:
            tar.add(self.root, arcname=os.path.basename(self.root))
        with open(f"{self.root}.tar.gz", "rb") as f:
            tar_bytes = f.read()
        return tar_bytes

    def _get_s3_client(self):
        "Return an S3 object based on the run or s3_root."
        if self.run:
            return S3(run=self.run)
        elif self.s3_root:
            return S3(s3root=self.s3_root)
        else:
            return S3(s3root=os.path.join(DATATOOLS_S3ROOT, self.root))

    def _upload_to_s3(self, tar_bytes):
        "Push the tar file to S3."
        s3 = self._get_s3_client()
        if s3 is None:
            return None
        if self.node_index is not None:
            self.s3_path = s3.put(
                f"{self.root}-node-{self.node_index}.tar.gz", tar_bytes
            )
        else:
            self.s3_path = s3.put(f"{self.root}.tar.gz", tar_bytes)
        s3.close()

    def _download_from_s3(
        self, all_nodes: bool = False
    ) -> Union[bytes, Dict[str, bytes]]:
        "Pull the tar file(s) from S3."
        s3 = self._get_s3_client()
        candidate_paths = s3.list_paths()
        if all_nodes:
            tar_balls = {}
            for s3obj in candidate_paths:
                if self.root in s3obj.key:
                    obj = s3.get(s3obj.key)
                    tar_balls[obj.key] = obj.blob
            s3.close()
            return tar_balls
        elif self.node_index is not None:
            tar_bytes = s3.get(f"{self.root}-node-{self.node_index}.tar.gz").blob
        else:
            tar_bytes = s3.get(f"{self.root}.tar.gz").blob
        s3.close()
        return tar_bytes

    def _extract_tar(self, tar_bytes, path=None):
        """
        Extract the tar file to the root of the directory.
        If `path` is specified, assumed to be a file path and extract to that location.
        The use case for path is
        """
        if path:
            with open(path, "wb") as f:
                f.write(tar_bytes)
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(path=path.replace(".tar.gz", ""))
            os.remove(path)
        else:
            with open(f"{self.root}.tar.gz", "wb") as f:
                f.write(tar_bytes)
            with tarfile.open(f"{self.root}.tar.gz", "r:gz") as tar:
                tar.extractall(path=os.path.dirname(self.root))
            os.remove(f"{self.root}.tar.gz")

    def download(self, all_nodes=False):
        if all_nodes:
            tar_balls = self._download_from_s3(all_nodes=all_nodes)
            for _path, _bytes in tar_balls.items():
                self._extract_tar(_bytes, path=_path)
        else:
            tar_bytes = self._download_from_s3()
            self._extract_tar(tar_bytes)

    def _check_and_push(self):
        modified_since_last_check = self._check_directory_last_update()
        if modified_since_last_check:
            tar_bytes = self._get_tar_bytes()
            self.s3_path = self._upload_to_s3(tar_bytes)

    def _periodic_check(self):
        "Periodically check the directory for updates and upload to S3 if changes observed."
        try:
            while not self.stop_event.is_set():
                self._check_and_push()
                time.sleep(self.interval)
        except Exception as e:
            print(f"An exception occurred: {e}")

    def start(self):
        if not hasattr(self, "_thread"):
            self._thread = threading.Thread(target=self._periodic_check, daemon=True)
            self._thread.start()
        else:
            self.stop()
            self.start()

    def stop(self):
        self.stop_event.set()
        self._check_and_push()
        if hasattr(self, "_thread"):
            self._thread.join()
            del self._thread
