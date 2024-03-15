#!/bin/bash

cd nba-bot

# Activate the virtual environment
source venv/bin/activate

# Run the Python script
python main.py

# commit and push the current changes
echo $(date +"%D")

git commit -am "$(date +"%D")"

#git push