@echo off
pip install "https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.1/llama_cpp_python-0.3.1+cu121-cp310-cp310-win_amd64.whl"
if %errorlevel% neq 0 (
    pip install "https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.1/llama_cpp_python-0.3.1+cu118-cp310-cp310-win_amd64.whl"
)
