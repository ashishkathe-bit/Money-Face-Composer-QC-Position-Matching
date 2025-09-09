import csv
import pandas as pd
from collections import defaultdict

def convert_csv_format(input_file, reference_file, output_file):
    """
    Convert QC format to reference format by extracting symbols from reference file
    
    Args:
        input_file (str): Path to input CSV file (QC format)
        reference_file (str): Path to reference CSV file to extract symbols and format from
        output_file (str): Path to output CSV file
    """
    
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Extract only the columns we need: date, symbol, Percentage
    df = df[['date', 'symbol', 'Percentage']].copy()
    
    # Group by date and create a dictionary of symbol allocations
    date_allocations = defaultdict(dict)
    
    for _, row in df.iterrows():
        date = row['date']
        symbol = row['symbol']
        percentage = row['Percentage']
        
        # Format percentage to match target format (e.g., "100.0%")
        if pd.notna(percentage):
            formatted_percentage = f"{percentage:.1f}%"
        else:
            formatted_percentage = "0"
            
        date_allocations[date][symbol] = formatted_percentage
    
    # Extract symbols from reference file headers
    with open(reference_file, 'r', encoding='utf-8') as ref_file:
        ref_reader = csv.reader(ref_file)
        ref_headers = next(ref_reader)  # Read first row (headers)
        
    # Remove quotes from headers and manually exclude non-symbol columns
    cleaned_headers = [header.strip('"') for header in ref_headers]
    
    # Define non-symbol columns to exclude (these are standard columns, not asset symbols)
    non_symbol_columns = ["Date", "Day Traded", "$USD", "Cash"]
    
    # Extract only symbol columns (exclude the standard non-symbol columns)
    target_symbols = [header for header in cleaned_headers if header not in non_symbol_columns]
    
    # Extract Day Traded value from reference file
    with open(reference_file, 'r', encoding='utf-8') as ref_file:
        ref_reader = csv.reader(ref_file)
        next(ref_reader)  # Skip header
        next(ref_reader)  # Skip asset type row
        first_data_row = next(ref_reader)  # Read first data row
        day_traded_value = first_data_row[1].strip('"')  # Get Day Traded value
    
    # Create the output data structure
    output_data = []
    
    # Header row
    header = ["Date", "Day Traded", "$USD"] + target_symbols
    output_data.append(header)
    
    # Asset type row
    asset_types = ["Asset Type", "", "Cash"] + ["Equity"] * len(target_symbols)
    output_data.append(asset_types)
    
    # Sort dates in descending order (newest first, matching target format)
    sorted_dates = sorted(date_allocations.keys(), reverse=True)
    
    # Data rows
    for date in sorted_dates:
        row = [str(date), day_traded_value, "0"]  # Date with quotes, Day Traded from reference, USD as "0"
        
        # Add symbol allocations or "0" if not present
        for symbol in target_symbols:
            if symbol in date_allocations[date]:
                row.append(date_allocations[date][symbol])
            else:
                row.append("0")
        
        output_data.append(row)
    
    # Write to output CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for row in output_data:
            writer.writerow(row)
    
    print(f"Conversion completed! Output saved to: {output_file}")
    print(f"Total dates processed: {len(sorted_dates)}")

if __name__ == "__main__":
    # File paths - Update these as needed
    input_file = "QC_generated_positions.csv"  # QC file to convert
    reference_file = "Bitcoin_ref.csv"  # Reference file for format
    output_file = "converted_QC_generated_positions.csv"  # Output file

    try:
        convert_csv_format(input_file, reference_file, output_file)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")