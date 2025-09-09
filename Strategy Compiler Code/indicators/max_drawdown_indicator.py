"""
Maximum Drawdown Indicator for QuantConnect Lean Engine

Calculates the maximum drawdown over a specified period.
"""

from AlgorithmImports import *
from collections import defaultdict


class MaxDrawdownIndicator:
    """
    Custom indicator for calculating maximum drawdown over a given period.
    
    This indicator tracks the largest peak-to-trough decline in value over
    the specified lookback period.
    """
    
    def __init__(self, period: int = 252):
        """
        Initialize the Maximum Drawdown indicator.
        
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
        Calculate and return the current maximum drawdown value.
        
        Returns:
            Maximum drawdown as a decimal (0.0 to 1.0)
        """
        if not self.is_ready or len(self.price_history) < 2:
            return 0.0
            
        peak = self.price_history[0]
        max_drawdown = 0.0
        
        for price in self.price_history[1:]:
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak if peak > 0 else 0.0
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown


class IndicatorDataPoint:
    """Simple data point class for indicator values."""
    
    def __init__(self, value: float):
        self.value = value