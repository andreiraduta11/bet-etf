#!/usr/bin/env bash


SYMBOLS_FILE_NAME='symbols-data.json'

# Get the data in the specified file.
python3 collector.py

# Make it public on GitHub.
git add $SYMBOLS_FILE_NAME

git commit --amend --no-edit

git push -f
