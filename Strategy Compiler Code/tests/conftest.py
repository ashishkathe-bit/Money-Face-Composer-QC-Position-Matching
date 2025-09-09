"""
Pytest configuration and fixtures for MetaGenerator tests.
"""

import pytest
from pathlib import Path
import sys

# Add generators to path
sys.path.append(str(Path(__file__).parent.parent / 'generators'))

from meta_generator import MetaGenerator


@pytest.fixture
def meta_generator():
    """Fixture providing a fresh MetaGenerator instance for each test."""
    return MetaGenerator()


@pytest.fixture
def sample_meta_full():
    """Fixture with complete meta data including all optional fields."""
    return {
        "name": "BB-XM NASDAQ-X ||| Deez ||| 29JUN2023",
        "description": "Believe in the power of tactical semiconductor trading strategies",
        "version": "1.0",
        "source": "composer",
        "source_id": "1hoPN3tFE0aDY3aiZtxT",
        "source_url": "https://app.composer.trade/symphony/1hoPN3tFE0aDY3aiZtxT/details",
        "category": "tactical",
        "complexity_score": 9,
        "created_at": "2025-06-25T03:37:14.947339Z",
        "updated_at": "2025-06-25T03:37:14.947363Z"
    }


@pytest.fixture
def sample_meta_minimal():
    """Fixture with minimal meta data (only required fields)."""
    return {
        "name": "Simple Strategy",
        "version": "1.0"
    }


@pytest.fixture
def sample_meta_with_description():
    """Fixture with meta data including description."""
    return {
        "name": "Momentum Strategy",
        "description": "A momentum-based trading strategy using technical indicators",
        "version": "2.1.5",
        "category": "momentum"
    }


@pytest.fixture(params=[
    "Simple Name",
    "Complex-Name_With|Special@Characters",
    "123NumbersFirst",
    "UPPERCASE_STRATEGY",
    "mixed_Case-Strategy123",
    "",
    "   Spaces   Around   ",
    "Very Long Strategy Name With Many Words And Special Characters !!!"
])
def class_name_test_cases(request):
    """Parametrized fixture for testing class name generation edge cases."""
    return request.param


