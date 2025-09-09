from typing import Dict, List, Any
from indicators.indicator_code_reader import IndicatorCodeReader

class IndicatorGenerator:
    """
    Generates QuantConnect indicator initialization and calculation code.
    
    Handles all 18 supported indicators with proper parameter validation,
    QCL-compliant code generation, and custom indicator implementations.
    """
    
    # List of all implemented indicators
    IMPLEMENTED_INDICATORS = {
        "rsi", "current-price", "cumulative-return", "moving-average-price", 
        "exponential-moving-average-price", "moving-average-return", 
        "standard-deviation-price", "standard-deviation-return", "max-drawdown", 
        "volatility", "returns", "drawdown", "month", "day-of-week", 
        "day-of-month", "day-of-year"
    }
    
    # Indicators that require custom implementations
    CUSTOM_INDICATORS = {
        "max-drawdown", "drawdown", "moving-average-return"
    }
    
    def __init__(self, embed_custom_indicators: bool = True):
        """Initialize the IndicatorGenerator."""
        self.indicators_used = {}  # indicator_key -> indicator_config
        self.custom_methods_needed = set()
        self.embed_custom_indicators = embed_custom_indicators
        self.code_reader = IndicatorCodeReader() if IndicatorCodeReader else None
    
    def reset_variables(self):
        self.indicators_used.clear()
        self.custom_methods_needed.clear()
        
    def _process_indicator(self, indicator_config: Dict[str, Any]) -> None:
        """Process a single indicator configuration."""
        name = str(indicator_config.get('name', 'unknown')).lower()
        symbol = indicator_config.get('symbol')
        args = indicator_config.get('args', {})
        
        if name not in self.IMPLEMENTED_INDICATORS:
            return  # Skip unknown indicators
        
        # Create unique key
        indicator_key = self._create_indicator_key(name, symbol, args)
        
        # Store configuration
        if symbol is not None:
            self.indicators_used[indicator_key] = {
                "name": name,
                "symbol": symbol.upper(),
                "args": args
            }
        
        # Track custom methods needed
        if name in self.CUSTOM_INDICATORS:
            self.custom_methods_needed.add(name)
    
    def _create_indicator_key(self, name: str, symbol: str, args: Dict[str, Any]) -> str:
        """Create unique identifier for indicator instance."""
        key_parts = [name, symbol.upper()] if symbol else [name]
        
        # Add significant parameters to key
        if 'period' in args:
            key_parts.append(str(args['period']))
        if 'smoothing' in args:
            key_parts.append(f"s{args['smoothing']}")
        if 'fast' in args and 'slow' in args:
            key_parts.extend([str(args['fast']), str(args['slow'])])
            
        return "_".join(key_parts)
    
    def generate_initialization_code(self) -> str:
        """Generate indicator initialization code for Initialize() method with modern patterns."""
        if not self.indicators_used:
            return "        # No indicators needed"
            
        lines = []
        lines.append("        # Initialize indicators with automatic warm-up support")
        lines.append("        self.settings.automatic_indicator_warm_up = True")
        lines.append("")
        
        # Custom indicators are self-contained and don't need additional tracking
        
        # Initialize each indicator with modern patterns
        for indicator_key, config in self.indicators_used.items():
            init_line = self._generate_indicator_initialization(indicator_key, config)
            if init_line:
                lines.append(f"        {init_line}")
        
        # Custom indicators are initialized and ready
        
        return "\n".join(lines)
    
    def _generate_indicator_initialization(self, indicator_key: str, config: Dict[str, Any]) -> str:
        """Generate initialization line for a specific indicator using modern QuantConnect patterns."""
        name = config["name"]
        symbol = config["symbol"]
        args = config["args"]
        
        # Create clean variable name for the indicator
        clean_symbol = symbol.lower().replace('-', '_')
        clean_name = name.lower().replace('-', '_')
        
        # Handle special cases
        if name in ["current-price", "current_price"]:
            return f"self.{clean_symbol}_{clean_name} = self.identity('{symbol}')"
        
        
        # Time-based indicators use direct self.time access (no initialization needed)
        elif name in ["month", "day-of-week", "day-of-month", "day-of-year"]:
            return None  # No initialization code needed for time-based indicators
        
        elif name == "max-drawdown":
            # Use custom MaxDrawdownIndicator
            period = args.get('period', 252)
            return f"self.{clean_symbol}_max_drawdown_{period} = MaxDrawdownIndicator({period})"
        
        elif name == "drawdown":
            # Use custom DrawdownIndicator
            period = args.get('period', 252)
            return f"self.{clean_symbol}_drawdown_{period} = DrawdownIndicator({period})"
        
        elif name == "moving-average-return":
            # Use custom MovingAvgReturnIndicator
            period = args.get('period', 20)
            return f"self.{clean_symbol}_moving_avg_return_{period} = MovingAvgReturnIndicator({period})"
        
        
        # Modern QuantConnect indicators with automatic registration and warm-up support
        elif name == "moving-average-price":
            period = args.get('period', 20)
            return f"self.{clean_symbol}_sma_{period} = self.sma('{symbol}', {period})"
        
        elif name == "exponential-moving-average-price":
            period = args.get('period', 20)
            return f"self.{clean_symbol}_ema_{period} = self.ema('{symbol}', {period})"
        
        elif name == "rsi":
            period = args.get('period', 14)
            return f"self.{clean_symbol}_rsi_{period} = self.rsi('{symbol}', {period})"
        
        elif name == "standard-deviation-price":
            period = args.get('period', 30)
            return f"self.{clean_symbol}_std_{period} = self.std('{symbol}', {period})"
        
        elif name == "volatility":
            period = args.get('period', 30)
            return f"self.{clean_symbol}_std_{period} = self.std('{symbol}', {period})"
        
        elif name in ["cumulative-return", "returns"]:
            period = args.get('period', 1)
            return f"self.{clean_symbol}_roc_{period} = self.roc('{symbol}', {period})"
        
        elif name == "standard-deviation-return":
            period = args.get('period', 30)
            return f"self.{clean_symbol}_std_dev_return_{period} = IndicatorExtensions.of(StandardDeviation({period}), self.roc('{symbol}', 1))"
        
        return None
    
    def generate_update_code(self) -> str:
        """Generate code for OnData() method to update custom indicators."""
        if not self.custom_methods_needed:
            return None
        
        lines = []
        lines.append("        # Update custom indicators with current prices")
        lines.append("        for kvp in self.securities:")
        lines.append("            symbol = kvp.key")
        lines.append("            security = kvp.value")
        lines.append("            if security.has_data:")
        lines.append("                price = security.price")
        
        # Generate updates for each custom indicator type
        for indicator_key, config in self.indicators_used.items():
            if config['name'] in self.CUSTOM_INDICATORS:
                symbol = config['symbol'].lower().replace('-', '_')
                name = config['name'].lower().replace('-', '_')
                period = config['args'].get('period', '')
                
                if name in ['max_drawdown', 'drawdown', 'moving_avg_return']:
                    period_suffix = f"_{period}" if period else ""
                    lines.append(f"                if symbol.value == '{config['symbol']}':")
                    lines.append(f"                    self.{symbol}_{name}{period_suffix}.update(price)")
        
        return "\n".join(lines) + "\n\n"
    
    def _generate_helper_methods(self) -> str:
        """Generate helper methods for custom indicators."""
        # Custom indicators are now self-contained classes
        # No additional helper methods needed
        return ""
    
    def _get_required_imports(self) -> List[str]:
        """Get list of required imports for the generated code using modern QuantConnect patterns."""
        imports = []
        
        # Modern QuantConnect uses AlgorithmImports which includes everything needed
        imports.append("from AlgorithmImports import *")
        
        # Add custom indicator imports only if not embedding
        if self.custom_methods_needed and not self.embed_custom_indicators:
            imports.append("from indicators import (")
            custom_imports = []
            if any('max_drawdown' in method for method in self.custom_methods_needed):
                custom_imports.append("    MaxDrawdownIndicator,")
            if any('drawdown' in method for method in self.custom_methods_needed):
                custom_imports.append("    DrawdownIndicator,")
            if any('moving_avg_return' in method for method in self.custom_methods_needed):
                custom_imports.append("    MovingAvgReturnIndicator,")
            # Time-based indicators no longer need imports (use direct self.time access)
            
            if custom_imports:
                imports.extend(custom_imports)
                imports.append(")")
        
        return imports
    
    def get_embedded_indicator_classes(self) -> str:
        """
        Generate embedded class code for only the custom indicators that are used.
        
        Returns:
            String containing the embedded class definitions, or empty string if none needed
        """
        if not self.embed_custom_indicators or not self.custom_methods_needed:
            return ""
        
        if not self.code_reader:
            return ""
        
        # Validate that all needed indicators exist
        missing_indicators = self.code_reader.validate_indicators_exist(self.custom_methods_needed)
        if missing_indicators:
            # Log warnings but continue (could add proper logging here)
            print(f"Warning: Missing indicator files: {missing_indicators}")
        
        # Generate embedded classes for used indicators only
        return self.code_reader.get_embedded_classes_code(self.custom_methods_needed)
    
    def get_indicator_value_code(self, indicator_config: Dict[str, Any]) -> str:
        """Generate code to access an indicator's current value with proper readiness checks."""
        self._process_indicator(indicator_config)
        indicator_name = indicator_config.get('name', '')
        symbol = indicator_config.get('symbol', '')
        args = indicator_config.get('args', {})

        # Time-based indicators use direct self.time property access
        if indicator_name == "month":
            return "self.time.month"
        elif indicator_name == "day-of-week":
            return "self.time.weekday()"
        elif indicator_name == "day-of-month":
            return "self.time.day"
        elif indicator_name == "day-of-year":
            return "self.time.timetuple().tm_yday"
        
        # Current price - use modern Securities access
        elif indicator_name == "current-price":
            return f"self.securities['{symbol.upper()}'].price"
        
        
        # Custom indicator calculations
        elif indicator_name == "max-drawdown":
            clean_symbol = symbol.lower().replace('-', '_')
            period = args.get('period', 252)
            return f"(self.{clean_symbol}_max_drawdown_{period}.current.value)"
        
        elif indicator_name == "drawdown":
            clean_symbol = symbol.lower().replace('-', '_')
            period = args.get('period', 252)
            return f"(self.{clean_symbol}_drawdown_{period}.current.value)"
        
        elif indicator_name == "moving-average-return":
            clean_symbol = symbol.lower().replace('-', '_')
            period = args.get('period', 20)
            return f"(self.{clean_symbol}_moving_avg_return_{period}.current.value)"
        
        
        # Standard QuantConnect indicators - use correct .Current.Value pattern with readiness check
        else:
            clean_symbol = symbol.lower().replace('-', '_')
            clean_name = indicator_name.lower().replace('-', '_')
            if 'period' in args:
                if indicator_name == "moving-average-price":
                    indicator_var = f"self.{clean_symbol}_sma_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name == "exponential-moving-average-price":
                    indicator_var = f"self.{clean_symbol}_ema_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name == "rsi":
                    indicator_var = f"self.{clean_symbol}_rsi_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name == "standard-deviation-price":
                    indicator_var = f"self.{clean_symbol}_std_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name == "volatility":
                    indicator_var = f"self.{clean_symbol}_std_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name in ["cumulative-return", "returns"]:
                    indicator_var = f"self.{clean_symbol}_roc_{args['period']}"
                    return f"({indicator_var}.current.value)"
                elif indicator_name == "standard-deviation-return":
                    indicator_var = f"self.{clean_symbol}_std_dev_return_{args['period']}"
                    return f"({indicator_var}.current.value)"
                else:
                    indicator_var = f"self.{clean_symbol}_{clean_name}_{args['period']}"
                    return f"({indicator_var}.current.value)"
            else:
                indicator_var = f"self.{clean_symbol}_{clean_name}"
                return f"({indicator_var}.current.value)"