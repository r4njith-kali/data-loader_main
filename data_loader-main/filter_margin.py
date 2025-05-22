import pandas as pd
from datetime import timedelta

# Read the original data (make sure timestamp is parsed as datetime)
original_df = pd.read_csv("output.csv", parse_dates=["timestamp"])

# Read your aggregated data which should include 'start_time' and 'end_time' columns
aggregated_df = pd.read_csv("aggregated_motor_data.csv", parse_dates=["start_time", "end_time"])

# Calculate an extended time window for each cycle (5 minutes before start and 5 minutes after end)
# Create a list of tuples (window_start, window_end) for each cycle
windows = []
for idx, row in aggregated_df.iterrows():
    window_start = row['start_time'] - timedelta(minutes=5)
    window_end = row['end_time'] + timedelta(minutes=5)
    windows.append((window_start, window_end))

# For each window, filter original_df and combine results
filtered_list = [
    original_df[(original_df['timestamp'] >= start) & (original_df['timestamp'] <= end)]
    for start, end in windows
]

# Concatenate all the filtered subsets
filtered_df = pd.concat(filtered_list, ignore_index=True)

# Remove duplicates in case windows overlap
filtered_df = filtered_df.drop_duplicates()

# Save the resulting DataFrame to CSV
filtered_df.to_csv("filtered_with_margin.csv", index=False)

print("Filtered data with a 5-minute margin around each cycle saved to 'filtered_with_margin.csv'.")
