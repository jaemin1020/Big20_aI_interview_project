import os
import sys

def get_env_info():
    results = []
    results.append(f"Python: {sys.version}")
    results.append(f"PATH Environment:\n{os.environ.get('PATH')}")
    results.append(f"CUDA_PATH: {os.environ.get('CUDA_PATH')}")
    
    # Check common CUDA paths
    base_cuda = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if os.path.exists(base_cuda):
        results.append(f"Found CUDA base folder: {os.listdir(base_cuda)}")
        for v in os.listdir(base_cuda):
            bin_path = os.path.join(base_cuda, v, "bin")
            if os.path.exists(bin_path):
                results.append(f"Found bin path: {bin_path}")
                # List first 10 files to avoid bloat
                results.append(f"Files in {bin_path}: {os.listdir(bin_path)[:10]}")

    return "\n".join(results)

with open('env_check_v2.txt', 'w', encoding='utf-8') as f:
    f.write(get_env_info())
print("Environment check complete.")
