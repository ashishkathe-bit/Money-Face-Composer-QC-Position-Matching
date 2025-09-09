"""
Universe Generator Module

Handles generation of universe setup code for QuantConnect Lean algorithms.
"""

import re
from typing import Dict, List, Any, Optional


class UniverseGenerator:
    """Generates universe setup and related algorithm initialization code."""
    
    def generate_class_name(self, strategy_name: str) -> str:
        """Generate a valid Python class name from strategy name."""
        # Remove special characters and convert to PascalCase
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', strategy_name)
        words = cleaned.split()
        
        # Capitalize each word and join
        class_name = ''.join(word.capitalize() for word in words if word)
        
        # Handle empty or invalid class names
        if not class_name:
            class_name = 'GeneratedStrategy'
        elif not class_name[0].isalpha():
            class_name = 'Strategy' + class_name
        
        return class_name
    
    def generate_date_setup(self, settings: Dict[str, Any], metrics_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate date setup code."""
        # Use metrics data for default dates if available
        default_start = '2020-01-01'
        default_end = None
        if metrics_data and 'backtest_start_date' in metrics_data:
            default_start = metrics_data['backtest_start_date']
        if metrics_data and 'backtest_end_date' in metrics_data:
            default_end = metrics_data['backtest_end_date']
            
        start_date = settings.get('start', default_start)
        end_date = settings.get('end', default_end)
        
        lines = []
        
        # Parse and format start date
        try:
            start_parts = start_date.split('-')
            if len(start_parts) == 3:
                year = int(start_parts[0])
                month = int(start_parts[1])
                day = int(start_parts[2])
                lines.append(f"        self.SetStartDate({year}, {month}, {day})")
            else:
                lines.append(f"        self.SetStartDate(2020, 1, 1)  # Default start date")
        except:
            lines.append(f"        self.SetStartDate(2020, 1, 1)  # Default start date")
        
        # Parse and format end date if provided
        if end_date:
            try:
                end_parts = end_date.split('-')
                if len(end_parts) == 3:
                    year = int(end_parts[0])
                    month = int(end_parts[1])
                    day = int(end_parts[2])
                    lines.append(f"        self.SetEndDate({year}, {month}, {day})")
            except:
                lines.append(f"        # End date parsing failed: {end_date}")
        
        return '\n'.join(lines) if lines else "        self.SetStartDate(2020, 1, 1)"
    
    def generate_cash_setup(self, settings: Dict[str, Any]) -> str:
        """Generate cash setup code."""
        capital = settings.get('capital', 100000)
        return f"        self.SetCash({capital})"
    
    def generate_benchmark_setup(self, settings: Dict[str, Any]) -> str:
        """Generate benchmark setup code."""
        benchmark = settings.get('benchmark', 'SPY')
        return f'        self.SetBenchmark("{benchmark}")'
    
    def generate_universe_setup(self, universe: List[Dict[str, Any]]) -> str:
        """Generate universe setup code."""
        lines = []
        lines.append("        # Add securities to universe and store symbol references")
        
        symbol_storage_lines = []
        
        symbols_list = []
        
        for asset in universe:
            symbol = asset.get('symbol', '')
            asset_class = asset.get('assetClass', 'EQUITY').upper()
            clean_symbol = symbol.lower().replace('-', '_')
            
            symbols_list.append(symbol)
            
            if asset_class == 'EQUITY':
                lines.append(f'        self.{clean_symbol}_symbol = self.AddEquity("{symbol}", Resolution.Daily).Symbol')
                symbol_storage_lines.append(f'            self.{clean_symbol}_symbol,')
            elif asset_class == 'ETF':
                lines.append(f'        self.{clean_symbol}_symbol = self.AddEquity("{symbol}", Resolution.Daily).Symbol')
                symbol_storage_lines.append(f'            self.{clean_symbol}_symbol,')
            elif asset_class == 'FOREX':
                lines.append(f'        self.{clean_symbol}_symbol = self.AddForex("{symbol}", Resolution.Daily).Symbol')
                symbol_storage_lines.append(f'            self.{clean_symbol}_symbol,')
            elif asset_class == 'CRYPTO':
                lines.append(f'        self.{clean_symbol}_symbol = self.AddCrypto("{symbol}", Resolution.Daily).Symbol')
                symbol_storage_lines.append(f'            self.{clean_symbol}_symbol,')
            elif asset_class == 'FUTURE':
                lines.append(f'        # Future: {symbol} - Manual setup required')
                # lines.append(f'        # self.{clean_symbol}_symbol = self.AddFuture("{symbol}", Resolution.Daily).Symbol')
            elif asset_class == 'OPTION':
                lines.append(f'        # Option: {symbol} - Manual setup required')
                # lines.append(f'        # self.{clean_symbol}_symbol = self.AddOption("{symbol}", Resolution.Daily).Symbol')
            else:
                lines.append(f'        self.{clean_symbol}_symbol = self.AddEquity("{symbol}", Resolution.Daily).Symbol  # Default to equity')
                symbol_storage_lines.append(f'            self.{clean_symbol}_symbol,')
        
        # Symbol storage removed as it was unused
        
        return '\n'.join(lines), symbols_list
    
    def generate_rebalance_schedule(self, settings: Dict[str, Any]) -> str:
        """Generate rebalance schedule code."""
        rebalance = settings.get('rebalance', 'none')
        
        if rebalance == 'daily':
            return "        self.schedule.on(self.date_rules.every_day('SPY'), self.time_rules.after_market_open('SPY', 1), self.rebalance)"
        elif rebalance == 'weekly':
            return "        self.schedule.on(self.date_rules.week_start('SPY'), self.time_rules.after_market_open('SPY', 1), self.rebalance)"
        elif rebalance == 'monthly':
            return "        self.schedule.on(self.date_rules.month_start('SPY'), self.time_rules.after_market_open('SPY', 1), self.rebalance)"
        elif rebalance == 'quarterly':
            return "        self.schedule.on(self.date_rules.month_start('SPY'), self.time_rules.after_market_open('SPY', 1), self.rebalance)  # Quarterly rebalancing: check month in rebalance method"
        else:
            return "        # No rebalance schedule set"
    
    def generate_fee_setup(self, settings: Dict[str, Any]) -> str:
        """Generate fee model setup code."""
        fees = settings.get('fees', {})
        
        if not fees:
            return "        # Using default fee model"
        
        # Simple fee model generation - could be enhanced
        if 'percentage' in fees:
            percentage = fees['percentage']
            return f"        self.SetSecurityInitializer(lambda security: security.SetFeeModel(ConstantFeeModel({percentage})))"
        else:
            return "        # Using default fee model"
    
    def generate_slippage_setup(self, settings: Dict[str, Any]) -> str:
        """Generate slippage model setup code."""
        slippage = settings.get('slippage', {})
        
        if not slippage:
            return "        # Using default slippage model"
        
        model = slippage.get('model', 'percentage')
        value = slippage.get('value', 0.001)
        
        if model == 'percentage':
            return f"        self.SetSecurityInitializer(lambda security: security.SetSlippageModel(ConstantSlippageModel({value})))"
        elif model == 'fixed':
            return f"        self.SetSecurityInitializer(lambda security: security.SetSlippageModel(ConstantSlippageModel({value})))"
        else:
            return "        # Using default slippage model"