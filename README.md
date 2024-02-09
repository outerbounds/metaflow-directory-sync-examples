This repository contains a Metaflow tool you can use inside `@step` functions, that will sync a local directory with S3 periodically, in a background thread.

This is particularly useful when with long-running training jobs that save checkpoints at long intervals, and you want to establish a two-way sync to ensure that those checkpoints are being pushed to S3. 

The repository contains three examples. Each example folder contains the file `dir_sync.py`. To use it, place this file in the same directory as your Metaflow flow and import the `DirectorySyncManager` in 
1. [Example without Metaflow](./basic_example/): How to use the `DirectorySyncManager` in Python code.
2. [Example with Metaflow](./basic_metaflow_example/): How to use the `DirectorySyncManager` in a Metaflow workflow.
3. [Example with HuggingFace Trainer Workflow](./hf_trainer_example/): How to use the `DirectorySyncManager` in a Metaflow workflow that does multinode HuggingFace Training.

The steps to use the `DirectorySyncManager` are:
1. Create the object `manager = DirectorySyncManager(...)` using these arguments.
    - `root`: You must set this to the directory on the `@step` you want to sync to S3.
    - `s3_root`: Specify this or `run`. This can be any S3 path your task can write to.
    - `run`: Specify this or `s3_root`. This is the Metaflow Run object. You can use `self` when set inside a `FlowSpec`.
    - `interval`: How often to check for changes in the `root`, and if detected, push the new contents to S3.
    - `node_index`: Use this if you are running a `num_parallel` job in the Metaflow task. Set it with `current.parallel.node_index`.
2. Start the manager `manager.start()`.
3. Run the code you want to sync during.
4. Stop the manager `manager.stop()`.