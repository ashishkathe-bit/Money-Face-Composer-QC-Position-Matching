import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class SettingsGenerator:
    """
    Generates settings-related code and configuration for QCL algorithms.
    
    Processes the settings property from StrategySpec JSON and provides formatted
    output for algorithm.py initialization and metadata.json files.
    """
    
    # Mapping of StrategySpec rebalance frequencies to QCL schedule expressions
    REBALANCE_QCL_MAPPING = {
        "none": None,  # No scheduled rebalancing
        "intraday": "self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(TimeSpan.FromHours(1)), self.rebalance)",
        "daily": "self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.BeforeMarketClose('SPY', 30), self.rebalance)",
        "weekly": "self.Schedule.On(self.DateRules.WeekStart(), self.TimeRules.BeforeMarketClose('SPY', 30), self.rebalance)",
        "monthly": "self.Schedule.On(self.DateRules.MonthStart(), self.TimeRules.BeforeMarketClose('SPY', 30), self.rebalance)",
        "quarterly": "self.Schedule.On(self.DateRules.MonthStart('SPY', 1), self.TimeRules.BeforeMarketClose('SPY', 30), self.rebalance)",
        "yearly": "self.Schedule.On(self.DateRules.YearStart(), self.TimeRules.BeforeMarketClose('SPY', 30), self.rebalance)"
    }
    
    # Slippage model mapping to QCL implementations
    SLIPPAGE_QCL_MAPPING = {
        "fixed": "ConstantSlippageModel",
        "percentage": "VolumeShareSlippageModel",
        "volumeImpact": "MarketImpactSlippageModel"
    }
    
    def __init__(self):
        """Initialize the SettingsGenerator with default settings."""
        self.compilation_timestamp = None
    
    def generate_capital_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method capital setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for capital initialization
        """
        if not isinstance(settings, dict) or 'capital' not in settings:
            return "        # No capital specified"
        
        capital = settings['capital']
        if not isinstance(capital, (int, float)) or capital <= 0:
            return "        # Invalid capital value"
        
        code_lines = []
        code_lines.append("        # Set initial capital")
        code_lines.append(f"        self.SetCash({capital})")
        
        return "\n".join(code_lines)
    
    def generate_dates_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method date range setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for date range initialization
        """
        if not isinstance(settings, dict):
            return ""
        
        code_lines = []
        
        # Set start date
        if 'start' in settings:
            start_date = settings['start']
            if isinstance(start_date, str):
                code_lines.append("        # Set backtest start date")
                code_lines.append(f"        self.SetStartDate(datetime.strptime('{start_date}', '%Y-%m-%d'))\n")
        
        # Set end date
        if 'end' in settings:
            end_date = settings['end']
            if isinstance(end_date, str):
                code_lines.append("        # Set backtest end date")
                code_lines.append(f"        self.SetEndDate(datetime.strptime('{end_date}', '%Y-%m-%d'))")
        
        return "\n".join(code_lines) if code_lines else ""
    
    def generate_currency_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method currency setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for currency initialization
        """
        if not isinstance(settings, dict) or 'currency' not in settings:
            return ""
        
        currency = settings['currency']
        # Validate currency format: exactly 3 uppercase letters
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper() or not currency.isalpha():
            return ""
        
        # Only add currency setup if it's not USD (QCL default)
        if currency == "USD":
            return ""
        
        code_lines = []
        code_lines.append("        # Set account currency")
        code_lines.append(f"        self.SetAccountCurrency('{currency}')")
        
        return "\n".join(code_lines)
    
    def generate_benchmark_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method benchmark setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for benchmark initialization
        """
        if not isinstance(settings, dict) or 'benchmark' not in settings:
            return ""
        
        benchmark = settings['benchmark']
        if not isinstance(benchmark, str) or not benchmark.strip():
            return ""
        
        code_lines = []
        code_lines.append("        # Set performance benchmark")
        code_lines.append(f"        self.SetBenchmark('{benchmark.strip()}')")
        
        return "\n".join(code_lines)
    
    def generate_fees_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method fees setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for fees initialization
        """
        if not isinstance(settings, dict) or 'fees' not in settings:
            return ""
        
        fees = settings['fees']
        if not isinstance(fees, dict) or not fees:
            return ""
        
        code_lines = []
        
        # Check for different fee types and generate appropriate QCL code
        if 'percentage' in fees:
            percentage = fees['percentage']
            if isinstance(percentage, (int, float)) and 0 <= percentage <= 1:
                code_lines.append("        # Set percentage-based fees")
                code_lines.append(f"        fee_model = PercentageFeeModel({percentage})")
        
        if 'perOrder' in fees:
            per_order = fees['perOrder']
            if isinstance(per_order, (int, float)) and per_order >= 0:
                code_lines.append(f"       # Per-order fee: ${per_order}")
                code_lines.append(f"        fee_model = PerOrderFeeModel({per_order})")
        
        if 'perShare' in fees:
            per_share = fees['perShare']
            if isinstance(per_share, (int, float)) and per_share >= 0:
                code_lines.append(f"       # Per-share fee: ${per_share}")
                code_lines.append(f"        fee_model = PerShareFeeModel({per_share})")
        
        if code_lines and not any("Custom fee model" in line for line in code_lines):
            # Add general fee setup if specific implementation not added
            code_lines.insert(0, "        # Set custom transaction fees")
        
        return "\n".join(code_lines)
    
    def generate_slippage_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method slippage setup code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for slippage initialization
        """
        if not isinstance(settings, dict) or 'slippage' not in settings:
            return ""
        
        slippage = settings['slippage']
        if not isinstance(slippage, dict) or not slippage:
            return ""
        
        code_lines = []
        
        model = slippage.get('model', 'percentage')
        value = slippage.get('value', 0)
        
        if not isinstance(value, (int, float)) or value < 0:
            return ""
        
        code_lines.append("        # Set slippage model")
        
        if model == "fixed":
            code_lines.append(f"        slippage_model = class FixedSlippageModel({value})")
        elif model == "percentage":
            code_lines.append(f"        slippage_model = PercentageSlippageModel({value})")
        elif model == "volumeImpact":
            code_lines.append(f"        slippage_model = VolumeImpactSlippageModel({value})")
        else:
            code_lines.append(f"        # Unknown slippage model: {model}")
        
        return "\n".join(code_lines)
    
    def generate_rebalance_setup_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate QCL Initialize() method rebalancing schedule code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for rebalancing schedule
        """
        if not isinstance(settings, dict) or 'rebalance' not in settings:
            return ""
        
        rebalance = settings['rebalance']
        if not isinstance(rebalance, str) or rebalance not in self.REBALANCE_QCL_MAPPING:
            return ""
        
        qcl_schedule = self.REBALANCE_QCL_MAPPING[rebalance]
        
        if qcl_schedule is None:  # "none" case
            return "        # No automatic rebalancing scheduled"
        
        code_lines = []
        code_lines.append(f"        # Schedule {rebalance} rebalancing")
        code_lines.append(f"        {qcl_schedule}")
        
        return "\n".join(code_lines)
    
    def generate_settings_imports(self, settings: Dict[str, Any]) -> List[str]:
        """
        Generate required imports for settings functionality.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            List of import statements needed for generated code
        """
        imports = []
        
        # Basic imports always needed
        imports.append("from datetime import datetime, timedelta")
        imports.append("from QuantConnect.Orders.Fees import FeeModel")
        
        # Date-related imports
        if 'start' in settings or 'end' in settings:
            imports.append("from datetime import datetime")
        
        # Scheduling imports for rebalancing
        if 'rebalance' in settings and settings['rebalance'] != 'none':
            imports.append("from System import TimeSpan")
        
        return list(set(imports))  # Remove duplicates
    
    def generate_settings_initialization_code(self, settings: Dict[str, Any]) -> str:
        """
        Generate complete QCL Initialize() method settings code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for all settings initialization
        """
        if not isinstance(settings, dict):
            return "        # No settings configuration"
        
        code_sections = []
        
        # Generate each section
        capital_code = self.generate_capital_setup_code(settings)
        if capital_code and capital_code != "        # No capital specified":
            code_sections.append(capital_code)
        
        currency_code = self.generate_currency_setup_code(settings)
        if currency_code:
            code_sections.append(currency_code)
        
        dates_code = self.generate_dates_setup_code(settings)
        if dates_code:
            code_sections.append(dates_code)
        
        benchmark_code = self.generate_benchmark_setup_code(settings)
        if benchmark_code:
            code_sections.append(benchmark_code)
        
        fees_code = self.generate_fees_setup_code(settings)
        if fees_code:
            code_sections.append(fees_code)
        
        slippage_code = self.generate_slippage_setup_code(settings)
        if slippage_code:
            code_sections.append(slippage_code)
        
        security_initializer_code = self.generate_security_initializer(fees_code, slippage_code)
        
        code_sections.append(security_initializer_code)
        
        rebalance_code = self.generate_rebalance_setup_code(settings)
        if rebalance_code:
            code_sections.append(rebalance_code)
        
        if not code_sections:
            return "        # No settings configuration"
        
        # Join sections with empty lines
        return "\n        \n".join(code_sections)
    
    def generate_settings_statistics(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate settings metrics and configuration statistics.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Dictionary containing settings statistics
        """
        if not isinstance(settings, dict):
            return {
                'total_fields': 0,
                'required_fields_present': {'capital': False, 'rebalance': False},
                'optional_fields_present': {},
                'has_date_range': False,
                'has_fees': False,
                'has_slippage': False,
                'configuration_complexity': 'minimal'
            }
        
        stats = {
            'total_fields': len(settings),
            'required_fields_present': {
                'capital': 'capital' in settings,
                'rebalance': 'rebalance' in settings
            },
            'optional_fields_present': {
                'start': 'start' in settings,
                'end': 'end' in settings,
                'currency': 'currency' in settings,
                'benchmark': 'benchmark' in settings,
                'fees': 'fees' in settings,
                'slippage': 'slippage' in settings
            },
            'has_date_range': 'start' in settings and 'end' in settings,
            'has_fees': 'fees' in settings and bool(settings.get('fees', {})),
            'has_slippage': 'slippage' in settings and bool(settings.get('slippage', {})),
            'rebalance_frequency': settings.get('rebalance', 'none'),
            'currency': settings.get('currency', 'USD')
        }
        
        # Determine configuration complexity
        complexity_score = 0
        complexity_score += 1 if stats['has_date_range'] else 0
        complexity_score += 1 if stats['has_fees'] else 0
        complexity_score += 1 if stats['has_slippage'] else 0
        complexity_score += 1 if settings.get('currency') and settings['currency'] != 'USD' else 0
        complexity_score += 1 if 'benchmark' in settings else 0
        complexity_score += 1 if settings.get('rebalance', 'none') != 'none' else 0
        
        if complexity_score == 0:
            stats['configuration_complexity'] = 'minimal'
        elif complexity_score <= 2:
            stats['configuration_complexity'] = 'moderate'
        else:
            stats['configuration_complexity'] = 'complex'
        
        return stats
    
    def generate_compilation_settings_metadata(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive settings metadata for tracking file.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Dictionary containing complete settings metadata
        """
        statistics = self.generate_settings_statistics(settings)
        imports_needed = self.generate_settings_imports(settings)
        
        metadata = {
            'statistics': statistics,
            'imports_needed': imports_needed,
            'qcl_features_used': {
                'cash_management': 'capital' in settings,
                'date_range_override': statistics['has_date_range'],
                'currency_override': settings.get('currency', 'USD') != 'USD',
                'benchmark_tracking': 'benchmark' in settings,
                'custom_fees': statistics['has_fees'],
                'slippage_modeling': statistics['has_slippage'],
                'scheduled_rebalancing': settings.get('rebalance', 'none') != 'none'
            },
            'configuration_summary': {
                'capital': settings.get('capital'),
                'rebalance': settings.get('rebalance', 'none'),
                'currency': settings.get('currency', 'USD'),
                'date_range_days': self._calculate_date_range_days(settings) if statistics['has_date_range'] else None,
                'complexity': statistics['configuration_complexity']
            }
        }
        
        return metadata
    
    def _calculate_date_range_days(self, settings: Dict[str, Any]) -> Optional[int]:
        """Calculate the number of days in the date range."""
        try:
            if 'start' in settings and 'end' in settings:
                start_date = datetime.strptime(settings['start'], '%Y-%m-%d')
                end_date = datetime.strptime(settings['end'], '%Y-%m-%d')
                return (end_date - start_date).days
        except (ValueError, TypeError):
            pass
        return None
    
    def generate_fee_model(self, settings: Dict[str, Any]) -> str:
        """
        Generate fee model code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for fee model
        """
        
        fee_model = "# -------- Fee Models --------\n# Per order, per share, percentage fee model custom classes definitions (do not manipulate it)" + r'''
class PerOrderFeeModel(FeeModel):
    """Fixed fee per order, regardless of size."""
    def __init__(self, fee: float = 1.0):
        self.fee = float(fee)

    def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
        security = parameters.Security
        return OrderFee(CashAmount(self.fee, security.QuoteCurrency.Symbol))

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
        return OrderFee(CashAmount(fee_amount, security.QuoteCurrency.Symbol))''' + "\n\n"
        
        return fee_model
    
    def generate_slippage_model(self, settings: Dict[str, Any]) -> str:
        """
        Generate slippage model code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for slippage model
        """
        
        slippage_model = r'''
# -------- Slippage Models --------
# Fixed, percentage, volume impact slippage model custom classes definitions (do not manipulate it)
class FixedSlippageModel:
    """Fixed slippage model."""
    def __init__(self, value: float = 0.01):
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        return self.value

class PercentageSlippageModel:
    """Percentage slippage model."""
    def __init__(self, value: float = 0.0005):
        if not (0 <= value <= 1):
            raise ValueError("Percentage slippage must be between 0 and 1")
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        return asset.Price * self.value

class VolumeImpactSlippageModel:
    """Volume impact slippage model."""
    def __init__(self, value: float = 0.1):
        self.value = float(value)
    def GetSlippageApproximation(self, asset: Security, order: Order) -> float:
        vol = max(asset.Volume, 1)
        qty = abs(order.AbsoluteQuantity)
        return asset.Price * self.value * (qty / vol)''' + "\n\n"
        
        return slippage_model
    
    def generate_security_initializer(self, is_fee_model: bool = False, is_slippage_model: bool = False) -> str:
        """
        Generate security initializer code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for security initializer
        """
        
        if not is_fee_model and not is_slippage_model:
            
            return ""
        
        elif is_fee_model and not is_slippage_model:
            
            return r"""
        # wrap brokerage defaults + fee model
        def init_sec(security: Security):
            security.SetFeeModel(fee_model)
        
        self.SetSecurityInitializer(init_sec)""" 
        
        elif not is_fee_model and is_slippage_model:
            
            return r"""
        # wrap brokerage defaults + slippage model
        def init_sec(security: Security):
            security.SetSlippageModel(slippage_model)
        
        self.SetSecurityInitializer(init_sec)""" 
        
        else:
            
            return r"""
        # wrap brokerage defaults + fee model + slippage model
        def init_sec(security: Security):
            security.SetFeeModel(fee_model)
            security.SetSlippageModel(slippage_model)
        
        self.SetSecurityInitializer(init_sec)""" 
        
    def generate_rebalance_method(self) -> str:
        """
        Generate rebalance method code.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Formatted Python code for rebalance method
        """
        
        
        return r"""
    def rebalance(self):
        '''
        Equal-weight rebalance across all currently invested positions.

        Behavior:
        - Finds all symbols with non-zero holdings (Portfolio[x].Invested == True).
        - If any are invested, sets each to an equal target weight of 1/N.
        - Uses SetHoldings(...) so Lean submits the necessary orders to reach targets.
        - Emits a Debug line summarizing the action.

        Side effects:
        - May place market orders and change portfolio exposure.

        Returns:
        - None
        '''
    
        # Collect currently invested symbols (positions with non-zero holdings)
        invested_symbols = [p.Symbol for p in self.Portfolio.Values if p.Invested]

        # If nothing is invested, skip rebalancing to avoid unnecessary orders
        if not invested_symbols:
            self.Debug("Rebalance skipped: no invested positions")
            return

        # Target equal weight for each invested symbol
        weight = 1.0 / len(invested_symbols)

        # Bring each position to the target weight
        for symbol in invested_symbols:
            # SetHoldings adjusts the position to the given portfolio weight
            self.SetHoldings(symbol, weight)

        # Log a concise summary for debugging/audit
        self.Debug(f"Rebalanced equally across {len(invested_symbols)} positions at {weight:.2%} each")""" + "\n\n"
    
    def process_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method that processes settings property and returns all generated components.
        
        Args:
            settings: Settings dictionary from StrategySpec
            
        Returns:
            Dictionary containing all processed settings information:
            {
                "settings_initialization_code": str,
                "required_imports": List[str],
                "settings_statistics": Dict[str, Any],
                "compilation_settings_metadata": Dict[str, Any],
                "original_settings": Dict[str, Any]
            }
        """
        # Note: Validation is handled by SettingsValidator, so we assume settings is valid
        
        # Generate all components
        processed_settings = {
            "settings_initialization_code": self.generate_settings_initialization_code(settings),
            "required_imports": self.generate_settings_imports(settings),
            "settings_statistics": self.generate_settings_statistics(settings),
            "compilation_settings_metadata": self.generate_compilation_settings_metadata(settings),
            "original_settings": settings.copy() if isinstance(settings, dict) else {},
            "fee_model": self.generate_fee_model(settings),
            "slippage_model": self.generate_slippage_model(settings),
            "rebalance_method": self.generate_rebalance_method()
            
        }
        
        return processed_settings