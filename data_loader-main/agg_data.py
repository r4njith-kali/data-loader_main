import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from datetime import timedelta

# ----------------------------------------------------------------------------
# 1) LOAD AND PREPARE THE DATA
# ----------------------------------------------------------------------------
file = "sie_mtr_raw_cm3_output.csv"
file_path = file  # Change to your file path
df = pd.read_csv(file_path, parse_dates=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# Fill NaN in the "current" column with 0
df["current"] = df["current_input"].fillna(0)
df["status_run"] = df["status_run"].fillna(0).astype(int)


# ----------------------------------------------------------------------------
# 2) LEARN MOTOR ACTIVITY USING GMM
# ----------------------------------------------------------------------------
def learn_threshold(current_values):
    """
    Determine an optimal current threshold using a 2-component Gaussian Mixture Model (GMM).
    Returns the probability that each sample belongs to the "active" cluster.
    """
    # Reshape for GMM: shape (num_samples, 1)
    current_reshaped = current_values.values.reshape(-1, 1)

    # Fit GMM with 2 clusters: idle vs. active
    gmm = GaussianMixture(n_components=2, random_state=42)
    gmm.fit(current_reshaped)

    # Get probability that each point belongs to the active cluster (we use cluster 1)
    probabilities = gmm.predict_proba(current_reshaped)[:, 1]
    return probabilities

# Get active probability for each row
optimal_probability = learn_threshold(df["current"])
df["active_prob"] = optimal_probability
df["motor_on"] = df["active_prob"] > 0.5

# ----------------------------------------------------------------------------
# 3) ASSIGN CYCLE IDs WITH SHORT OFF PERIOD HANDLING
# ----------------------------------------------------------------------------
# We'll iterate through the DataFrame row by row and assign a cycle ID only to rows
# where the motor is on. A new cycle starts when the motor goes from off to on
# *and* the off period was longer than a defined threshold.
off_threshold = 30  # seconds (adjust as needed)

cycle_ids = []  # to store cycle id for each row
current_cycle = 0
last_on_time = None

# Iterate over rows in the DataFrame (which is sorted by timestamp)
for idx, row in df.iterrows():
    if row["motor_on"]:
        if last_on_time is None:
            # First occurrence of motor on
            current_cycle += 1
            cycle_ids.append(current_cycle)
        else:
            # Check if previous row was off
            if idx > 0 and (df.loc[idx - 1, "motor_on"] == False):
                # Compute off duration: time since the last on state
                off_duration = (row["timestamp"] - last_on_time).total_seconds()
                if off_duration >= off_threshold:
                    # Off period is long enough -> start a new cycle
                    current_cycle += 1
                # Else, off duration is too short: remain in the same cycle
                cycle_ids.append(current_cycle)
            else:
                # Continuation of an active period
                cycle_ids.append(current_cycle)
        # Update last_on_time with current timestamp for rows where motor is on
        last_on_time = row["timestamp"]
    else:
        # For off periods, we can assign NaN (or keep the previous cycle if needed)
        cycle_ids.append(np.nan)

# Assign the cycle IDs to the DataFrame
df["cycle_id"] = cycle_ids

# ----------------------------------------------------------------------------
# 4) AGGREGATE CYCLES
# ----------------------------------------------------------------------------
NUM_REPRESENTATIVE_POINTS = 10  # Number of points to sample per cycle

def aggregate_cycle(cycle_df):
    if cycle_df.empty:
        return None

    start_time = cycle_df["timestamp"].min()
    end_time = cycle_df["timestamp"].max()
    duration = (end_time - start_time).total_seconds()
    min_current = cycle_df["current"].min()
    max_current = cycle_df["current"].max()
    avg_current = cycle_df["current"].mean()
    peak_to_peak = max_current - min_current

    num_rows = len(cycle_df)
    step = max(1, num_rows // NUM_REPRESENTATIVE_POINTS)
    sampled_points = cycle_df.iloc[::step][["timestamp", "current"]].head(NUM_REPRESENTATIVE_POINTS)

    rep_timestamps = list(sampled_points["timestamp"].astype(str))
    rep_currents = list(sampled_points["current"])

    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_sec": duration,
        "min_current": min_current,
        "max_current": max_current,
        "avg_current": avg_current,
        "peak_to_peak": peak_to_peak,
        "rep_timestamps": rep_timestamps,
        "rep_currents": rep_currents
    }

# Only aggregate rows where motor is on and a valid cycle_id is present
aggregated_data = (
    df[df["motor_on"] & df["cycle_id"].notna()]
    .groupby("cycle_id")
    .apply(aggregate_cycle)
    .dropna()
    .tolist()
)

aggregated_df = pd.DataFrame(aggregated_data)

# ----------------------------------------------------------------------------
# 5) SAVE RESULTS
# ----------------------------------------------------------------------------
aggregated_df.to_csv("aggregated_motor_data.csv", index=False)

parameters = {
    "optimal_probability": optimal_probability.tolist(),
    "off_threshold_sec": off_threshold
}
param_df = pd.DataFrame([parameters])
param_df.to_csv("learned_parameters.csv", index=False)

print("Aggregation complete. Saved as 'aggregated_motor_data.csv'.")
print("Learned parameters saved in 'learned_parameters.csv'.")

# Read the original data (make sure timestamp is parsed as datetime)
original_df = pd.read_csv(file, parse_dates=["timestamp"])

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
