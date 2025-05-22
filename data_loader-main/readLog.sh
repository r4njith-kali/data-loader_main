#!/bin/bash

# Specify the directory where you want to search for .log files
log_directory="./log"

# Use the 'find' command to search for .log files in the specified directory
latest_log_file=$(find "$log_directory" -type f -name "*.log" -print0 | xargs -0 ls -lt | head -n 1 | awk '{print $NF}')

# Check if a .log file was found
if [ -n "$latest_log_file" ]; then
  echo "Latest .log file in $log_directory:"
  echo "$latest_log_file"
  cat $latest_log_file
else
  echo "No .log files found in $log_directory"
fi
