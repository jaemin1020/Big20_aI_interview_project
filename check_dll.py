import os

path = r"C:\Users\TJ\AppData\Local\Programs\Python\Python310\lib\site-packages\llama_cpp\lib\llama.dll"
with open('file_check.txt', 'w', encoding='utf-8') as f:
    if os.path.exists(path):
        f.write(f"EXISTS: {path}\n")
        f.write(f"Size: {os.path.getsize(path)}\n")
    else:
        f.write(f"DOES NOT EXIST: {path}\n")
        # Check if the folder exists
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            f.write(f"Folder exists: {folder}\n")
            f.write(f"Contents: {os.listdir(folder)}\n")
        else:
            f.write(f"Folder DOES NOT exist: {folder}\n")
