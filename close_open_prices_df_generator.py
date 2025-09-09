import csv
import pandas as pd
from datetime import datetime
import os
import zipfile
def parse_price_date(date_str):
    """Convert price file date format (YYYYMMDD HH:MM) to YYYY-MM-DD"""
    try:
        # Remove time part and parse date
        date_part = date_str.split(' ')[0]
        parsed_date = datetime.strptime(date_part, '%Y%m%d')
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return None

def format_price(price):
    """Convert price to float by dividing by 10000"""
    # Simply divide by 10000 and return as float
    return price / 10000

def load_symbol_prices(symbol):
    """Load price data for a specific symbol - returns both open and close prices"""
    
    
    try:
        
        # Path to your ZIP file
        zip_path = f"C:/Users/ashish/Documents/Money_Face_Projects/Lean/Data/equity/usa/daily/{symbol.lower()}.zip"

        # Open the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as z:
            # List all files inside the ZIP
            print(z.namelist())  # Optional: see available files

            # Read the CSV file directly without extracting
            csv_filename = z.namelist()[0]  # Or specify exact name, e.g., "data.csv"
            df = pd.read_csv(z.open(csv_filename), header=None)
            
        
        # Read price file (assuming no headers: Date, Open, High, Low, Close, Volume)
        # df = pd.read_csv(price_file, header=None)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Convert dates and create price dictionaries
        open_price_data = {}
        close_price_data = {}
        dates_list = []
        
        for _, row in df.iterrows():
            original_date = str(row['Date'])
            converted_date = parse_price_date(original_date)
            
            if converted_date:
                open_price = row['Open']
                close_price = row['Close']
                open_price_data[converted_date] = open_price
                close_price_data[converted_date] = close_price
                dates_list.append(converted_date)
        
        # Sort dates chronologically
        dates_list = sorted(dates_list)
        
        print(f"Loaded {len(dates_list)} price records for {symbol}")
        return open_price_data, close_price_data, dates_list
    
    except Exception as e:
        print(f"Error loading {price_file}: {e}")
        return {}, {}, []

def create_next_day_prices_csv(symbols, close_output_file, open_output_file):
    """
    Create CSV files where each row shows next day's prices
    
    Args:
        symbols (list): List of symbol names
        close_output_file (str): Path to output CSV file for close prices
        open_output_file (str): Path to output CSV file for open prices
    """
    
    print("=" * 60)
    print("NEXT-DAY PRICES CSV GENERATOR")
    print("=" * 60)
    
    # Load all symbol data
    all_open_price_data = {}
    all_close_price_data = {}
    all_dates_lists = {}
    
    for symbol in symbols:
        open_price_data, close_price_data, dates_list = load_symbol_prices(symbol)
        all_open_price_data[symbol] = open_price_data
        all_close_price_data[symbol] = close_price_data
        all_dates_lists[symbol] = dates_list
    
    # Find common dates where all symbols have data
    common_dates = None
    for symbol in symbols:
        symbol_dates = set(all_dates_lists[symbol])
        if common_dates is None:
            common_dates = symbol_dates
        else:
            common_dates = common_dates.intersection(symbol_dates)
    
    if not common_dates:
        print("Error: No common dates found across all symbols")
        return
    
    common_dates = sorted(common_dates)
    print(f"Found {len(common_dates)} common dates across all symbols")
    
    # Create next-day price data for both open and close
    next_day_close_data = []
    next_day_open_data = []
    
    for i, current_date in enumerate(common_dates[:-1]):  # Exclude last date (no next day)
        next_date = common_dates[i + 1]
        
        # Get next day's close prices for all symbols
        close_row_data = {'Date': current_date}
        open_row_data = {'Date': current_date}
        
        all_symbols_have_next_day = True
        for symbol in symbols:
            if next_date in all_close_price_data[symbol] and next_date in all_open_price_data[symbol]:
                # Close prices
                next_day_close_price = all_close_price_data[symbol][next_date]
                float_close_price = format_price(next_day_close_price)
                close_row_data[symbol] = float_close_price
                
                # Open prices
                next_day_open_price = all_open_price_data[symbol][next_date]
                float_open_price = format_price(next_day_open_price)
                open_row_data[symbol] = float_open_price
            else:
                all_symbols_have_next_day = False
                break
        
        # Only add row if all symbols have next day data
        if all_symbols_have_next_day:
            next_day_close_data.append(close_row_data)
            next_day_open_data.append(open_row_data)
    
    if not next_day_close_data:
        print("Error: No valid next-day price data found")
        return
    
    # Create DataFrames and export to CSV
    # Reorder columns: Date first, then symbols in alphabetical order
    ordered_columns = ['Date'] + sorted(symbols)
    
    # Close prices CSV
    close_df = pd.DataFrame(next_day_close_data)
    close_df = close_df[ordered_columns]
    close_df.to_csv(close_output_file, index=False)
    
    # Open prices CSV
    open_df = pd.DataFrame(next_day_open_data)
    open_df = open_df[ordered_columns]
    open_df.to_csv(open_output_file, index=False)
    
    print("=" * 60)
    print("NEXT-DAY PRICES CSV COMPLETED!")
    print("=" * 60)
    print(f"Close prices output file: {close_output_file}")
    print(f"Open prices output file: {open_output_file}")
    print(f"Rows created: {len(next_day_close_data)}")
    print(f"Symbols included: {', '.join(sorted(symbols))}")
    print()
    print("CSV Format:")
    print("  • Each row date shows NEXT day's prices")
    print("  • Example: July 6th row contains July 7th's prices")
    print("  • Prices are normalized (divided by 10,000)")
    print("  • Formatted with minimum 2 decimal places")
    print()
    print("Sample close prices data:")
    print(close_df.head().to_string(index=False))
    print()
    print("Sample open prices data:")
    print(open_df.head().to_string(index=False))

def main():
    """Main function"""
    
    # Get all files in Composer Positions Files folder
    file_name_list = os.listdir("Composer Positions Files")
    
    # Iterate through all files
    for file_name in file_name_list:
                
        # Read CSV file
        df = pd.read_csv(f"Composer Positions Files\{file_name}", sep=',', header=0)
        
        # Get columns of the dataframe
        columns = list(df.columns)
        
        # Remove Date, Day Traded and $USD columns
        columns.remove('Date')
        columns.remove('Day Traded')
        columns.remove('$USD')
        
        # Remove Cash column if present
        if 'Cash' in columns:
        
            columns.remove('Cash')
        
        # Define symbols based on available CSV files
        symbols = columns
        close_output_file = f'Next Day Close Prices And Open Prices/next_day_close_prices_{file_name[0:-4]}.csv'
        open_output_file = f'Next Day Close Prices And Open Prices/next_day_open_prices_{file_name[0:-4]}.csv'
        
        
        
        try:
            create_next_day_prices_csv(symbols, close_output_file, open_output_file)
            
            print()
            print("Usage:")
            print("- Each row shows what tomorrow's prices will be")
            print("- Close prices CSV: Perfect for end-of-day backtesting")
            print("- Open prices CSV: Perfect for next-day entry strategies")
            print("- Load these CSVs to know future prices for any given date")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()   

if __name__ == "__main__":
    main()