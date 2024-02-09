from metaflow import FlowSpec, step, deepspeed, current, kubernetes, environment, pypi
from dir_sync import DirectorySyncManager
import os

N_NODES = 2
RESOURCES = {
    "image": "public.ecr.aws/p7g1e3j4/deepspeed:6",
    # "gpu": 1,
    "memory": "12000",
    "port": 22,
    "cpu": 2,
    # "node_selector": "outerbounds.co/provider=azure",
    # "gpu_vendor": "nvidia"
}


class MultinodeTrainerDirSync(FlowSpec):
    @step
    def start(self):
        self.next(self.train, num_parallel=N_NODES)

    @pypi(packages={"matplotlib": "3.8.2"})
    @environment(
        vars={
            "NCCL_SOCKET_IFNAME": "eth0",
            "WANDB_API_KEY": os.environ["WANDB_API_KEY"],
            "TOKENIZERS_PARALLELISM": "false",
        }
    )
    @kubernetes(**RESOURCES)
    @deepspeed
    @step
    def train(self):
        self.checkpoint_dir = "training_output"
        manager = DirectorySyncManager(  # Use the same signature after flow completes, then manager.download() to unpack.
            root=self.checkpoint_dir,  # What directory to sync?
            run=self,  # How to version the run? You can pass run, s3root for arbitrary path, or leave it blank and path is selected for you.
            node_index=current.parallel.node_index,  # If running in parallel, pass the node index to version the contents in S3 by each node.
            interval=1,  # How often to check for changes? Every ten seconds, in this case.
        )
        manager.start()
        current.deepspeed.run(
            entrypoint="trainer.py",
            entrypoint_args=["--checkpoint-dir", self.checkpoint_dir],
        )
        manager.stop()
        self.next(self.join)

    @step
    def join(self, inputs):
        self.checkpoint_dir = inputs[0].checkpoint_dir
        self.next(self.end)

    @step
    def end(self):
        # unlike the train step, this is run locally
        # in this case, we'll just use the manager to download the checkpoint (be careful if checkpoints are huge, this is just a demo)
        manager = DirectorySyncManager(root=self.checkpoint_dir, run=self)
        manager.download(all_nodes=True)  # download the checkpoints from all nodes


if __name__ == "__main__":
    MultinodeTrainerDirSync()
