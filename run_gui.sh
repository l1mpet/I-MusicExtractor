#!/bin/bash
echo "Starting I-MusicExtractor GUI..."
python3 I-MusicExtractor-GUI.py
if [ $? -ne 0 ]; then
  echo ""
  echo "An error occurred. Press Enter to exit."
  read
fi 