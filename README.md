This repository contains a Metaflow tool you can use inside `@step` functions, that will sync a local directory with S3 periodically, in a background thread.

This is particularly useful when with long-running training jobs that save checkpoints at long intervals, and you want to establish a two-way sync to ensure that those checkpoints are being pushed to S3. 

The repository contains three examples. Each example folder contains the file `dir_sync.py`. To use it, place this file in the same directory as your Metaflow flow and import the `DirectorySyncManager` in 
1. [Example without Metaflow](./basic_example/): How to use the `DirectorySyncManager` in Python code.
2. [Example with Metaflow](./basic_metaflow_example/): How to use the `DirectorySyncManager` in a Metaflow workflow.
3. [Example with HuggingFace Trainer Workflow](./hf_trainer_example/): How to use the `DirectorySyncManager` in a Metaflow workflow that does multinode HuggingFace Training.