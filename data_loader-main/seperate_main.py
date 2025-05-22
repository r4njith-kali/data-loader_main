import pandas as pd

def split_csv_by_cell():
    # Ask user for the CSV file name
    file_name = input("Enter the name of the CSV file (including .csv extension): ")

    try:
        # Load the CSV file
        df = pd.read_csv(file_name)

        # Check if 'cell' column exists
        if "cell" not in df.columns:
            print("Error: 'cell' column not found in the file. Please check the data.")
            return
        
        # Find all unique values in the 'cell' column
        unique_cells = df["cell"].unique()

        # Loop through each unique cell value and save corresponding data
        for cell_value in unique_cells:
            cell_df = df[df["cell"] == cell_value]
            output_file = f"{file_name.replace('.csv', '')}_{cell_value}.csv"
            cell_df.to_csv(output_file, index=False)
            print(f"Created: {output_file}")

        print("\nCSV files successfully created for all distinct cell values!")

    except FileNotFoundError:
        print("Error: File not found. Please check the file name and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
split_csv_by_cell()
