from dir_sync import DirectorySyncManager
import time
import os

# Initialize the DirectorySyncManager
directory = "test"
manager = DirectorySyncManager(root=directory, interval=5)

# Start the directory monitoring thread
manager.start()

# Here, write your code that you want to run after manager.start()
print("Running some other operations...")
os.makedirs(f"{directory}", exist_ok=True)
with open(f"{directory}/foo.txt", "w") as f:
    f.write("Hello, world! ")
time.sleep(2)  # Example delay to simulate doing work

# Stop the directory monitoring thread
manager.stop()
print("Stopped the directory monitoring.")
