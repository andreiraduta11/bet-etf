#!/bin/bash


SYMBOLS_FILE_NAME='symbols-data.json'

# Get the data in the specified file.
/usr/bin/python3 collector.py

# Make it public on GitHub.
/usr/bin/git add $SYMBOLS_FILE_NAME

/usr/bin/git commit --amend --no-edit

/usr/bin/git push -f origin master
