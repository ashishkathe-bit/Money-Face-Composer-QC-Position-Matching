"""
Indicator Code Reader for Strategy Compiler

Reads and extracts custom indicator class definitions for embedding
into generated algorithm files. Only includes indicators that are
actually used in the strategy specification.
"""

import os
import re
from typing import Dict, Set, List


class IndicatorCodeReader:
    """
    Utility class to read and extract custom indicator class definitions
    from individual indicator files for embedding into algorithm files.
    """
    
    # Mapping of indicator names to their corresponding file names
    INDICATOR_FILE_MAPPING = {
        "max-drawdown": "max_drawdown_indicator.py",
        "drawdown": "drawdown_indicator.py", 
        "moving-average-return": "moving_avg_return_indicator.py"
    }
    
    # Mapping of indicator names to their class names
    INDICATOR_CLASS_MAPPING = {
        "max-drawdown": "MaxDrawdownIndicator",
        "drawdown": "DrawdownIndicator",
        "moving-average-return": "MovingAvgReturnIndicator"
    }
    
    def __init__(self, indicators_dir: str = None):
        """
        Initialize the IndicatorCodeReader.
        
        Args:
            indicators_dir: Path to the indicators directory
        """
        if indicators_dir is None:
            # Default to indicators directory relative to this file
            current_dir = os.path.dirname(__file__)
            self.indicators_dir = current_dir
        else:
            self.indicators_dir = indicators_dir
    
    def get_embedded_classes_code(self, used_indicators: Set[str]) -> str:
        """
        Generate embedded class code for only the indicators that are used.
        
        Args:
            used_indicators: Set of indicator names that are actually used
            
        Returns:
            String containing the embedded class definitions
        """
        if not used_indicators:
            return ""
        
        embedded_code = []
        embedded_code.append("# Custom Indicator Classes")
        embedded_code.append("")
        
        # Add IndicatorDataPoint class first (shared by all custom indicators)
        indicator_data_point_code = self._get_indicator_data_point_class()
        embedded_code.append(indicator_data_point_code)
        embedded_code.append("")
        
        # Add each used custom indicator class
        for indicator_name in used_indicators:
            if indicator_name in self.INDICATOR_FILE_MAPPING:
                class_code = self._extract_indicator_class(indicator_name)
                if class_code:
                    embedded_code.append(class_code)
                    embedded_code.append("")
        
        return "\n".join(embedded_code)
    
    def _extract_indicator_class(self, indicator_name: str) -> str:
        """
        Extract the main indicator class from its file.
        
        Args:
            indicator_name: Name of the indicator (e.g., "max-drawdown")
            
        Returns:
            String containing the class definition
        """
        filename = self.INDICATOR_FILE_MAPPING.get(indicator_name)
        if not filename:
            return ""
        
        file_path = os.path.join(self.indicators_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return ""
        
        # Extract the main indicator class (not IndicatorDataPoint)
        class_name = self.INDICATOR_CLASS_MAPPING.get(indicator_name)
        if not class_name:
            return ""
        
        # Pattern to match the main indicator class
        pattern = rf'^class {class_name}:.*?(?=^class|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            class_code = match.group(0).rstrip()
            # Remove any trailing IndicatorDataPoint class that might be included
            class_code = re.sub(r'\n\nclass IndicatorDataPoint:.*', '', class_code, flags=re.DOTALL)
            return class_code
        
        return ""
    
    def _get_indicator_data_point_class(self) -> str:
        """
        Get the IndicatorDataPoint class definition.
        Since multiple indicator files contain this class, we extract it once.
        
        Returns:
            String containing IndicatorDataPoint class definition
        """
        # Read from any indicator file that contains IndicatorDataPoint
        sample_file = os.path.join(self.indicators_dir, "max_drawdown_indicator.py")
        
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            # Fallback implementation
            return '''class IndicatorDataPoint:
    """Simple data point class for indicator values."""
    
    def __init__(self, value: float):
        self.value = value'''
        
        # Extract IndicatorDataPoint class
        pattern = r'^class IndicatorDataPoint:.*?(?=^class|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            return match.group(0).rstrip()
        
        # Fallback if not found
        return '''class IndicatorDataPoint:
    """Simple data point class for indicator values."""
    
    def __init__(self, value: float):
        self.value = value'''
    
    def validate_indicators_exist(self, used_indicators: Set[str]) -> List[str]:
        """
        Validate that all used indicators have corresponding files.
        
        Args:
            used_indicators: Set of indicator names to validate
            
        Returns:
            List of missing indicator files
        """
        missing_indicators = []
        
        for indicator_name in used_indicators:
            filename = self.INDICATOR_FILE_MAPPING.get(indicator_name)
            if not filename:
                missing_indicators.append(f"Unknown indicator: {indicator_name}")
                continue
                
            file_path = os.path.join(self.indicators_dir, filename)
            if not os.path.exists(file_path):
                missing_indicators.append(f"File not found: {filename}")
        
        return missing_indicators