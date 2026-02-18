import subprocess
import sys

def run(cmd):
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return res.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='ignore')

with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write("Python Version:\n")
    f.write(sys.version + "\n\n")
    f.write("nvidia-smi:\n")
    f.write(run("nvidia-smi") + "\n\n")
    f.write("nvcc:\n")
    f.write(run("nvcc --version") + "\n\n")
    f.write("pip list:\n")
    f.write(run("pip list") + "\n\n")
    f.write("Path:\n")
    f.write(run("echo %PATH%") + "\n\n")
