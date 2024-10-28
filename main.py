# main.py

import subprocess

def run_file(filename):
    subprocess.run(["python", filename])

if __name__ == "__main__":
    files_to_run = ["get_ignition.py", "get_permanent_parkings.py", "get_last_parking.py", "fileget_permenent_time4.py"]

    for file in files_to_run:
        print(f"Running {file}...")
        run_file(file)
        print(f"Finished {file}\n")
