import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class SettingsValidator:
    """
    Validates the settings property from StrategySpec JSON.
    
    Handles validation of capital, rebalance, currency, dates, fees, slippage,
    and benchmark settings according to the StrategySpec v1 schema.
    """
    
    VALID_REBALANCE_VALUES = {
        "none", "intraday", "daily", "weekly", "monthly", "quarterly", "yearly"
    }
    
    VALID_SLIPPAGE_MODELS = {
        "fixed", "percentage", "volumeImpact"
    }
    
    CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    def __init__(self):
        """Initialize the SettingsValidator with default settings."""
        pass
    
    def validate_settings(self, settings: Any) -> Tuple[bool, List[str]]:
        """
        Main validation method for settings property.
        
        Args:
            settings: Settings object from StrategySpec
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        if not isinstance(settings, dict):
            return False, ["Settings must be a dictionary/object"]
        
        errors = []
        
        # Validate required fields
        capital_errors = self._validate_capital(settings.get('capital'))
        errors.extend(capital_errors)
        
        rebalance_errors = self._validate_rebalance(settings.get('rebalance'))
        errors.extend(rebalance_errors)
        
        # Validate start date fields
        start_errors = self._validate_date_field(settings.get('start'), 'start')
        errors.extend(start_errors)


        end_errors = self._validate_date_field(settings.get('end'), 'end')
        errors.extend(end_errors)
        
        if 'currency' in settings:
        
            currency_errors = self._validate_currency(settings.get('currency'))
            errors.extend(currency_errors)
            
        if 'fees' in settings:
        
            fees_errors = self._validate_fees(settings.get('fees'))
            errors.extend(fees_errors)
            
        if 'slippage' in settings:
            
            slippage_errors = self._validate_slippage(settings.get('slippage'))
            errors.extend(slippage_errors)
        
        # Validate date logic (start <= end)
        if 'start' in settings and 'end' in settings:
            date_logic_errors = self._validate_date_logic(settings['start'], settings['end'])
            errors.extend(date_logic_errors)
        
        return len(errors) == 0, errors
    
    def _validate_capital(self, capital: Any) -> List[str]:
        """Validate capital field (required, number, minimum 0)."""
        errors = []
        
        if capital is None:
            errors.append("Capital is required")
            return errors
        
        # Exclude boolean from number types (bool is subclass of int in Python)
        if not isinstance(capital, (int, float)) or isinstance(capital, bool):
            errors.append("Capital must be a number")
            return errors
        
        if capital < 0:
            errors.append("Capital must be greater than or equal to 0")
        
        return errors
    
    def _validate_rebalance(self, rebalance: Any) -> List[str]:
        """Validate rebalance field (required, enum)."""
        errors = []
        
        if rebalance is None:
            errors.append("Rebalance is required")
            return errors
        
        if not isinstance(rebalance, str):
            errors.append("Rebalance must be a string")
            return errors
        
        if rebalance not in self.VALID_REBALANCE_VALUES:
            valid_values = ", ".join(sorted(self.VALID_REBALANCE_VALUES))
            errors.append(f"Rebalance must be one of: {valid_values}")
        
        return errors
    
    def _validate_date_field(self, date_value: Any, field_name: str) -> List[str]:
        """Validate date fields (start/end) format."""
        errors = []
        
        if date_value is None:
            errors.append(f"{field_name.capitalize()} is required")
            return errors
        
        if not isinstance(date_value, str):
            errors.append(f"{field_name.capitalize()} date must be a string")
            return errors
        
        # First check strict format with regex
        if not self.DATE_PATTERN.match(date_value):
            errors.append(f"{field_name.capitalize()} date must be in YYYY-MM-DD format")
            return errors
        
        try:
            # Validate that it's a real date
            datetime.strptime(date_value, '%Y-%m-%d')
        except ValueError:
            errors.append(f"{field_name.capitalize()} date must be in YYYY-MM-DD format")
        
        return errors
    
    def _validate_currency(self, currency: Any) -> List[str]:
        """Validate currency field (3-letter uppercase code)."""
        errors = []
        
        if currency is None:
            errors.append("Currency is required")
            return errors
        
        if not isinstance(currency, str):
            errors.append("Currency must be a string")
            return errors
        
        if not self.CURRENCY_PATTERN.match(currency):
            errors.append("Currency must be a 3-letter uppercase code (e.g., USD, EUR, GBP)")
        
        return errors
    
    def _validate_benchmark(self, benchmark: Any) -> List[str]:
        """Validate benchmark field (string)."""
        errors = []
        
        if not isinstance(benchmark, str):
            errors.append("Benchmark must be a string")
        
        return errors
    
    def _validate_fees(self, fees: Any) -> List[str]:
        """Validate fees nested object."""
        errors = []
        
        if fees is None:
            errors.append("Fees field is required")
            return errors
        
        if not isinstance(fees, dict):
            errors.append("Fees must be an object/dictionary")
            return errors
        
        # Validate individual fee fields (all optional)
        if 'perOrder' in fees:
            per_order_errors = self._validate_fee_field(fees['perOrder'], 'perOrder')
            errors.extend(per_order_errors)
        
        if 'perShare' in fees:
            per_share_errors = self._validate_fee_field(fees['perShare'], 'perShare')
            errors.extend(per_share_errors)
        
        if 'percentage' in fees:
            percentage_errors = self._validate_percentage_fee(fees['percentage'])
            errors.extend(percentage_errors)
        
        # Check for unknown fields
        valid_fee_fields = {'perOrder', 'perShare', 'percentage'}
        unknown_fields = set(fees.keys()) - valid_fee_fields
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            errors.append(f"Unknown fee fields: {unknown_list}")
        
        return errors
    
    def _validate_fee_field(self, value: Any, field_name: str) -> List[str]:
        """Validate individual fee field (number, minimum 0)."""
        errors = []
        
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"Fee {field_name} must be a number")
            return errors
        
        if value < 0:
            errors.append(f"Fee {field_name} must be greater than or equal to 0")
        
        return errors
    
    def _validate_percentage_fee(self, percentage: Any) -> List[str]:
        """Validate percentage fee field (number, 0 <= x <= 1)."""
        errors = []
        
        if not isinstance(percentage, (int, float)) or isinstance(percentage, bool):
            errors.append("Fee percentage must be a number")
            return errors
        
        if percentage < 0:
            errors.append("Fee percentage must be greater than or equal to 0")
        
        if percentage > 1:
            errors.append("Fee percentage must be less than or equal to 1")
        
        return errors
    
    def _validate_slippage(self, slippage: Any) -> List[str]:
        """Validate slippage nested object."""
        errors = []
        
        if slippage is None:
            errors.append("Slippage field is required")
            return errors
        
        if not isinstance(slippage, dict):
            errors.append("Slippage must be an object/dictionary")
            return errors
        
        # Validate model field
        if 'model' in slippage:
            model_errors = self._validate_slippage_model(slippage['model'])
            errors.extend(model_errors)
        
        # Validate value field
        if 'value' in slippage:
            value_errors = self._validate_slippage_value(slippage['value'])
            errors.extend(value_errors)
        
        # Check for unknown fields
        valid_slippage_fields = {'model', 'value'}
        unknown_fields = set(slippage.keys()) - valid_slippage_fields
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            errors.append(f"Unknown slippage fields: {unknown_list}")
        
        return errors
    
    def _validate_slippage_model(self, model: Any) -> List[str]:
        """Validate slippage model field (enum)."""
        errors = []
        
        if not isinstance(model, str):
            errors.append("Slippage model must be a string")
            return errors
        
        if model not in self.VALID_SLIPPAGE_MODELS:
            valid_models = ", ".join(sorted(self.VALID_SLIPPAGE_MODELS))
            errors.append(f"Slippage model must be one of: {valid_models}")
        
        return errors
    
    def _validate_slippage_value(self, value: Any) -> List[str]:
        """Validate slippage value field (number, minimum 0)."""
        errors = []
        
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append("Slippage value must be a number")
            return errors
        
        if value < 0:
            errors.append("Slippage value must be greater than or equal to 0")
        
        return errors
    
    def _validate_date_logic(self, start: str, end: str) -> List[str]:
        """Validate that start date is not after end date."""
        errors = []
        
        try:


            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            
            if start_date > end_date:
                errors.append("Start date must be on or before end date")
        except Exception as e:
            # Date format errors will be caught by individual field validation
            
            errors.append("Start & End date must be in YYYY-MM-DD format")
            pass
        
        return errors
    
    def validate_settings_structure(self, data: Any) -> Tuple[bool, List[str]]:
        """
        Validate that settings exists and has proper structure.
        
        Args:
            data: Full StrategySpec data dictionary
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        if not isinstance(data, dict):
            return False, ["StrategySpec must be a dictionary/object"]
        
        if 'settings' not in data:
            return False, ["Settings property is required"]
        
        # Delegate to main validation
        return self.validate_settings(data['settings'])
    
    def get_validation_summary(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a validation summary with details about the settings.
        
        Args:
            settings: Settings dictionary to summarize
            
        Returns:
            Dictionary containing validation summary information
        """
        is_valid, errors = self.validate_settings(settings)
        
        summary = {
            'is_valid': is_valid,
            'error_count': len(errors),
            'errors': errors,
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
            'field_types': {
                field: type(value).__name__ 
                for field, value in settings.items() 
                if isinstance(settings, dict)
            }
        }
        
        return summary