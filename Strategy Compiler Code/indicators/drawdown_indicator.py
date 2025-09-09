"""
Current Drawdown Indicator for QuantConnect Lean Engine

Calculates the current drawdown from the highest peak over a specified period.
"""

from AlgorithmImports import *
from collections import defaultdict


class DrawdownIndicator:
    """
    Custom indicator for calculating current drawdown from peak.
    
    This indicator measures the current decline in value from the highest
    peak over the specified lookback period.
    """
    
    def __init__(self, period: int = 252):
        """
        Initialize the Current Drawdown indicator.
        
        Args:
            period: Lookback period in days (default: 252 for 1 year)
        """
        self.period = period
        self.price_history = []
        self.is_ready = False
        
    def update(self, price: float) -> None:
        """
        Update the indicator with a new price value.
        
        Args:
            price: Current price value
        """
        self.price_history.append(price)
        
        # Maintain rolling window of prices
        if len(self.price_history) > self.period:
            self.price_history.pop(0)
            
        # Ready when we have at least 2 data points
        if len(self.price_history) >= 2:
            self.is_ready = True
    
    @property
    def current(self):
        """Get current indicator value object."""
        return IndicatorDataPoint(self.value)
    
    @property
    def value(self) -> float:
        """
        Calculate and return the current drawdown from peak.
        
        Returns:
            Current drawdown as a decimal (0.0 to 1.0)
        """
        if not self.is_ready or len(self.price_history) < 2:
            return 0.0
            
        peak = max(self.price_history)
        current_price = self.price_history[-1]
        
        if peak > 0:
            return (peak - current_price) / peak
        return 0.0


class IndicatorDataPoint:
    """Simple data point class for indicator values."""
    
    def __init__(self, value: float):
        self.value = value