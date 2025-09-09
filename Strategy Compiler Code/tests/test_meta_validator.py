import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from validators.meta_validator import MetaValidator


# Global fixtures available to all test classes
@pytest.fixture
def validator():
    """Create a fresh MetaValidator instance for each test."""
    return MetaValidator()

@pytest.fixture
def valid_meta():
    """Sample valid meta data."""
    return {
        "name": "Test Strategy",
        "version": "1.0.0",
        "description": "A test strategy for validation",
        "category": "momentum"
    }

@pytest.fixture
def temp_sample_dir(tmp_path):
    """Create a temporary directory structure with sample files."""
    sample_dir = tmp_path / "sample_inputs"
    strategy_dir = sample_dir / "test_strategy"
    strategy_dir.mkdir(parents=True)
    return sample_dir


class TestMetaValidator:
    pass


class TestValidateMetaProperty:
    
    def test_valid_meta_minimal(self, validator):
        """Test validation with minimal required fields."""
        meta = {"name": "Test", "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 0
    
    def test_valid_meta_complete(self, validator, valid_meta):
        """Test validation with all valid fields."""
        is_valid, errors, warnings = validator.validate_meta_property(valid_meta)
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 0
    
    def test_missing_required_name(self, validator):
        """Test validation fails when name is missing."""
        meta = {"version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("Missing required field 'name'" in error for error in errors)
    
    def test_missing_required_version(self, validator):
        """Test validation fails when version is missing."""
        meta = {"name": "Test Strategy"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("Missing required field 'version'" in error for error in errors)
    
    def test_missing_both_required_fields(self, validator):
        """Test validation fails when both required fields are missing."""
        meta = {"description": "Some description"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("Missing required field 'name' in meta" in error for error in errors)
        assert any("Missing required field 'version' in meta" in error for error in errors)


class TestNameValidation:
    
    def test_valid_name_min_length(self, validator):
        """Test name with minimum valid length."""
        meta = {"name": "A", "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    def test_valid_name_max_length(self, validator):
        """Test name with maximum valid length."""
        meta = {"name": "A" * 500, "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    def test_empty_name(self, validator):
        """Test validation fails for empty name."""
        meta = {"name": "", "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("cannot be empty" in error for error in errors)
    
    def test_name_too_long(self, validator):
        """Test validation fails for name exceeding 500 characters."""
        meta = {"name": "A" * 501, "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("exceeds maximum length of 500 characters" in error for error in errors)
    
    def test_name_wrong_type(self, validator):
        """Test validation fails for non-string name."""
        meta = {"name": 123, "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("must be a string, got int" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_name", [None, [], {}, 42, True])
    def test_name_invalid_types(self, validator, invalid_name):
        """Test validation fails for various invalid name types."""
        meta = {"name": invalid_name, "version": "1.0"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("must be a string" in error for error in errors)


class TestVersionValidation:
    
    @pytest.mark.parametrize("valid_version", [
        "1.0", "2.1", "10.25", "1.0.0", "2.1.3", "10.25.100"
    ])
    def test_valid_version_patterns(self, validator, valid_version):
        """Test various valid version patterns."""
        meta = {"name": "Test", "version": valid_version}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    @pytest.mark.parametrize("invalid_version", [
        "1", "1.", ".1", "1.0.", "1.0.0.", "v1.0", "1.0.0.0", 
        "1.a", "a.1", "1.0.a", "", "1.0-beta", "1.0.0-alpha"
    ])
    def test_invalid_version_patterns(self, validator, invalid_version):
        """Test various invalid version patterns."""
        meta = {"name": "Test", "version": invalid_version}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("does not match required pattern" in error for error in errors)
    
    def test_version_wrong_type(self, validator):
        """Test validation fails for non-string version."""
        meta = {"name": "Test", "version": 1.0}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("must be a string, got float" in error for error in errors)


class TestDescriptionValidation:
    
    def test_valid_description(self, validator):
        """Test valid description field."""
        meta = {
            "name": "Test", 
            "version": "1.0", 
            "description": "A valid description"
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    def test_description_max_length(self, validator):
        """Test description at maximum allowed length."""
        meta = {
            "name": "Test", 
            "version": "1.0", 
            "description": "A" * 5000
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    def test_description_too_long(self, validator):
        """Test description exceeding maximum length."""
        meta = {
            "name": "Test", 
            "version": "1.0", 
            "description": "A" * 5001
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("exceeds maximum length of 5000 characters" in error for error in errors)
    
    def test_description_wrong_type(self, validator):
        """Test validation fails for non-string description."""
        meta = {"name": "Test", "version": "1.0", "description": 123}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("must be a string, got int" in error for error in errors)
    
    def test_description_none_allowed(self, validator):
        """Test that None description is allowed (optional field)."""
        meta = {"name": "Test", "version": "1.0", "description": None}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []


class TestCategoryValidation:
    
    @pytest.mark.parametrize("valid_category", [
        "momentum", "mean_reversion", "trend_following", "arbitrage",
        "market_neutral", "long_short", "buy_hold", "tactical", "other"
    ])
    def test_valid_categories(self, validator, valid_category):
        """Test all valid category values."""
        meta = {"name": "Test", "version": "1.0", "category": valid_category}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
    
    def test_invalid_category(self, validator):
        """Test invalid category value."""
        meta = {"name": "Test", "version": "1.0", "category": "invalid_category"}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("is not a valid category" in error for error in errors)
        assert any("Valid options:" in error for error in errors)
    
    def test_category_wrong_type(self, validator):
        """Test validation fails for non-string category."""
        meta = {"name": "Test", "version": "1.0", "category": 123}
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is False
        assert any("must be a string, got int" in error for error in errors)
    
    def test_category_none_allowed(self, validator):
        """Test that None category is allowed (optional field)."""
        meta = {"name": "Test", "version": "1.0", "category": None}
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []


class TestAdditionalProperties:
    
    def test_expected_additional_properties_no_warning(self, validator):
        """Test that expected additional properties don't generate warnings."""
        meta = {
            "name": "Test",
            "version": "1.0",
            "source": "test_source",
            "source_id": "123",
            "source_url": "http://example.com",
            "complexity_score": 5,
            "created_at": "2023-01-01",
            "updated_at": "2023-01-02"
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta)
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 0
    
    def test_unexpected_additional_property_warning(self, validator):
        """Test that unexpected additional properties generate warnings."""
        meta = {
            "name": "Test",
            "version": "1.0",
            "unexpected_field": "some value"
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 1
        assert "Unexpected additional property 'meta.unexpected_field'" in warnings[0]
    
    def test_multiple_unexpected_properties_multiple_warnings(self, validator):
        """Test multiple unexpected properties generate multiple warnings."""
        meta = {
            "name": "Test",
            "version": "1.0",
            "field1": "value1",
            "field2": "value2"
        }
        is_valid, errors, warnings = validator.validate_meta_property(meta, "test.json")
        
        assert is_valid is True
        assert errors == []
        assert len(warnings) == 2


class TestValidateSampleFiles:
    
    def test_validate_sample_files_success(self, validator, temp_sample_dir):
        """Test successful validation of sample files."""
        # Create a valid spec file
        strategy_dir = temp_sample_dir / "test_strategy"
        spec_file = strategy_dir / "spec_test.json"
        
        valid_spec = {
            "meta": {
                "name": "Test Strategy",
                "version": "1.0.0",
                "description": "Test description"
            }
        }
        
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
        
        # Write invalid JSON
        spec_file.write_text('{"invalid": json}')
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 1
        file_path = str(spec_file)
        is_valid, errors, warnings = results[file_path]
        assert is_valid is False
        assert any("JSON decode error" in error for error in errors)
    
    def test_validate_sample_files_no_meta(self, validator, temp_sample_dir):
        """Test handling of files without meta property."""
        strategy_dir = temp_sample_dir / "test_strategy"
        spec_file = strategy_dir / "spec_test.json"
        
        spec_file.write_text('{"other_property": "value"}')
        
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        assert len(results) == 1
        file_path = str(spec_file)
        is_valid, errors, warnings = results[file_path]
        assert is_valid is False
        assert any("No 'meta' property found" in error for error in errors)
    
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
        # Create multiple strategy directories with spec files
        for i in range(3):
            strategy_dir = temp_sample_dir / f"strategy_{i}"
            strategy_dir.mkdir()
            spec_file = strategy_dir / f"spec_strategy_{i}.json"
            
            spec_data = {
                "meta": {
                    "name": f"Strategy {i}",
                    "version": f"1.{i}.0"
                }
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
        assert "VALID: file1.json" in report
        assert "VALID: file2.json" in report
    
    def test_generate_validation_report_with_errors(self, validator):
        """Test report generation with errors."""
        results = {
            "valid.json": (True, [], []),
            "invalid.json": (False, ["Error 1", "Error 2"], ["Warning 1"])
        }
        
        report = validator.generate_validation_report(results)
        
        assert "Total files validated: 2" in report
        assert "Valid files: 1" in report
        assert "Invalid files: 1" in report
        assert "VALID: valid.json" in report
        assert "INVALID: invalid.json" in report
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
    
    def test_valid_categories_constant(self, validator):
        """Test that VALID_CATEGORIES contains expected values."""
        expected_categories = {
            "momentum", "mean_reversion", "trend_following", "arbitrage",
            "market_neutral", "long_short", "buy_hold", "tactical", "other"
        }
        assert validator.VALID_CATEGORIES == expected_categories
    
    def test_version_pattern_constant(self, validator):
        """Test VERSION_PATTERN regex."""
        valid_versions = ["1.0", "2.1", "10.25", "1.0.0", "2.1.3"]
        invalid_versions = ["1", "1.", "v1.0", "1.0.0.0"]
        
        for version in valid_versions:
            assert validator.VERSION_PATTERN.match(version) is not None
        
        for version in invalid_versions:
            assert validator.VERSION_PATTERN.match(version) is None


class TestIntegration:
    
    def test_full_validation_workflow(self, validator, temp_sample_dir):
        """Test complete validation workflow with mixed valid/invalid files."""
        # Create various test cases
        test_cases = [
            # Valid file
            {
                "dir": "valid_strategy",
                "file": "spec_valid.json",
                "content": {
                    "meta": {
                        "name": "Valid Strategy",
                        "version": "1.0.0",
                        "description": "A valid strategy",
                        "category": "momentum"
                    }
                }
            },
            # Invalid file - missing name
            {
                "dir": "invalid_strategy1",
                "file": "spec_no_name.json", 
                "content": {
                    "meta": {
                        "version": "1.0.0"
                    }
                }
            },
            # Invalid file - bad version pattern
            {
                "dir": "invalid_strategy2",
                "file": "spec_bad_version.json",
                "content": {
                    "meta": {
                        "name": "Bad Version Strategy",
                        "version": "v1.0"
                    }
                }
            }
        ]
        
        for case in test_cases:
            strategy_dir = temp_sample_dir / case["dir"]
            strategy_dir.mkdir()
            spec_file = strategy_dir / case["file"]
            spec_file.write_text(json.dumps(case["content"], indent=2))
        
        # Run validation
        results = validator.validate_sample_files(str(temp_sample_dir))
        
        # Verify results
        assert len(results) == 3
        
        valid_count = sum(1 for is_valid, _, _ in results.values() if is_valid)
        invalid_count = sum(1 for is_valid, _, _ in results.values() if not is_valid)
        
        assert valid_count == 1
        assert invalid_count == 2
        
        # Generate and verify report
        report = validator.generate_validation_report(results)
        assert "Total files validated: 3" in report
        assert "Valid files: 1" in report
        assert "Invalid files: 2" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])