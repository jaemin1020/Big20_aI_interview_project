#!/bin/bash

# Start Jupyter Notebook in the background
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' &

# Start Celery worker in the foreground
celery -A main.app worker --loglevel=info
