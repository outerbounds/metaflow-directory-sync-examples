from metaflow import FlowSpec, step, current, kubernetes

N_NODES = 2
RESOURCES = {
    "memory": "12000",
    "port": 22,
    "cpu": 2,
}


class HelloSubprocessMetaflowCurrent(FlowSpec):
    @step
    def start(self):
        self.next(self.train)

    # @kubernetes(**RESOURCES)
    @step
    def train(self):

        from metaflow import current
        from dir_sync import DirectorySyncManager
        import os
        import subprocess
        import time

        directory_to_sync = "test"
        manager = DirectorySyncManager(root=directory_to_sync, run=self, interval=1)
        manager.start()

        # do stuff that changes the directory
        os.makedirs(f"{directory_to_sync}/subdir", exist_ok=True)
        with open(f"{directory_to_sync}/subdir/foo.txt", "w") as f:
            f.write("Hello, world! ")
        time.sleep(2)  # how does this compare to time_interval arg of DirectorySync?
        with open(f"{directory_to_sync}/subdir/foo.txt", "a") as f:
            f.write("Hello, world! Again!")
        time.sleep(2)
        with open(f"{directory_to_sync}/subdir/bar.txt", "a") as f:
            f.write("A whole new (hello) world!")
        time.sleep(2)

        manager.stop()
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    HelloSubprocessMetaflowCurrent()
