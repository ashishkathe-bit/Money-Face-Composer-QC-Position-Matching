import pytest
import json
import tempfile
from pathlib import Path
from validators.universe_validator import UniverseValidator


# Global fixtures
@pytest.fixture
def validator():
    """Create a fresh UniverseValidator instance for each test."""
    return UniverseValidator()

@pytest.fixture
def valid_universe():
    """Sample valid universe data."""
    return [
        {
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "assetClass": "ETF"
        },
        {
            "symbol": "TQQQ",
            "name": "ProShares UltraPro QQQ",
            "assetClass": "ETF"
        },
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "assetClass": "EQUITY"
        }
    ]

@pytest.fixture
def minimal_valid_universe():
    """Minimal valid universe with only required fields."""
    return [
        {"symbol": "SPY"},
        {"symbol": "TQQQ"}
    ]

@pytest.fixture
def temp_sample_dir(tmp_path):
    """Create a temporary directory structure with sample files."""
    sample_dir = tmp_path / "sample_inputs"
    strategy_dir = sample_dir / "test_strategy"
    strategy_dir.mkdir(parents=True)
    return sample_dir


class TestValidateUniverseProperty:
    
    def test_valid_universe_complete(self, validator, valid_universe):
        """Test validation with complete valid universe."""
        is_valid, errors, warnings = validator.validate_universe_property(valid_universe)
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 0
    
    def test_valid_universe_minimal(self, validator, minimal_valid_universe):
        """Test validation with minimal valid universe."""
        is_valid, errors, warnings = validator.validate_universe_property(minimal_valid_universe)
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 0
    
    def test_universe_not_list(self, validator):
        """Test validation fails when universe is not a list."""
        test_cases = [None, {}, "string", 123, True]
        
        for universe in test_cases:
            is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
            assert is_valid is False
            assert any("Universe must be an array" in error for error in errors)
    
    def test_universe_empty_list(self, validator):
        """Test validation fails for empty universe."""
        is_valid, errors, warnings = validator.validate_universe_property([], "test.json")
        
        assert is_valid is False
        assert any("Universe must contain at least one asset" in error for error in errors)


class TestAssetValidation:
    
    def test_asset_not_dict(self, validator):
        """Test validation fails when asset is not a dictionary."""
        test_cases = [None, [], "SPY", 123, True]
        
        for asset in test_cases:
            universe = [asset]
            is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
            assert is_valid is False
            assert any("Asset must be an object" in error for error in errors)
    
    def test_asset_missing_symbol(self, validator):
        """Test validation fails when symbol is missing."""
        universe = [{"name": "Test Asset"}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("Missing required field 'symbol'" in error for error in errors)
    
    def test_asset_with_all_fields(self, validator):
        """Test validation passes with all valid fields."""
        universe = [{
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "assetClass": "EQUITY"
        }]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert errors == []


class TestSymbolValidation:
    
    @pytest.mark.parametrize("valid_symbol", [
        "SPY", "AAPL", "TQQQ", "BRK.B", "BTC-USD", "ES:DEC23", "A1B2C3", "X"
    ])
    def test_valid_symbols(self, validator, valid_symbol):
        """Test various valid symbol formats."""
        universe = [{"symbol": valid_symbol}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("symbol" in error and "does not match required pattern" in error for error in errors)
    
    def test_symbol_not_string(self, validator):
        """Test validation fails for non-string symbol."""
        test_cases = [123, [], {}, True, None]
        
        for symbol in test_cases:
            universe = [{"symbol": symbol}]
            is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
            assert is_valid is False
            assert any("symbol must be a string" in error for error in errors)
    
    def test_symbol_empty_string(self, validator):
        """Test validation fails for empty symbol."""
        universe = [{"symbol": ""}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("symbol cannot be empty" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_symbol", [
        "A" * 21,  # Too long
        "SPY@",    # Invalid character
        "A B",     # Space not allowed
        "TEST#",   # Hash not allowed
        "SYM%",    # Percent not allowed
        "A&B",     # Ampersand not allowed
    ])
    def test_invalid_symbol_patterns(self, validator, invalid_symbol):
        """Test validation fails for invalid symbol patterns."""
        universe = [{"symbol": invalid_symbol}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("does not match required pattern" in error for error in errors)
    
    def test_duplicate_symbols_warning(self, validator):
        """Test warning for duplicate symbols."""
        universe = [
            {"symbol": "SPY"},
            {"symbol": "AAPL"},
            {"symbol": "SPY"}  # Duplicate
        ]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert any("Duplicate symbol 'SPY' found" in warning for warning in warnings)
    
    def test_symbol_max_length(self, validator):
        """Test symbol at maximum allowed length."""
        universe = [{"symbol": "A" * 20}]  # Exactly 20 characters
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("does not match required pattern" in error for error in errors)


class TestNameValidation:
    
    def test_valid_name_string(self, validator):
        """Test valid name field."""
        universe = [{"symbol": "AAPL", "name": "Apple Inc."}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("name" in error for error in errors)
    
    def test_name_optional(self, validator):
        """Test that name field is optional."""
        universe = [{"symbol": "AAPL"}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("name" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_name", [123, [], {}, True])
    def test_name_invalid_types(self, validator, invalid_name):
        """Test validation fails for non-string name types."""
        universe = [{"symbol": "AAPL", "name": invalid_name}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("name must be a string" in error for error in errors)
    
    def test_name_none_allowed(self, validator):
        """Test that None name is allowed."""
        universe = [{"symbol": "AAPL", "name": None}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("name must be a string" in error for error in errors)
    
    def test_name_empty_string_allowed(self, validator):
        """Test that empty string name is allowed."""
        universe = [{"symbol": "AAPL", "name": ""}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("name" in error for error in errors)


class TestAssetClassValidation:
    
    @pytest.mark.parametrize("valid_asset_class", [
        "EQUITY", "ETF", "FUTURE", "FOREX", "CRYPTO", "OPTION", "BOND", "COMMODITY"
    ])
    def test_valid_asset_classes(self, validator, valid_asset_class):
        """Test all valid asset class values."""
        universe = [{"symbol": "TEST", "assetClass": valid_asset_class}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("assetClass" in error for error in errors)
    
    def test_asset_class_optional(self, validator):
        """Test that assetClass is optional."""
        universe = [{"symbol": "AAPL"}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("assetClass" in error for error in errors)
    
    def test_asset_class_invalid_value(self, validator):
        """Test validation fails for invalid asset class."""
        universe = [{"symbol": "AAPL", "assetClass": "STOCK"}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("assetClass 'STOCK' is not valid" in error for error in errors)
        assert any("Valid options:" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_asset_class", [123, [], {}, True])
    def test_asset_class_invalid_types(self, validator, invalid_asset_class):
        """Test validation fails for non-string asset class types."""
        universe = [{"symbol": "AAPL", "assetClass": invalid_asset_class}]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is False
        assert any("assetClass must be a string" in error for error in errors)
    
    def test_asset_class_none_allowed(self, validator):
        """Test that None asset class is allowed."""
        universe = [{"symbol": "AAPL", "assetClass": None}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        
        assert is_valid is True
        assert not any("assetClass" in error for error in errors)
    
    def test_asset_class_case_sensitive(self, validator):
        """Test that asset class validation is case sensitive."""
        test_cases = ["equity", "etf", "Equity", "Etf"]
        
        for asset_class in test_cases:
            universe = [{"symbol": "AAPL", "assetClass": asset_class}]
            is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
            assert is_valid is False
            assert any(f"assetClass '{asset_class}' is not valid" in error for error in errors)


class TestAdditionalProperties:
    
    def test_common_additional_properties_warning(self, validator):
        """Test warning for common additional properties."""
        universe = [{
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "currency": "USD",
            "market": "US"
        }]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 4  # All common additional properties
        assert all("common but not in schema" in warning for warning in warnings)
    
    def test_unexpected_additional_property_warning(self, validator):
        """Test warning for unexpected additional properties."""
        universe = [{
            "symbol": "AAPL",
            "unexpectedField": "value"
        }]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 1
        assert "Unexpected additional property 'unexpectedField'" in warnings[0]
    
    def test_multiple_additional_properties(self, validator):
        """Test multiple additional properties generate multiple warnings."""
        universe = [{
            "symbol": "AAPL",
            "exchange": "NASDAQ",  # Common
            "customField": "value",  # Unexpected
            "anotherField": "value2"  # Unexpected
        }]
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 3


class TestValidateSampleFiles:
    
    def test_validate_sample_files_success(self, validator, temp_sample_dir, valid_universe):
        """Test successful validation of sample files."""
        strategy_dir = temp_sample_dir / "test_strategy"
        spec_file = strategy_dir / "spec_test.json"
        
        valid_spec = {"universe": valid_universe}
        spec_file.write_text(json.dumps(valid_spec, indent=2))
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 1
        file_path = str(spec_file)
        assert file_path in results
        is_valid, errors, warnings = results[file_path]
        assert is_valid is True
        assert errors == []
    
    def test_validate_sample_files_invalid_json(self, validator, temp_sample_dir):
        """Test handling of invalid JSON files."""
        strategy_dir = temp_sample_dir / "test_strategy"
        spec_file = strategy_dir / "spec_test.json"
        
        spec_file.write_text('{"invalid": json}')
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 1
        file_path = str(spec_file)
        is_valid, errors, warnings = results[file_path]
        assert is_valid is False
        assert any("JSON decode error" in error for error in errors)
    
    def test_validate_sample_files_no_universe(self, validator, temp_sample_dir):
        """Test handling of files without universe property."""
        strategy_dir = temp_sample_dir / "test_strategy"
        spec_file = strategy_dir / "spec_test.json"
        
        spec_file.write_text('{"other_property": "value"}')
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 1
        file_path = str(spec_file)
        is_valid, errors, warnings = results[file_path]
        assert is_valid is False
        assert any("No 'universe' property found" in error for error in errors)
    
    def test_validate_sample_files_nonexistent_directory(self, validator):
        """Test handling of nonexistent directory."""
        with pytest.raises(FileNotFoundError, match="Sample inputs directory not found"):
            validator.validate_sample_files("/nonexistent/directory")
    
    def test_validate_sample_files_empty_directory(self, validator, temp_sample_dir):
        """Test handling of directory with no spec files."""
        results = validator.validate_sample_files(str(temp_sample_dir))
        assert len(results) == 0
    
    def test_validate_sample_files_multiple_files(self, validator, temp_sample_dir):
        """Test validation of multiple spec files."""
        for i in range(3):
            strategy_dir = temp_sample_dir / f"strategy_{i}"
            strategy_dir.mkdir()
            spec_file = strategy_dir / f"spec_strategy_{i}.json"
            
            spec_data = {
                "universe": [{"symbol": f"SYM{i}"}]
            }
            spec_file.write_text(json.dumps(spec_data, indent=2))
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 3
        for file_path, (is_valid, errors, warnings) in results.items():
            assert is_valid is True
            assert errors == []


class TestGenerateValidationReport:
    
    def test_generate_validation_report_all_valid(self, validator):
        """Test report generation for all valid files."""
        results = {
            "file1.json": (True, [], []),
            "file2.json": (True, [], [])
        }
        
        report = validator.generate_validation_report(results)
        
        assert "Total files validated: 2" in report
        assert "Valid files: 2" in report
        assert "Invalid files: 0" in report
        assert "[VALID]: file1.json" in report
        assert "[VALID]: file2.json" in report
    
    def test_generate_validation_report_with_errors(self, validator):
        """Test report generation with errors and warnings."""
        results = {
            "valid.json": (True, [], ["Warning 1"]),
            "invalid.json": (False, ["Error 1", "Error 2"], [])
        }
        
        report = validator.generate_validation_report(results)
        
        assert "Total files validated: 2" in report
        assert "Valid files: 1" in report
        assert "Invalid files: 1" in report
        assert "[VALID]: valid.json" in report
        assert "[INVALID]: invalid.json" in report
        assert "ERROR: Error 1" in report
        assert "ERROR: Error 2" in report
        assert "WARNING: Warning 1" in report
    
    def test_generate_validation_report_empty_results(self, validator):
        """Test report generation with no files."""
        results = {}
        report = validator.generate_validation_report(results)
        
        assert "Total files validated: 0" in report
        assert "Valid files: 0" in report
        assert "Invalid files: 0" in report


class TestValidatorConstants:
    
    def test_valid_asset_classes_constant(self, validator):
        """Test that VALID_ASSET_CLASSES contains expected values."""
        expected_classes = {
            "EQUITY", "ETF", "FUTURE", "FOREX", "CRYPTO", "OPTION", "BOND", "COMMODITY"
        }
        assert validator.VALID_ASSET_CLASSES == expected_classes
    
    def test_symbol_pattern_constant(self, validator):
        """Test SYMBOL_PATTERN regex."""
        valid_symbols = ["SPY", "AAPL", "BRK.B", "BTC-USD", "ES:DEC23", "A1B2C3"]
        invalid_symbols = ["", "A" * 21, "SPY@", "A B", "TEST#"]
        
        for symbol in valid_symbols:
            assert validator.SYMBOL_PATTERN.match(symbol) is not None
        
        for symbol in invalid_symbols:
            assert validator.SYMBOL_PATTERN.match(symbol) is None


class TestIntegration:
    
    def test_full_validation_workflow(self, validator, temp_sample_dir):
        """Test complete validation workflow with mixed valid/invalid files."""
        test_cases = [
            # Valid file
            {
                "dir": "valid_strategy",
                "file": "spec_valid.json",
                "content": {
                    "universe": [
                        {"symbol": "SPY", "name": "SPDR S&P 500", "assetClass": "ETF"},
                        {"symbol": "AAPL", "assetClass": "EQUITY"}
                    ]
                }
            },
            # Invalid file - empty universe
            {
                "dir": "invalid_strategy1",
                "file": "spec_empty.json",
                "content": {
                    "universe": []
                }
            },
            # Invalid file - invalid symbol pattern
            {
                "dir": "invalid_strategy2",
                "file": "spec_bad_symbol.json",
                "content": {
                    "universe": [{"symbol": "SPY@"}]
                }
            }
        ]
        
        for case in test_cases:
            strategy_dir = temp_sample_dir / case["dir"]
            strategy_dir.mkdir()
            spec_file = strategy_dir / case["file"]
            spec_file.write_text(json.dumps(case["content"], indent=2))
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 3
        
        valid_count = sum(1 for is_valid, _, _ in results.values() if is_valid)
        invalid_count = sum(1 for is_valid, _, _ in results.values() if not is_valid)
        
        assert valid_count == 1
        assert invalid_count == 2
        
        report = validator.generate_validation_report(results)
        assert "Total files validated: 3" in report
        assert "Valid files: 1" in report
        assert "Invalid files: 2" in report
    
    def test_complex_universe_validation(self, validator):
        """Test validation of complex universe with various scenarios."""
        universe = [
            # Valid basic asset
            {"symbol": "SPY"},
            # Valid complete asset
            {"symbol": "AAPL", "name": "Apple Inc.", "assetClass": "EQUITY"},
            # Asset with common additional properties
            {"symbol": "GOOGL", "exchange": "NASDAQ", "sector": "Technology"},
            # Asset with unexpected properties
            {"symbol": "MSFT", "customField": "value"},
            # Duplicate symbol (should warn)
            {"symbol": "SPY", "name": "Duplicate SPY"}
        ]
        
        is_valid, errors, warnings = validator.validate_universe_property(universe, "test.json")
        
        # Should be valid overall
        assert is_valid is True
        assert errors == []
        
        # Should have warnings for additional properties and duplicate
        assert len(warnings) >= 3
        assert any("Duplicate symbol 'SPY'" in warning for warning in warnings)
        assert any("common but not in schema" in warning for warning in warnings)
        assert any("Unexpected additional property" in warning for warning in warnings)
    
    def test_edge_cases(self, validator):
        """Test various edge cases."""
        # Test with maximum length symbol
        universe = [{"symbol": "A" * 20}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        assert is_valid is True
        
        # Test with special characters in symbol
        universe = [{"symbol": "BRK.B"}, {"symbol": "BTC-USD"}, {"symbol": "ES:DEC23"}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        assert is_valid is True
        
        # Test with None values for optional fields
        universe = [{"symbol": "TEST", "name": None, "assetClass": None}]
        is_valid, errors, warnings = validator.validate_universe_property(universe)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])