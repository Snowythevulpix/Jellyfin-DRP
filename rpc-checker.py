import subprocess
import time
from datetime import datetime

#Jellyfin Discord Rich Presence script path
script_path = r"jellyfin discord rich presence.py"

def run_script(script_path):
    """Run the given script."""
    return subprocess.Popen(["python", script_path], shell=True)

# Function to check if the time is 00:00
def is_midnight():
    now = datetime.now()
    return now.strftime("%H:%M") == "00:00"

# Infinite loop to monitor and restart the script if it crashes or at 00:00
while True:
    print("Starting the script...")
    process = run_script(script_path)

    while True:
        # Check if it's 00:00, if so, kill the process and restart
        if is_midnight():
            print("It's 00:00. Restarting the script...")
            process.terminate()  # Terminate the script at midnight
            process.wait()  # Wait for the script to fully terminate
            break  # Exit the inner loop to restart the script

        # Check if the process has exited for any other reason (e.g., crash)
        if process.poll() is not None:
            print("Script has stopped unexpectedly. Restarting...")
            break

        # Sleep for 1 second to avoid high CPU usage
        time.sleep(1)

    # Add a small delay before restarting (optional)
    time.sleep(2)
