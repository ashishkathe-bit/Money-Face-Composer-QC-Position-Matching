
from AlgorithmImports import *
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import os
from io import StringIO
import csv
from QuantConnect.Orders.Fills import ImmediateFillModel
import time as tm
from datetime import datetime
from datetime import datetime, timedelta
from QuantConnect.Orders.Fees import FeeModel

from QuantConnect import Resolution
from QuantConnect.Securities import NullBuyingPowerModel
from QuantConnect.Securities.Positions import SecurityPositionGroupModel
import sys, os, signal, faulthandler


# -------- Fee Models --------
# Per order fee custom classes definitions (do not manipulate it)
class PerOrderFeeModel(FeeModel):
    """Fixed fee per order, regardless of size."""
    def __init__(self, fee: float = 1.0):
        self.fee = float(fee)

    def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
        security = parameters.Security
        return OrderFee(CashAmount(self.fee, security.QuoteCurrency.Symbol))

# Per share fee custom classes definitions (do not manipulate it)
class PerShareFeeModel(FeeModel):
    """Fee = fee_per_share * quantity traded."""
    def __init__(self, fee_per_share: float = 0.005):
        self.fee_per_share = float(fee_per_share)

    def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
        security = parameters.Security
        order = parameters.Order
        quantity = abs(order.AbsoluteQuantity)   
        fee_amount = self.fee_per_share * quantity
        return OrderFee(CashAmount(fee_amount, security.QuoteCurrency.Symbol))

# Percentage fee model custom classes definitions (do not manipulate it)
class PercentageFeeModel(FeeModel):
    """Fee = percentage_of_trade_value * |trade value|."""
    def __init__(self, rate: float = 0.0005):
        if rate < 0 or rate > 1:
            raise ValueError("Percentage fee must be between 0 and 1")
        self.rate = float(rate)

    def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
        security = parameters.Security
        order = parameters.Order
        trade_value_quote = abs(order.GetValue(security))  # in quote currency
        fee_amount = trade_value_quote * self.rate
        return OrderFee(CashAmount(fee_amount, security.QuoteCurrency.Symbol))


# -------- Slippage Models --------
# Fixed slippage model custom classes definitions (do not manipulate it)
class FixedSlippageModel:
    """Fixed slippage model."""
    def __init__(self, value: float = 0.01):
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        return self.value
    
# Percentage slippage model custom classes definitions (do not manipulate it)
class PercentageSlippageModel:
    """Percentage slippage model."""
    def __init__(self, value: float = 0.0005):
        if not (0 <= value <= 1):
            raise ValueError("Percentage slippage must be between 0 and 1")
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        return asset.Price * self.value

# Volume impact slippage model custom classes definitions (do not manipulate it)

class VolumeImpactSlippageModel:
    """Volume impact slippage model."""
    def __init__(self, value: float = 0.1):
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        vol = max(asset.Volume, 1)
        qty = abs(order.AbsoluteQuantity)
        return asset.Price * self.value * (qty / vol)

class PositionSimulation(QCAlgorithm):
    '''
    Position Simulation Class
    '''

    def initialize(self):
        
        # Initialize empty list
        self._pos_rows = []
        
        # Flag for first day
        self.first_day_flag = True
        
        # Read psotion data of stratgey
        self.df = pd.read_csv("Bitcoin.csv")
        
        # Drop row at index 0
        self.df = self.df.drop(0) 
        
        # Convert date colum to datetime type
        self.df["Date"] = pd.to_datetime(self.df["Date"])
        
        # Preserve only date field of datetime 
        self.df["Date"] = self.df["Date"].dt.date
        
        # Get sorted unique dates from positions dataframe
        self.csv_dates = np.array(sorted(self.df["Date"].unique()))

        # Set initial capital
        self.SetCash(100000.0)
        
        # Set start date of backteest
        self.startdate = datetime.strptime('2022-07-06', '%Y-%m-%d')
        
        # Set backtest start date
        self.SetStartDate(self.startdate)

        # Set backtest end date
        self.SetEndDate(datetime.strptime('2025-08-27', '%Y-%m-%d'))
        
        # Set custom transaction fees
        # Set percentage-based fees
        fee_model = PercentageFeeModel(0.000)
        
        # Set slippage model
        slippage_model = PercentageSlippageModel(0.000)
        
        # wrap brokerage defaults + fee model + slippage model
        def init_sec(security: Security):
            security.SetFeeModel(fee_model)
            security.SetSlippageModel(slippage_model)
        
        # Run security initializer method to set fee and slippage model
        self.SetSecurityInitializer(init_sec)

        # Initialize empty list
        self.ticker_done_list = []

        # Spy symbol object(do not manipulate)
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Add securities to universe and store symbol references (to be change when strategy change)
        self.spy_symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.mstr_symbol = self.AddEquity("MSTR", Resolution.Daily).Symbol
        self.bito_symbol = self.AddEquity("BITO", Resolution.Daily).Symbol
        self.biti_symbol = self.AddEquity("BITI", Resolution.Daily).Symbol
        self.bsv_symbol = self.AddEquity("BSV", Resolution.Daily).Symbol
        self.tbt_symbol = self.AddEquity("TBT", Resolution.Daily).Symbol
        
        # Add equity objects for all tickers (to be change when strategy change)
        self.spy_eq = self.AddEquity("SPY", Resolution.Daily)
        self.mstr_eq = self.AddEquity("MSTR", Resolution.Daily)
        self.bito_eq = self.AddEquity("BITO", Resolution.Daily)
        self.biti_eq = self.AddEquity("BITI", Resolution.Daily)
        self.bsv_eq = self.AddEquity("BSV", Resolution.Daily)
        self.tbt_eq = self.AddEquity("TBT", Resolution.Daily)
        
        # Disable buying power checks for this security (to be change when strategy change)
        self.spy_eq.SetBuyingPowerModel(NullBuyingPowerModel())
        self.mstr_eq.SetBuyingPowerModel(NullBuyingPowerModel())
        self.bito_eq.SetBuyingPowerModel(NullBuyingPowerModel())
        self.biti_eq.SetBuyingPowerModel(NullBuyingPowerModel())
        self.bsv_eq.SetBuyingPowerModel(NullBuyingPowerModel())
        self.tbt_eq.SetBuyingPowerModel(NullBuyingPowerModel())

        self.trade_prices_df_columns = ['Symbol', 'Direction', 'FillQty', 'FillPrice', 'Time']

        self.trade_prices_df = pd.DataFrame(columns=self.trade_prices_df_columns)

        # If you use position groups (e.g., options), also disable group-level checks
        self.Portfolio.SetPositions(SecurityPositionGroupModel.NULL)

        # List of all symbols in strategy (to be change when strategy change)
        self.symbols = ['SPY', 'MSTR', 'BITO', 'BITI', 'BSV', 'TBT']        # Initialize indicators with automatic warm-up support
        self.settings.automatic_indicator_warm_up = True


        # Indicator Definitions for strategy (to be change when strategy change)
        self.spy_current_price = self.identity('SPY')
        self.spy_sma_200 = self.sma('SPY', 200)
        self.bito_current_price = self.identity('BITO')
        self.bito_sma_15 = self.sma('BITO', 15)
        self.biti_rsi_10 = self.rsi('BITI', 10)
        self.bsv_rsi_10 = self.rsi('BSV', 10)
        self.tbt_rsi_10 = self.rsi('TBT', 10)
        self.bito_rsi_10 = self.rsi('BITO', 10)
    
        # SEt execution model
        self.SetExecution(ImmediateExecutionModel())

        # Initialize dates list
        self.dates_list = []
        
        # Create empty dataframe for storing results
        self.result_df = pd.DataFrame(columns=[
            "date","symbol","quantity","avg_price","market_price",
            "holding_value","unrealized_pnl","portfolio_value","cash", "Percentage"
        ])
        self.close_price = pd.read_csv("next_day_close_prices.csv", parse_dates=['Date'])
        self.open_price = pd.read_csv("next_day_open_prices.csv", parse_dates=['Date'])
        # Initialize empty dictionary
        self.map_dict = {}
        self.exit_today = False
        self.prices_df = pd.DataFrame(columns=["Date"] + self.symbols)
        self.portfolio_value = 0

    # This gets invoked when order gets filled
    def OnOrderEvent(self, e):
        if e.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {e.Symbol} - {e.Direction} {e.FillQuantity} @ {e.FillPrice} at {self.time}")
            
            row = [[e.Symbol, e.Direction, e.FillQuantity, e.FillPrice, self.time]]
            
            temp_price_df = pd.DataFrame(row, columns=self.trade_prices_df_columns)
            

            self.trade_prices_df = pd.concat([self.trade_prices_df, temp_price_df], ignore_index=True)
            
            self.trade_prices_df.to_csv("aa_prices.csv", index=False)

    # Method to get next and next to next date
    def _next_two_csv_dates(self, today):
        i = np.searchsorted(self.csv_dates, today, side="right")  # strictly after today
        if i >= len(self.csv_dates):
            return None, None
        d1 = self.csv_dates[i]
        d2 = self.csv_dates[i+1] if i+1 < len(self.csv_dates) else None
        
        return d1, d2

    def OnData(self, data: Slice) -> None:
        '''Main algorithm logic executed on each data point'''
        
        # Get assume dcurrent date 
        current_date = self.Time
        
        # Get string version of current date
        current_date = current_date.strftime('%Y-%m-%d')
        
        # Get dataframe filter condition
        current_daytemp_df_condition = self.df['Date'].astype(str) == current_date
            
        # Apply dataframe filter condition
        current_daytemp_df = self.df[current_daytemp_df_condition]
        
        # If date is equal to start date then have empty row otherwise row of filtered df
        if self.first_day_flag:
            
            current_day_row = pd.Series()
        
        else:
        
            current_day_row = current_daytemp_df.iloc[0]
        
        # Get next date and next to next date
        next_date, next_to_next_date = self._next_two_csv_dates(self.Time.date())
        
        if next_date is None:
            
            return

        # convert dates into string format
        next_date = next_date.strftime('%Y-%m-%d')

        # GEt filtered df for assumed current day
        next_date_temp_df_condition = self.df['Date'].astype(str) == next_date
        next_date_temp_df = self.df[next_date_temp_df_condition]
        
        # Get row for assumed current day
        next_day_row = next_date_temp_df.iloc[0]
        
        # Get columns with non zero values
        next_day_cols = next_day_row.index[~next_day_row.astype(str).str.strip().isin({'-', '0.00%'})].tolist()[2:]
        
        # Get columns with non zero values
        current_day_cols = current_day_row.index[~current_day_row.astype(str).str.strip().isin({'-', '0.00%'})].tolist()[2:]
            
        # Get value for assumed current day traded
        if next_day_cols == current_day_cols:
            
            day_traded = "No"
            
        else:
            
            day_traded = "Yes"
        
        
        # Always set day trade to yes for first day
        if self.first_day_flag:
            
            day_traded = "Yes"
            
            
            self.first_day_flag = False
                    
        # Close position if assumed next day close positions
        if day_traded in ["Yes"]:        
            self.portfolio_value = 0
            for kvp in self.Portfolio:  # kvp.Key = Symbol, kvp.Value = SecurityHolding
                sym = kvp.Key
                h = kvp.Value
                # self.debug(f"{str(sym)=}, {h.Invested=}, {h.HoldingsValue=}, {h.Quantity=}")
                if not h.Invested and abs(h.Quantity) == 0:
                    
                    continue
                
                # Close position if ticker is invested
                exit_price = float(self.open_price[self.open_price['Date'].astype(str) == str(self.Time.date())][str(sym)].values[0])
                self.market_on_open_order(str(sym), -h.Quantity)
                self.portfolio_value += h.Quantity * exit_price
                self.debug(f"Placed order to liquidate {sym} ({h.Quantity} @ {exit_price})")

            if self.portfolio_value == 0:
                self.portfolio_value = self.Portfolio.TotalPortfolioValue
            else:
                self.exit_today = True
                self.portfolio_value += self.Portfolio.Cash
                
        # Take trade if assume current day needs to get position
        if day_traded in ["Yes"]:
                
            self.map_dict = {}

            # Get symbols for non zero values
            list_of_symbols_with_positions = next_day_cols
                        
            # Remove $USD values
            if "$USD" in list_of_symbols_with_positions:
            
                list_of_symbols_with_positions.remove("$USD")

            # Get portfolio value
            total = float(self.Portfolio.TotalPortfolioValue)

            # Iterate symbols            
            for symbol in list_of_symbols_with_positions:
                
                price = float(self.close_price[self.close_price['Date'].astype(str) == str(self.Time.date())][symbol].values[0])
                allocation = self.get_float_val(next_day_row[symbol])

                # Calculate quantity
                qty = (self.portfolio_value * allocation) / price
                
                # place market order
                ticker = self.market_on_close_order(symbol, qty)
                self.debug(f"Placed market order for {ticker.Symbol} - {ticker.Quantity} @ {price}")
                
    # Update positions in datafrmae
    def update_results_to_df(self):
        
        # Algorithm time is in the algo timezone.
        date = self.Time.strftime("%Y-%m-%d")
        total = float(self.Portfolio.TotalPortfolioValue)
        cash = float(self.Portfolio.Cash)
        
        # Get QuantConnect's values for reference
        qc_total_portfolio_value = float(self.Portfolio.TotalPortfolioValue)
        
        # Calculate our own portfolio base for percentage calculations
        total_absolute_exposure = 0.0
        
        # Create empty list of temporary rows
        temp_rows = []
        
        # First pass: Calculate total absolute exposure
        for kvp in self.Portfolio:
            sym = kvp.Key
            h = kvp.Value
            if not h.Invested and abs(h.Quantity) == 0:
                continue
            if str(sym) in self.ticker_done_list:
                continue
                
            sec = self.Securities[sym]
            multiplier = float(sec.SymbolProperties.ContractMultiplier)
            current_exposure = abs(float(h.Quantity)) * float(sec.Price) * multiplier
            total_absolute_exposure += current_exposure
        
        # Determine the appropriate base for percentage calculations
        # Use the larger of: total absolute exposure or absolute value of QC portfolio value
        portfolio_base = max(total_absolute_exposure, abs(qc_total_portfolio_value))
        
        # If cash is positive and larger than our exposures, use QC's calculation
        if cash > 0 and qc_total_portfolio_value > total_absolute_exposure:
            portfolio_base = qc_total_portfolio_value
        
        # record all invested holdings
        for kvp in self.Portfolio:  
            
            # Get symbol and object for all symbols records
            sym = kvp.Key
            h = kvp.Value
            
            # If symbol not invested then skip it
            if not h.Invested and abs(h.Quantity) == 0:
                
                continue
            
            # Get unrealised pnl 
            sec = self.Securities[sym]
            multiplier = float(sec.SymbolProperties.ContractMultiplier)
            upnl = float((sec.Price - h.AveragePrice) * h.Quantity * multiplier)
            
            # Current Exposure = Current Shares * Current Price
            current_exposure = abs(float(h.Quantity)) * float(sec.Price) * multiplier
            
            # FIXED PERCENTAGE: Current Exposure / Portfolio Base * 100
            position_percentage = round((current_exposure / portfolio_base) * 100, 2)
            
            # Append rows in list for creatiing temporray datafrma which will be concatenated with all dates dataframe
            temp_rows.append([
                date, str(sym), float(h.Quantity), float(h.AveragePrice),
                float(sec.Price), float(h.HoldingsValue), upnl, portfolio_base, cash, position_percentage
            ])
            
        # Update dataframe for invested holdings
        headers = [
            "date","symbol","quantity","avg_price","market_price",
            "holding_value","unrealized_pnl","portfolio_value","cash", "Percentage"
        ]
        
        # Create temporary dataframe for one date
        temp_row_df = pd.DataFrame(columns=headers, data=temp_rows)
        
        # Concatenate dataframes of all dates and current date to get updated dataframe
        self.result_df = pd.concat([self.result_df, temp_row_df], ignore_index=True)
        
        # Save Datafrmae to storage
        self.result_df.to_csv("a_daily_positions_pd.csv", index=False)
                
    def OnEndOfDay(self):
        
        # Update and write latest positions data csv file
        self.update_results_to_df()

    def OnEndOfAlgorithm(self):
        
        pass

    # Method to strip % symbol and get percentage value in decimal
    def get_float_val(self, value):
        
        # Get float value without % sign
        return float(value.strip().rstrip('%')) / 100 
