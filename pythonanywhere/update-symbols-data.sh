#!/bin/bash


SYMBOLS_FILE_NAME='symbols-data.json'

# Get the data in the specified file.
/usr/bin/python3 collector.py

# Make it public on GitHub.
/usr/bin/git add $SYMBOLS_FILE_NAME

/usr/bin/git commit -am "Daily PythonAnywhere Symbols Table update"

/usr/bin/git push -f
