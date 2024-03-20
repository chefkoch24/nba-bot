#!/bin/bash

# Activate the virtual environment
source myenv/bin/activate

# Run the Python script
python main.py

# commit and push the current changes
echo $(date +"%D")

git add .

git commit -m "$(date +"%D")"

git push