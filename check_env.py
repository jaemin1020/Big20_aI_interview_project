import os
import subprocess
import sys

def get_env_info():
    results = []
    results.append(f"Python: {sys.version}")
    results.append(f"CWD: {os.getcwd()}")
    results.append(f"CUDA_PATH: {os.environ.get('CUDA_PATH')}")
    
    # Check common CUDA paths
    base_cuda = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if os.path.exists(base_cuda):
        results.append(f"Found CUDA base folder: {os.listdir(base_cuda)}")
        for v in os.listdir(base_cuda):
            bin_path = os.path.join(base_cuda, v, "bin")
            if os.path.exists(bin_path):
                results.append(f"Found bin path: {bin_path}")
                dlls = [f for f in os.listdir(bin_path) if f.lower().endswith('.dll') and ('cuda' in f.lower() or 'cublas' in f.lower())]
                results.append(f"DLLs in {v}: {dlls[:5]}...")

    # Check if llama-cpp-python is actually installed and where
    try:
        import llama_cpp
        results.append(f"llama_cpp file: {llama_cpp.__file__}")
    except Exception as e:
        results.append(f"llama_cpp import failed: {e}")

    return "\n".join(results)

with open('env_check.txt', 'w', encoding='utf-8') as f:
    f.write(get_env_info())
