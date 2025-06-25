import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta # For calculating the end of the month

# Ensure you have these libraries installed:
# pip install pandas python-dateutil

def load_prepayment_schedule(file_path: str) -> pd.DataFrame | None:
    """
    Loads the prepayment schedule from the CSV, handling its specific multi-row header.
    It identifies month columns and renames key columns for easier access.

    Args:
        file_path (str): Path to the CSV file. Expects headers like 'Items', 'Invoice number',
                         'Invoice amount', and month columns (e.g., 'Jan-24').

    Returns:
        pd.DataFrame | None: Processed DataFrame, or None on error.
    """
    try:
        # Read the CSV, skipping the first 2 header rows to get to the actual column names.
        df = pd.read_csv(file_path, skiprows=2)

        # Drop the last row if it's the "Balance" summary row.
        # Check if the first column of the last row is 'Balance' or similar.
        if df.iloc[-1, 0] == 'Balance':
            df = df.drop(df.tail(1).index)
            print("Note: Removed the 'Balance' summary row from the CSV data.")

        # Rename columns for clarity and consistency with the previous structure, if desired.

        df = df.rename(columns={
            'Items': 'Prepayment Item',
            'Invoice number': 'Reference',
            'Invoice amount': 'Total Amount' 
        })

        # --- START OF ADDITION FOR REFERENCE NUMBER ---
        if 'Reference' in df.columns:
            # Convert 'Reference' to numeric, coercing non-numeric values to NaN.
            df['Reference'] = pd.to_numeric(df['Reference'], errors='coerce')
            # Convert to Pandas' nullable integer type ('Int64') to handle NaNs and keep as whole numbers.
            df['Reference'] = df['Reference'].astype('Int64')
        else:
            print("Warning: 'Invoice number' (mapped to 'Reference') column not found.")
            df['Reference'] = 'N/A' # Default if column is missing
        # --- END OF ADDITION FOR REFERENCE NUMBER ---

        # Identify month columns dynamically.
        # Filter for columns that represent months, e.g., 'Jan-24', 'Feb-24'
        # Basic check: contains '-', length 6 (MMM-YY), first 3 chars are alphabetic
        month_columns = [
            col for col in df.columns
            if len(col) == 6 and '-' in col and col.split('-')[0].isalpha() and col.split('-')[1].isdigit()
        ]
        if not month_columns:
            print("Warning: No month columns (e.g., 'Jan-24') found in the CSV. Please check header format.")
            raise ValueError("Required month columns are missing in the CSV.")

        # Ensure numeric type for month columns and fill NaN with 0, as empty cells mean 0 amortization.
        for col in month_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Ensure 'Prepayment Item' and 'Reference' are present after renaming
        if 'Prepayment Item' not in df.columns:
            df['Prepayment Item'] = 'Generic Item'
            print("Note: 'Prepayment Item' column not found, defaulting to 'Generic Item'.")
        # The 'Reference' column handling is now above this point, so this check might be redundant if always present,
        # but kept for consistency with the user's provided structure.
        # if 'Reference' not in df.columns:
        #     df['Reference'] = 'N/A'
        #     print("Note: 'Reference' column not found, defaulting to 'N/A'.")

        print(f"Successfully loaded {len(df)} records from {file_path}")
        return df, month_columns # Return month columns too, as they define the data we need

    except FileNotFoundError:
        print(f"Error: The specified file '{file_path}' was not found. Please ensure the path is correct.")
        return None, None
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty or contains no data.")
        return None, None
    except ValueError as ve:
        print(f"Data parsing error: {ve}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred while loading or processing the CSV: {e}")
        return None, None


def generate_accounting_entries(schedule_df: pd.DataFrame, month_columns: list[str], target_month_str: str) -> list[dict]:
    """
    Generates accounting entries for prepaid items based on pre-calculated amounts in month columns.

    Args:
        schedule_df (pd.DataFrame): DataFrame containing the prepayment schedule with monthly amounts.
        month_columns (list[str]): List of column names that represent the months (e.g., 'Jan-24').
        target_month_str (str): The specific month for which to generate entries, in 'YYYY-MM' format
                                (e.g., '2024-05').

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an accounting entry.
                    Returns an empty list if no entries are generated or if the target_month_str is invalid.
    """
    entries = []

    try:
        # Convert the target_month_str (e.g., '2024-05') to a format matching CSV month headers (e.g., 'May-24').
        # First, parse to a datetime object.
        target_dt = datetime.strptime(target_month_str, '%Y-%m')
        # Then, format it to 'MMM-YY' (e.g., 'May-24').
        # Use %b for abbreviated month name (Jan, Feb, etc.) and %y for 2-digit year.
        target_month_col_name = target_dt.strftime('%b-%y')
    except ValueError:
        print(f"Error: Invalid target month format '{target_month_str}'. Please use 'YYYY-MM' (e.g., '2024-05').")
        return []

    # Get the last day of the target month for the accounting entry date.
    accounting_entry_date = target_dt + relativedelta(day=31)

    # Check if the target month column exists in the DataFrame.
    if target_month_col_name not in month_columns: 
        print(f"Warning: The month '{target_month_col_name}' is not found as a column in the input schedule. "
              f"No entries can be generated for this month.")
        return []

    # Iterate through each row (prepayment item) in the DataFrame.
    for index, row in schedule_df.iterrows():
        prepayment_item = row.get('Prepayment Item', 'Unknown Item')
        # --- START OF MODIFICATION FOR REFERENCE NUMBER ---
        raw_reference = row.get('Reference', pd.NA) # Get the reference, which is now Int64 or pd.NA
        # Convert to string: if it's a valid number, convert to int then string (e.g., 46248 -> '46248').
        # If it's pd.NA (missing/invalid), default to 'N/A'.
        reference_str = str(int(raw_reference)) if pd.notna(raw_reference) else 'N/A'
        # --- END OF MODIFICATION FOR REFERENCE NUMBER ---


        # Get the pre-calculated monthly amortization amount for the target month.
        # Use .get() with a default of 0 in case the column exists but has a NaN (should be handled by fillna above).
        monthly_amortization = row.get(target_month_col_name, 0)

        # Only generate entries if there's an actual amortization amount for this month.
        # We use a small epsilon for floating-point comparison, though round() helps.
        if abs(monthly_amortization) > 0.005: # Check if amount is significantly non-zero
            # The CSV shows negative amounts for amortization, so take the absolute value for the debit.
            debit_amount = abs(round(monthly_amortization, 2))

            # Entry 1: Debit (Increase) to an Expense Account
            entries.append({
                'Date': accounting_entry_date.strftime('%d/%m/%Y'), # Format as DD/MM/YYYY
                'Description': f'Prepayment amortisation for {prepayment_item}',
                'Reference': reference_str, # Use the string formatted reference
                'Account': 'EXP001', # Example expense account code
                'Amount': debit_amount
            })
            # Entry 2: Credit (Decrease) to a Prepayment Asset Account
            
            entries.append({
                'Date': accounting_entry_date.strftime('%d/%m/%Y'),
                'Description': f'Prepayment amortisation for {prepayment_item}',
                'Reference': reference_str, # Use the string formatted reference
                'Account': 'PRE001', # Example prepayment asset account code
                'Amount': -debit_amount # The credit amount will be negative of the debit amount to balance the entry.
            })
    return entries


def main():
    """
    Main function to orchestrate the prepayment automation process.
    Handles user interaction, calls data loading and entry generation functions,
    and manages the display and optional saving of the generated accounting entries.
    """
    csv_file_path = 'Prepayment assignment.csv'
    target_month_input = input("Enter the target month for amortization (YYYY-MM, e.g., 2024-05): ")

    # Load the prepayment schedule and get the list of month columns
    schedule_df, month_columns = load_prepayment_schedule(csv_file_path)

    if schedule_df is not None and month_columns is not None:
        print(f"\nAttempting to generate accounting entries for {target_month_input}...")
        accounting_entries = generate_accounting_entries(schedule_df, month_columns, target_month_input)

        if accounting_entries:
            # Convert the list of dictionaries into a pandas DataFrame for structured output.
            entries_df = pd.DataFrame(accounting_entries)

            # Define the desired order of columns for the output.
            output_columns = ['Date', 'Description', 'Reference', 'Account', 'Amount']
            entries_df = entries_df[output_columns]

            print("\n--- Generated Accounting Entries ---")
            print(entries_df.to_string(index=False)) # Print without pandas index

            # Optional: Save the output to a new CSV file.
            output_filename = f"accounting_entries_{target_month_input}.csv"
            try:
                entries_df.to_csv(output_filename, index=False)
                print(f"\nSuccessfully saved accounting entries to '{output_filename}'")
            except Exception as e:
                print(f"Error saving entries to CSV: {e}")
        else:
            print("No accounting entries generated for the specified month. "
                  "Check if amortization amounts exist for this period in the schedule or if the month format is correct.")
    else:
        print("\nCould not proceed with generating entries due to errors loading the prepayment schedule.")


if __name__ == "__main__":
    main()
