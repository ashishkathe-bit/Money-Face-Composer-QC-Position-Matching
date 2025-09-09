import json
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
import os


class MetaValidator:
    """
    Validates meta properties in StrategySpec JSON files against the schema requirements.
    
    Schema Requirements for meta:
    - Required: name (string, 1-500 chars), version (string, pattern: \\d+\\.\\d+(\\.\\d+)?)
    - Optional: description (string, max 5000 chars), category (enum)
    - Additional properties allowed: true
    
    Category enum values: momentum, mean_reversion, trend_following, arbitrage, 
    market_neutral, long_short, buy_hold, tactical, other
    """
    
    VALID_CATEGORIES = {
        "momentum", "mean_reversion", "trend_following", "arbitrage",
        "market_neutral", "long_short", "buy_hold", "tactical", "other"
    }
    
    VERSION_PATTERN = re.compile(r'^\d+\.\d+(\.\d+)?$')
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_meta_property(self, meta: Dict[str, Any], file_path: str = "") -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single meta property dictionary.
        
        Args:
            meta: The meta dictionary to validate
            file_path: Optional file path for error reporting
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Check required properties
        self._validate_required_fields(meta, file_path)
        
        # Validate individual properties
        self._validate_name(meta.get('name'), file_path)
        self._validate_version(meta.get('version'), file_path)
        self._validate_description(meta.get('description'), file_path)
        self._validate_category(meta.get('category'), file_path)
        
        # Check for common additional properties
        self._check_additional_properties(meta, file_path)
        
        is_valid = len(self.validation_errors) == 0
        return is_valid, self.validation_errors.copy(), self.validation_warnings.copy()
    
    def _validate_required_fields(self, meta: Dict[str, Any], file_path: str):
        """Validate required fields are present."""
        if 'name' not in meta:
            self.validation_errors.append(f"{file_path}: Missing required field 'name' in meta")
        
        if 'version' not in meta:
            self.validation_errors.append(f"{file_path}: Missing required field 'version' in meta")
    
    def _validate_name(self, name: Any, file_path: str):
        """Validate name field."""
        
        
        if not isinstance(name, str):
            self.validation_errors.append(f"{file_path}: meta.name must be a string, got {type(name).__name__}")
            return
        
        if len(name) == 0:
            self.validation_errors.append(f"{file_path}: meta.name cannot be empty (minLength: 1)")
        elif len(name) > 500:
            self.validation_errors.append(f"{file_path}: meta.name exceeds maximum length of 500 characters")
    
    def _validate_version(self, version: Any, file_path: str):
        """Validate version field."""
        if version is None:
            return  # Already handled in required fields check
        
        if not isinstance(version, str):
            self.validation_errors.append(f"{file_path}: meta.version must be a string, got {type(version).__name__}")
            return
        
        if not self.VERSION_PATTERN.match(version):
            self.validation_errors.append(
                f"{file_path}: meta.version '{version}' does not match required pattern (e.g., '1.0', '1.2.3')"
            )
    
    def _validate_description(self, description: Any, file_path: str):
        """Validate description field if present."""
        if description is None:
            return
        
        if not isinstance(description, str):
            self.validation_errors.append(f"{file_path}: meta.description must be a string, got {type(description).__name__}")
            return
        
        if len(description) > 5000:
            self.validation_errors.append(f"{file_path}: meta.description exceeds maximum length of 5000 characters")
    
    def _validate_category(self, category: Any, file_path: str):
        """Validate category field if present."""
        if category is None:
            return
        
        if not isinstance(category, str):
            self.validation_errors.append(f"{file_path}: meta.category must be a string, got {type(category).__name__}")
            return
        
        if category not in self.VALID_CATEGORIES:
            self.validation_errors.append(
                f"{file_path}: meta.category '{category}' is not a valid category. "
                f"Valid options: {', '.join(sorted(self.VALID_CATEGORIES))}"
            )
    
    def _check_additional_properties(self, meta: Dict[str, Any], file_path: str):
        """Check for common additional properties and warn about unexpected ones."""
        expected_additional = {
            'source', 'source_id', 'source_url', 'complexity_score', 
            'created_at', 'updated_at'
        }
        
        schema_defined = {'name', 'description', 'version', 'category'}
        
        for key in meta.keys():
            if key not in schema_defined and key not in expected_additional:
                self.validation_warnings.append(
                    f"{file_path}: Unexpected additional property 'meta.{key}' found"
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
                
                if 'meta' not in data:
                    results[str(spec_file)] = (False, [f"No 'meta' property found"], [])
                    continue
                
                is_valid, errors, warnings = self.validate_meta_property(data['meta'], str(spec_file))
                results[str(spec_file)] = (is_valid, errors, warnings)
                
            except json.JSONDecodeError as e:
                results[str(spec_file)] = (False, [f"JSON decode error: {e}"], [])
            except Exception as e:
                results[str(spec_file)] = (False, [f"Unexpected error: {e}"], [])
        
        return results
    
    def generate_validation_report(self, results: Dict[str, Tuple[bool, List[str], List[str]]]) -> str:
        """Generate a human-readable validation report."""
        report_lines = []
        report_lines.append("Meta Property Validation Report")
        report_lines.append("=" * 35)
        report_lines.append("")
        
        total_files = len(results)
        valid_files = sum(1 for is_valid, _, _ in results.values() if is_valid)
        
        report_lines.append(f"Total files validated: {total_files}")
        report_lines.append(f"Valid files: {valid_files}")
        report_lines.append(f"Invalid files: {total_files - valid_files}")
        report_lines.append("")
        
        for file_path, (is_valid, errors, warnings) in results.items():
            filename = Path(file_path).name
            status = "✓ VALID" if is_valid else "✗ INVALID"
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


    def meta_data_validator_main():
        """Main function to run validation on sample inputs."""
        script_dir = Path(__file__).parent.parent
        sample_inputs_dir = script_dir / "sample_inputs"
        
        validator = MetaValidator()
        
        try:
            results = validator.validate_sample_files(str(sample_inputs_dir))
            report = validator.generate_validation_report(results)
            print(report)
            
            # Return appropriate exit code
            invalid_count = sum(1 for is_valid, _, _ in results.values() if not is_valid)
            exit(1 if invalid_count > 0 else 0)
            
        except Exception as e:
            print(f"Error running validation: {e}")
            exit(1)
