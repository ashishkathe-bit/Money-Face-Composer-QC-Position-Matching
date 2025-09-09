"""
Moving Average Return Indicator for QuantConnect Lean Engine

Calculates the moving average of returns over a specified period.
"""

from AlgorithmImports import *
from collections import defaultdict


class MovingAvgReturnIndicator:
    """
    Custom indicator for calculating moving average of returns.
    
    This indicator tracks price changes and calculates the rolling 
    average of percentage returns over the specified period.
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize the Moving Average Return indicator.
        
        Args:
            period: Number of return observations to average (default: 20)
        """
        self.period = period
        self.price_history = []
        self.return_history = []
        self.is_ready = False
        
    def update(self, price: float) -> None:
        """
        Update the indicator with a new price value.
        
        Args:
            price: Current price value
        """
        self.price_history.append(price)
        
        # Calculate return if we have previous price
        if len(self.price_history) >= 2:
            prev_price = self.price_history[-2]
            if prev_price > 0:
                return_value = (price - prev_price) / prev_price
                self.return_history.append(return_value)
                
                # Maintain rolling window of returns
                if len(self.return_history) > self.period:
                    self.return_history.pop(0)
        
        # Maintain price history (limit for memory)
        if len(self.price_history) > 500:
            self.price_history.pop(0)
            
        # Ready when we have enough returns
        if len(self.return_history) >= min(self.period, 1):
            self.is_ready = True
    
    @property
    def current(self):
        """Get current indicator value object."""
        return IndicatorDataPoint(self.value)
    
    @property
    def value(self) -> float:
        """
        Calculate and return the moving average of returns.
        
        Returns:
            Moving average of returns as a decimal
        """
        if not self.is_ready or len(self.return_history) == 0:
            return 0.0
            
        return sum(self.return_history) / len(self.return_history)


class IndicatorDataPoint:
    """Simple data point class for indicator values."""
    
    def __init__(self, value: float):
        self.value = value