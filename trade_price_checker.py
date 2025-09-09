import pandas as pd
import zipfile

# Path to your ZIP files of symbol data lean data files (Please change the path as per your requirement)
lean_data_path = "C:/Users/ashish/Documents/Money_Face_Projects/Lean/Data"

# Create a dataframe from the CSV file (please change name of CSV file as per your requirement)
prices_df = pd.read_csv("trade_prices_bitcoin_strategy.csv")

# Method to get the symbol-price dataframe's dictionary
def get_symbol_price_df_dict(symbol_list):
    
    # Initialize the dictionary
    result_dict = {}
    
    # Iterate over the list of symbols
    for symbol in symbol_list:
        
        # Path to your ZIP file of symbol data
        zip_path = lean_data_path + f"/equity/usa/daily/{symbol.lower()}.zip"

        # Open the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as z:
            
            # Read the CSV file directly without extracting
            csv_filename = z.namelist()[0]  # Or specify exact name, e.g., "data.csv"
            df = pd.read_csv(z.open(csv_filename))
            
            # Convert the column names to lowercase and add dataframe to dictionary
            result_dict[symbol.lower()] = df
            
    return result_dict

# Get a list of unique symbols
symbols_list = list(set(prices_df['Symbol'].to_list()))

# Get the symbol-price dataframe's dictionary
df_dict = get_symbol_price_df_dict(symbols_list)

# Define a function to get the close price
def get_close_price(date, df):
    
    # Convert the dataframe to a string
    df.astype(str)
    
    # Filter the dataframe based on the date
    filtered_df = df[df.iloc[:,0] == date[0:4] + date[5:7] + date[8:10] + " 00:00"]
    
    # Get the price(s)
    price = filtered_df.iloc[0,4]
    
    # Convert the price to float and round it to 2 decimal places
    return float(round(price/10000,2))

# Define a function to get the open price
def get_open_price(date, df):
    
    # Convert the dataframe to a string
    df.astype(str)
    
    # Filter the dataframe based on the date
    filtered_df = df[df.iloc[:,0] == date[0:4] + date[5:7] + date[8:10] + " 00:00"]

    # Get the price(s)
    price = filtered_df.iloc[0,1]

    # Convert the price to float and round it to 2 decimal places
    return float(round(price / 10000,2))

# Initialize variables
total_count = 0
correct_count = 0

# Iterate over the dataframe
for index, row in prices_df.iterrows():
    
    # Convert the symbol to lowercase
    symbol = row['Symbol'].lower()

    # Get the direction
    direction = row['Direction']
    
    # Get the fill quantity and fill price
    fill_qty = row['FillQty']
    fill_price = row['FillPrice']
    
    # Get the date from the time column
    time = row['Time'][0:10]
    
    # Check if the direction is Buy or Sell
    if direction == "Buy":
    
        # Get the close price
        price = get_close_price(time, df_dict[symbol])
        
    # Check if the direction is Sell or Buy
    elif direction == "Sell":
    
        # Get the open price
        price = get_open_price(time, df_dict[symbol])
    
    # Increment the total count
    total_count += 1
    
    # Check if the fill price is equal to the price
    if round(fill_price, 2) == price:
        
        # Increment the correct count
        correct_count += 1
        
    else:
        
        # Print the fill price and close/open price
        print(f"Fill price: {fill_price}, Close/Open price: {price} did not matched for {symbol} on {time}")
    
# Print the percentage of correct fills
print(f"Percentage of correct fills: {correct_count / total_count * 100:.2f}%")

