# Prepayment Amortization Automation Script
This repository contains a Python script designed to automate the generation of accounting entries for prepaid items based on a provided schedule. This script addresses the technical assessment challenge from Backbone Pte. Ltd.

## Table of Contents
1. Project Description

2. Features

3. How to Run

4. Prerequisites

5. Input File

6. Execution Steps

7. Design Choices & Assumptions

8. Output

9. Potential Improvements

## 1. Project Description
The script automates the process of generating monthly accounting entries for prepayment amortization. Given a pre-calculated amortization schedule (in CSV format) and a target month, it extracts the relevant monthly expense amount for each item and generates the corresponding debit (expense) and credit (prepayment asset) entries.

## 2. Features
Reads prepayment schedule data from a specifically formatted CSV file (handling multi-row headers).

Dynamically identifies month columns in the input CSV.

Extracts pre-calculated monthly amortization amounts for a specified target month.

Ensures 'Reference' numbers are formatted as whole numbers in the output.

Generates two standard journal entries per amortized item: one debit to an expense account and one credit to a prepayment asset account.

Robust error handling for missing files, invalid month format input, and malformed data within the CSV.

Outputs generated entries to the console in a clear, tabular format.

Saves generated entries to a new, distinct CSV file for each month processed.

## 3. How to Run
### Prerequisites
Python 3.x (recommended 3.8+)

Required Python libraries: pandas, python-dateutil.
You can install them using pip:

pip install pandas python-dateutil

### Input File
The script expects an input CSV file named Prepayment assignment.csv in the same directory as the Python script.

The CSV file is expected to have a specific structure, with the actual headers starting from the third row. Key columns expected (after skipping initial rows) include:

Items: Represents the 'Prepayment Item' (e.g., "Webhosting", "Insurance").

Invoice number: Represents the 'Reference' number for the item.

Invoice amount: (Present in CSV, but its value is not used by the script for amortization calculation, as monthly amounts are pre-calculated).

Monthly columns: Columns in MMM-YY format (e.g., Jan-24, Feb-24, May-24), which contain the pre-calculated monthly amortization amounts. Empty cells in these columns are treated as 0.

### Execution Steps
Ensure Prepayment assignment.csv is in the same directory as prepayment_automation.py.

Open your terminal or command prompt.

Navigate to the directory where you saved the script.

Run the script using the following command:

python prepayment_automation.py

The script will prompt you to enter the target month for amortization in YYYY-MM format (e.g., 2024-05).

The generated accounting entries will be displayed in the console and saved to a new CSV file (e.g., accounting_entries_2024-05.csv).

To generate entries for a different month, simply run the script again as described in step 4. Each run will prompt for a new month and generate a new, distinct output CSV file, ensuring previous months' data is not overwritten.

## 4. Design Choices & Assumptions
Python & Pandas: Python was chosen for its strong capabilities in data manipulation and automation, leveraging the pandas library for efficient handling of tabular data.

CSV Structure Parsing: The load_prepayment_schedule function specifically handles the CSV's multi-row header (skiprows=2) and dynamically identifies the month-specific amortization columns. It also removes the summary 'Balance' row if present.

Pre-calculated Amortization: The script assumes that the monthly amortization amounts are already pre-calculated and provided directly in the monthly columns of the input CSV. It does not recalculate these based on an Invoice amount and a period.

Accounting Entry Date: As per the assessment requirement, the date for all accounting entries for a given target month is the last day of that month (e.g., 31/05/2024 for 2024-05). This is determined using dateutil.relativedelta.

Reference Number Formatting: The 'Invoice number' column (renamed to 'Reference') is explicitly converted to a nullable integer (Int64) during loading and then formatted as a clean string (without decimals) in the output. Non-numeric or missing values default to 'N/A'.

Account Codes: Each amortization generates a debit to EXP001 (Expense) and a credit to PRE001 (Prepayment Asset). These account codes are hardcoded for simplicity in this assessment.

Rounding: All monetary amounts are rounded to two decimal places to ensure financial accuracy.

Error Handling: Comprehensive try-except blocks are implemented to manage FileNotFoundError, ValueError (for invalid month input or missing critical columns/data), and other general exceptions, providing informative messages to the user.

Output Management: Output is displayed on the console and saved to a uniquely named CSV file for each run, ensuring results for different months are preserved.

## 5. Output
The script will print a summary of the generated entries to the console. Additionally, a new CSV file named accounting_entries_YYYY-MM.csv (where YYYY-MM is the input target month) will be created in the same directory, containing the following columns:

Date: The last day of the target month (e.g., "31/05/2024").

Description: "Prepayment amortisation for [Prepayment Item Name]".

Reference: The invoice number/reference for the item (as a whole number or 'N/A').

Account: Either "EXP001" (for debit) or "PRE001" (for credit).

Amount: The monthly amortization amount (positive for debit, negative for credit).

## 6. Potential Improvements
Dynamic Account Code Mapping: Implement a mechanism (e.g., via a separate configuration file or lookup table) to map Prepayment Item types to specific expense and asset account codes, rather than using hardcoded EXP001 and PRE001.

Command-Line Arguments: Enhance user interaction by utilizing Python's argparse module to allow the input CSV path and target month to be passed as command-line arguments, facilitating easier integration into automated workflows.

Robust Date Parsing for Month Columns: While current dynamic identification works for MMM-YY, adding more flexible regex or date parsing logic could handle variations like MM-YYYY or MMM YYYY if expected in future inputs.

# backbone-prepayment-assessment
