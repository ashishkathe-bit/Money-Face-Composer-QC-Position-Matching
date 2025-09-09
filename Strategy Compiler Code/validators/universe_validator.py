import json
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
import os


class UniverseValidator:
    """
    Validates universe properties in StrategySpec JSON files against the schema requirements.
    
    Schema Requirements for universe:
    - Required: Array of asset objects with minItems: 1
    - Each asset requires: symbol (string, 1-20 chars, pattern: ^[A-Za-z0-9/.:-]{1,20}$)
    - Optional asset fields: name (string), assetClass (enum)
    - Additional properties: false (warn but don't fail)
    
    Asset class enum values: EQUITY, ETF, FUTURE, FOREX, CRYPTO, OPTION, BOND, COMMODITY
    """
    
    VALID_ASSET_CLASSES = {
        "EQUITY", "ETF", "FUTURE", "FOREX", "CRYPTO", "OPTION", "BOND", "COMMODITY"
    }
    
    SYMBOL_PATTERN = re.compile(r'^[A-Za-z0-9/.:-]{1,20}$')
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_universe_property(self, universe: List[Dict[str, Any]], file_path: str = "") -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single universe property list.
        
        Args:
            universe: The universe list to validate
            file_path: Optional file path for error reporting
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Check universe structure
        self._validate_universe_structure(universe, file_path)
        
        if isinstance(universe, list):
            # Track symbols for duplicate detection
            seen_symbols = set()
            
            # Validate each asset
            for i, asset in enumerate(universe):
                self._validate_asset(asset, i, file_path, seen_symbols)
        
        is_valid = len(self.validation_errors) == 0
        return is_valid, self.validation_errors.copy(), self.validation_warnings.copy()
    
    def _validate_universe_structure(self, universe: Any, file_path: str):
        """Validate universe is a non-empty array."""
        if not isinstance(universe, list):
            self.validation_errors.append(f"{file_path}: Universe must be an array, got {type(universe).__name__}")
            return
        
        if len(universe) == 0:
            self.validation_errors.append(f"{file_path}: Universe must contain at least one asset (minItems: 1)")
    
    def _validate_asset(self, asset: Any, index: int, file_path: str, seen_symbols: set):
        """Validate individual asset object."""
        asset_path = f"{file_path}[{index}]" if file_path else f"asset[{index}]"
        
        if not isinstance(asset, dict):
            self.validation_errors.append(f"{asset_path}: Asset must be an object, got {type(asset).__name__}")
            return
        
        # Check required symbol field
        if 'symbol' not in asset:
            self.validation_errors.append(f"{asset_path}: Missing required field 'symbol'")
        else:
            symbol = asset['symbol']
            self._validate_symbol(symbol, asset_path, seen_symbols)
        
        # Validate optional fields
        if 'name' in asset:
            self._validate_name(asset['name'], asset_path)
        
        if 'assetClass' in asset:
            self._validate_asset_class(asset['assetClass'], asset_path)
        
        # Check for additional properties (warn but don't fail)
        self._check_additional_properties(asset, asset_path)
    
    def _validate_symbol(self, symbol: Any, asset_path: str, seen_symbols: set):
        """Validate symbol field."""
        if not isinstance(symbol, str):
            self.validation_errors.append(f"{asset_path}: symbol must be a string, got {type(symbol).__name__}")
            return
        
        if not symbol:
            self.validation_errors.append(f"{asset_path}: symbol cannot be empty")
            return
        
        # Check pattern and length
        if not self.SYMBOL_PATTERN.match(symbol):
            self.validation_errors.append(
                f"{asset_path}: symbol '{symbol}' does not match required pattern. "
                f"Must be 1-20 characters containing only letters, numbers, and ./:-"
            )
        
        # Check for duplicates
        if symbol in seen_symbols:
            self.validation_warnings.append(f"{asset_path}: Duplicate symbol '{symbol}' found in universe")
        else:
            seen_symbols.add(symbol)
    
    def _validate_name(self, name: Any, asset_path: str):
        """Validate name field if present."""
        if name is not None and not isinstance(name, str):
            self.validation_errors.append(f"{asset_path}: name must be a string, got {type(name).__name__}")
    
    def _validate_asset_class(self, asset_class: Any, asset_path: str):
        """Validate assetClass field if present."""
        if asset_class is None:
            return
        
        if not isinstance(asset_class, str):
            self.validation_errors.append(f"{asset_path}: assetClass must be a string, got {type(asset_class).__name__}")
            return
        
        if asset_class not in self.VALID_ASSET_CLASSES:
            self.validation_errors.append(
                f"{asset_path}: assetClass '{asset_class}' is not valid. "
                f"Valid options: {', '.join(sorted(self.VALID_ASSET_CLASSES))}"
            )
    
    def _check_additional_properties(self, asset: Dict[str, Any], asset_path: str):
        """Check for additional properties and warn about unexpected ones."""
        expected_properties = {'symbol', 'name', 'assetClass'}
        common_additional = {'exchange', 'sector', 'currency', 'market'}
        
        for key in asset.keys():
            if key not in expected_properties:
                if key in common_additional:
                    self.validation_warnings.append(
                        f"{asset_path}: Additional property '{key}' found (common but not in schema)"
                    )
                else:
                    self.validation_warnings.append(
                        f"{asset_path}: Unexpected additional property '{key}' found"
                    )
    
    def validate_sample_files(self, sample_inputs_dir: str) -> Dict[str, Tuple[bool, List[str], List[str]]]:
        """
        Validate all sample input files in the given directory.
        
        Args:
            sample_inputs_dir: Path to directory containing sample strategy files
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        sample_path = Path(sample_inputs_dir)
        
        if not sample_path.exists():
            raise FileNotFoundError(f"Sample inputs directory not found: {sample_inputs_dir}")
        
        # Find all spec JSON files
        spec_files = list(sample_path.glob("*/spec_*.json"))
        
        for spec_file in spec_files:
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'universe' not in data:
                    results[str(spec_file)] = (False, [f"No 'universe' property found"], [])
                    continue
                
                is_valid, errors, warnings = self.validate_universe_property(data['universe'], str(spec_file))
                results[str(spec_file)] = (is_valid, errors, warnings)
                
            except json.JSONDecodeError as e:
                results[str(spec_file)] = (False, [f"JSON decode error: {e}"], [])
            except Exception as e:
                results[str(spec_file)] = (False, [f"Unexpected error: {e}"], [])
        
        return results
    
    def generate_validation_report(self, results: Dict[str, Tuple[bool, List[str], List[str]]]) -> str:
        """Generate a human-readable validation report."""
        report_lines = []
        report_lines.append("Universe Property Validation Report")
        report_lines.append("=" * 38)
        report_lines.append("")
        
        total_files = len(results)
        valid_files = sum(1 for is_valid, _, _ in results.values() if is_valid)
        
        report_lines.append(f"Total files validated: {total_files}")
        report_lines.append(f"Valid files: {valid_files}")
        report_lines.append(f"Invalid files: {total_files - valid_files}")
        report_lines.append("")
        
        for file_path, (is_valid, errors, warnings) in results.items():
            filename = Path(file_path).name
            status = "[VALID]" if is_valid else "[INVALID]"
            report_lines.append(f"{status}: {filename}")
            
            if errors:
                for error in errors:
                    # Remove file path prefix from error message for cleaner display
                    clean_error = error.split(": ", 1)[-1] if ": " in error else error
                    report_lines.append(f"  ERROR: {clean_error}")
            
            if warnings:
                for warning in warnings:
                    clean_warning = warning.split(": ", 1)[-1] if ": " in warning else warning
                    report_lines.append(f"  WARNING: {clean_warning}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
