import pytest
from datetime import datetime
from validators.settings_validator import SettingsValidator


# Global fixtures available to all test classes
@pytest.fixture
def validator():
    """Create a fresh SettingsValidator instance for each test."""
    return SettingsValidator()

@pytest.fixture
def valid_settings():
    """Sample valid settings data."""
    return {
        "capital": 100000,
        "rebalance": "monthly",
        "start": "2020-01-01",
        "end": "2023-12-31",
        "currency": "USD",
        "fees": {
            "perOrder": 5.0,
            "perShare": 0.01,
            "percentage": 0.001
        },
        "slippage": {
            "model": "fixed",
            "value": 0.001
        }
    }

@pytest.fixture
def minimal_valid_settings():
    """Minimal valid settings with only required fields."""
    return {
        "capital": 50000,
        "rebalance": "daily",
        "start": "2021-01-01",
        "end": "2021-12-31"
    }


class TestValidateSettings:
    
    def test_valid_settings_complete(self, validator, valid_settings):
        """Test validation with complete valid settings."""
        is_valid, errors = validator.validate_settings(valid_settings)
        
        assert is_valid is True
        assert errors == []
    
    def test_valid_settings_minimal(self, validator, minimal_valid_settings):
        """Test validation with minimal required fields."""
        is_valid, errors = validator.validate_settings(minimal_valid_settings)
        
        assert is_valid is True
        assert errors == []
    
    def test_settings_not_dict(self, validator):
        """Test validation fails when settings is not a dictionary."""
        test_cases = [None, [], "string", 123, True]
        
        for settings in test_cases:
            is_valid, errors = validator.validate_settings(settings)
            assert is_valid is False
            assert any("Settings must be a dictionary/object" in error for error in errors)
    
    def test_empty_settings(self, validator):
        """Test validation with empty settings dictionary."""
        is_valid, errors = validator.validate_settings({})
        
        assert is_valid is False
        assert any("Capital is required" in error for error in errors)
        assert any("Rebalance is required" in error for error in errors)
        assert any("Start is required" in error for error in errors)
        assert any("End is required" in error for error in errors)


class TestCapitalValidation:
    
    def test_valid_capital_integer(self, validator):
        """Test valid integer capital."""
        settings = {"capital": 100000, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Capital" in error for error in errors)
    
    def test_valid_capital_float(self, validator):
        """Test valid float capital."""
        settings = {"capital": 100000.50, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Capital" in error for error in errors)
    
    def test_valid_capital_zero(self, validator):
        """Test capital with zero value (should be valid)."""
        settings = {"capital": 0, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Capital" in error for error in errors)
    
    def test_missing_capital(self, validator):
        """Test validation fails when capital is missing."""
        settings = {"rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Capital is required" in error for error in errors)
    
    def test_capital_none(self, validator):
        """Test validation fails when capital is None."""
        settings = {"capital": None, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Capital is required" in error for error in errors)
    
    def test_capital_negative(self, validator):
        """Test validation fails for negative capital."""
        settings = {"capital": -1000, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Capital must be greater than or equal to 0" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_capital", [
        "100000", [], {}, True, False
    ])
    def test_capital_invalid_types(self, validator, invalid_capital):
        """Test validation fails for non-numeric capital types."""
        settings = {"capital": invalid_capital, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Capital must be a number" in error for error in errors)


class TestRebalanceValidation:
    
    @pytest.mark.parametrize("valid_rebalance", [
        "none", "intraday", "daily", "weekly", "monthly", "quarterly", "yearly"
    ])
    def test_valid_rebalance_values(self, validator, valid_rebalance):
        """Test all valid rebalance values."""
        settings = {"capital": 100000, "rebalance": valid_rebalance, "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Rebalance" in error for error in errors)
    
    def test_missing_rebalance(self, validator):
        """Test validation fails when rebalance is missing."""
        settings = {"capital": 100000, "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Rebalance is required" in error for error in errors)
    
    def test_rebalance_none(self, validator):
        """Test validation fails when rebalance is None."""
        settings = {"capital": 100000, "rebalance": None, "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Rebalance is required" in error for error in errors)
    
    def test_invalid_rebalance_value(self, validator):
        """Test validation fails for invalid rebalance value."""
        settings = {"capital": 100000, "rebalance": "invalid", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Rebalance must be one of:" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_rebalance", [
        123, [], {}, True, False
    ])
    def test_rebalance_invalid_types(self, validator, invalid_rebalance):
        """Test validation fails for non-string rebalance types."""
        settings = {"capital": 100000, "rebalance": invalid_rebalance, "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Rebalance must be a string" in error for error in errors)


class TestDateValidation:
    
    @pytest.mark.parametrize("valid_date", [
        "2020-01-01", "2023-12-31", "2000-02-29", "1999-01-01"
    ])
    def test_valid_date_formats(self, validator, valid_date):
        """Test various valid date formats."""
        settings = {"capital": 100000, "rebalance": "daily", "start": valid_date, "end": "2023-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        # Should not have date format errors (may have other errors)
        assert not any("date must be in YYYY-MM-DD format" in error for error in errors)
    
    def test_missing_start_date(self, validator):
        """Test validation fails when start date is missing."""
        settings = {"capital": 100000, "rebalance": "daily", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Start is required" in error for error in errors)
    
    def test_missing_end_date(self, validator):
        """Test validation fails when end date is missing."""
        settings = {"capital": 100000, "rebalance": "daily", "start": "2020-01-01"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("End is required" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_date", [
        "2020/01/01", "01-01-2020", "2020-1-1", "2020-13-01", "2020-02-30", "invalid", ""
    ])
    def test_invalid_date_formats(self, validator, invalid_date):
        """Test various invalid date formats."""
        settings = {"capital": 100000, "rebalance": "daily", "start": invalid_date, "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("date must be in YYYY-MM-DD format" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_date_type", [
        123, [], {}, True, None
    ])
    def test_date_invalid_types(self, validator, invalid_date_type):
        """Test validation fails for non-string date types."""
        settings = {"capital": 100000, "rebalance": "daily", "start": invalid_date_type, "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        if invalid_date_type is None:
            assert any("Start is required" in error for error in errors)
        else:
            assert any("Start date must be a string" in error for error in errors)
    
    def test_start_after_end_date(self, validator):
        """Test validation fails when start date is after end date."""
        settings = {
            "capital": 100000, 
            "rebalance": "daily", 
            "start": "2020-12-31", 
            "end": "2020-01-01"
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Start date must be on or before end date" in error for error in errors)
    
    def test_start_equals_end_date(self, validator):
        """Test validation passes when start date equals end date."""
        settings = {
            "capital": 100000, 
            "rebalance": "daily", 
            "start": "2020-01-01", 
            "end": "2020-01-01"
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Start date must be on or before end date" in error for error in errors)


class TestCurrencyValidation:
    
    @pytest.mark.parametrize("valid_currency", [
        "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"
    ])
    def test_valid_currencies(self, validator, valid_currency):
        """Test various valid currency codes."""
        settings = {
            "capital": 100000, 
            "rebalance": "daily", 
            "start": "2020-01-01", 
            "end": "2020-12-31",
            "currency": valid_currency
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Currency" in error for error in errors)
    
    def test_currency_optional(self, validator):
        """Test that currency is optional."""
        settings = {"capital": 100000, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Currency" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_currency", [
        "usd", "US", "USDX", "12D", "", "U$D"
    ])
    def test_invalid_currency_formats(self, validator, invalid_currency):
        """Test various invalid currency formats."""
        settings = {
            "capital": 100000, 
            "rebalance": "daily", 
            "start": "2020-01-01", 
            "end": "2020-12-31",
            "currency": invalid_currency
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Currency must be a 3-letter uppercase code" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_currency_type", [
        123, [], {}, True
    ])
    def test_currency_invalid_types(self, validator, invalid_currency_type):
        """Test validation fails for non-string currency types."""
        settings = {
            "capital": 100000, 
            "rebalance": "daily", 
            "start": "2020-01-01", 
            "end": "2020-12-31",
            "currency": invalid_currency_type
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Currency must be a string" in error for error in errors)


class TestFeesValidation:
    
    def test_valid_fees_complete(self, validator):
        """Test validation with all fee fields."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {
                "perOrder": 5.0,
                "perShare": 0.01,
                "percentage": 0.001
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Fee" in error for error in errors)
    
    def test_valid_fees_partial(self, validator):
        """Test validation with some fee fields."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {
                "perOrder": 5.0
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Fee" in error for error in errors)
    
    def test_fees_optional(self, validator):
        """Test that fees field is optional."""
        settings = {"capital": 100000, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Fees" in error for error in errors)
    
    def test_fees_not_dict(self, validator):
        """Test validation fails when fees is not a dictionary."""
        test_cases = ["string", 123, [], True]
        
        for fees in test_cases:
            settings = {
                "capital": 100000,
                "rebalance": "daily",
                "start": "2020-01-01",
                "end": "2020-12-31",
                "fees": fees
            }
            is_valid, errors = validator.validate_settings(settings)
            assert is_valid is False
            assert any("Fees must be an object/dictionary" in error for error in errors)
    
    def test_fees_empty_dict(self, validator):
        """Test validation passes with empty fees dictionary."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Fee" in error for error in errors)
    
    @pytest.mark.parametrize("fee_field", ["perOrder", "perShare"])
    def test_valid_fee_fields(self, validator, fee_field):
        """Test valid fee field values."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {fee_field: 5.0}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any(f"Fee {fee_field}" in error for error in errors)
    
    @pytest.mark.parametrize("fee_field", ["perOrder", "perShare"])
    def test_fee_fields_zero_value(self, validator, fee_field):
        """Test fee fields with zero value (should be valid)."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {fee_field: 0}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any(f"Fee {fee_field}" in error for error in errors)
    
    @pytest.mark.parametrize("fee_field", ["perOrder", "perShare"])
    def test_fee_fields_negative(self, validator, fee_field):
        """Test validation fails for negative fee values."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {fee_field: -1.0}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any(f"Fee {fee_field} must be greater than or equal to 0" in error for error in errors)
    
    @pytest.mark.parametrize("fee_field,invalid_value", [
        ("perOrder", "5.0"),
        ("perOrder", []),
        ("perOrder", {}),
        ("perOrder", True),
        ("perShare", "0.01"),
        ("perShare", []),
        ("perShare", {}),
        ("perShare", False)
    ])
    def test_fee_fields_invalid_types(self, validator, fee_field, invalid_value):
        """Test validation fails for non-numeric fee types."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {fee_field: invalid_value}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any(f"Fee {fee_field} must be a number" in error for error in errors)
    
    def test_percentage_fee_valid_range(self, validator):
        """Test valid percentage fee values (0 to 1)."""
        valid_percentages = [0, 0.5, 1, 0.001, 0.999]
        
        for percentage in valid_percentages:
            settings = {
                "capital": 100000,
                "rebalance": "daily",
                "start": "2020-01-01",
                "end": "2020-12-31",
                "fees": {"percentage": percentage}
            }
            is_valid, errors = validator.validate_settings(settings)
            
            assert is_valid is True
            assert not any("Fee percentage" in error for error in errors)
    
    def test_percentage_fee_too_high(self, validator):
        """Test validation fails for percentage fee > 1."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {"percentage": 1.5}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Fee percentage must be less than or equal to 1" in error for error in errors)
    
    def test_percentage_fee_negative(self, validator):
        """Test validation fails for negative percentage fee."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {"percentage": -0.1}
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Fee percentage must be greater than or equal to 0" in error for error in errors)
    
    def test_fees_unknown_fields(self, validator):
        """Test validation fails for unknown fee fields."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "fees": {
                "perOrder": 5.0,
                "unknownField": 10.0,
                "anotherUnknown": 20.0
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Unknown fee fields:" in error for error in errors)


class TestSlippageValidation:
    
    @pytest.mark.parametrize("valid_model", ["fixed", "percentage", "volumeImpact"])
    def test_valid_slippage_models(self, validator, valid_model):
        """Test all valid slippage models."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": valid_model,
                "value": 0.001
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Slippage" in error for error in errors)
    
    def test_slippage_optional(self, validator):
        """Test that slippage field is optional."""
        settings = {"capital": 100000, "rebalance": "daily", "start": "2020-01-01", "end": "2020-12-31"}
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is True
        assert not any("Slippage" in error for error in errors)
    
    def test_slippage_not_dict(self, validator):
        """Test validation fails when slippage is not a dictionary."""
        test_cases = ["string", 123, [], True]
        
        for slippage in test_cases:
            settings = {
                "capital": 100000,
                "rebalance": "daily",
                "start": "2020-01-01",
                "end": "2020-12-31",
                "slippage": slippage
            }
            is_valid, errors = validator.validate_settings(settings)
            assert is_valid is False
            assert any("Slippage must be an object/dictionary" in error for error in errors)
    
    def test_invalid_slippage_model(self, validator):
        """Test validation fails for invalid slippage model."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": "invalid",
                "value": 0.001
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Slippage model must be one of:" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_model_type", [123, [], {}, True])
    def test_slippage_model_invalid_types(self, validator, invalid_model_type):
        """Test validation fails for non-string slippage model types."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": invalid_model_type,
                "value": 0.001
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Slippage model must be a string" in error for error in errors)
    
    def test_valid_slippage_values(self, validator):
        """Test valid slippage value range."""
        valid_values = [0, 0.001, 1.0, 10.5]
        
        for value in valid_values:
            settings = {
                "capital": 100000,
                "rebalance": "daily",
                "start": "2020-01-01",
                "end": "2020-12-31",
                "slippage": {
                    "model": "fixed",
                    "value": value
                }
            }
            is_valid, errors = validator.validate_settings(settings)
            
            assert is_valid is True
            assert not any("Slippage value" in error for error in errors)
    
    def test_negative_slippage_value(self, validator):
        """Test validation fails for negative slippage value."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": "fixed",
                "value": -0.001
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Slippage value must be greater than or equal to 0" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_value_type", ["0.001", [], {}, True])
    def test_slippage_value_invalid_types(self, validator, invalid_value_type):
        """Test validation fails for non-numeric slippage value types."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": "fixed",
                "value": invalid_value_type
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Slippage value must be a number" in error for error in errors)
    
    def test_slippage_unknown_fields(self, validator):
        """Test validation fails for unknown slippage fields."""
        settings = {
            "capital": 100000,
            "rebalance": "daily",
            "start": "2020-01-01",
            "end": "2020-12-31",
            "slippage": {
                "model": "fixed",
                "value": 0.001,
                "unknownField": "unknown"
            }
        }
        is_valid, errors = validator.validate_settings(settings)
        
        assert is_valid is False
        assert any("Unknown slippage fields:" in error for error in errors)


class TestValidateSettingsStructure:
    
    def test_valid_structure(self, validator, valid_settings):
        """Test validation of valid settings structure."""
        data = {"settings": valid_settings}
        is_valid, errors = validator.validate_settings_structure(data)
        
        assert is_valid is True
        assert errors == []
    
    def test_missing_settings_property(self, validator):
        """Test validation fails when settings property is missing."""
        data = {"other_property": "value"}
        is_valid, errors = validator.validate_settings_structure(data)
        
        assert is_valid is False
        assert any("Settings property is required" in error for error in errors)
    
    def test_data_not_dict(self, validator):
        """Test validation fails when data is not a dictionary."""
        test_cases = [None, [], "string", 123, True]
        
        for data in test_cases:
            is_valid, errors = validator.validate_settings_structure(data)
            assert is_valid is False
            assert any("StrategySpec must be a dictionary/object" in error for error in errors)


class TestGetValidationSummary:
    
    def test_validation_summary_valid(self, validator, valid_settings):
        """Test validation summary for valid settings."""
        summary = validator.get_validation_summary(valid_settings)
        
        assert summary['is_valid'] is True
        assert summary['error_count'] == 0
        assert summary['errors'] == []
        assert summary['required_fields_present']['capital'] is True
        assert summary['required_fields_present']['rebalance'] is True
        assert summary['optional_fields_present']['currency'] is True
        assert summary['optional_fields_present']['fees'] is True
        assert summary['optional_fields_present']['slippage'] is True
    
    def test_validation_summary_minimal(self, validator, minimal_valid_settings):
        """Test validation summary for minimal settings."""
        summary = validator.get_validation_summary(minimal_valid_settings)
        
        assert summary['is_valid'] is True
        assert summary['error_count'] == 0
        assert summary['required_fields_present']['capital'] is True
        assert summary['required_fields_present']['rebalance'] is True