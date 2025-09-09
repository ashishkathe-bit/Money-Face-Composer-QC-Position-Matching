import json
import zipfile
import pandas as pd
from io import StringIO
import os
from datetime import datetime
import sys

class StrategyCompiler:
    
    # Constructor
    def __init__(self):
        '''
        Constructor
        '''
        
        # Setting the file path of json
        self.file_path = r'C:\Users\ashish\Documents\Money_Face_Projects\example_files\01_strategy_compiler\sample_inputs\all_files\spec_strat_01jyqr5qpyf5f9k09xw4aw9xjn_v1.json'
        
        self.folder_path = r'C:\Users\ashish\Documents\Money_Face_Projects\example_files\01_strategy_compiler\sample_inputs\all_files'
        
        # Setting the output file path
        self.output_file_path = r'output/algorithm.py'
        
        # Setting the data files folder path
        self.data_files_folder_path = r'C:\Users\ashish\Documents\Money_Face_Projects\Lean\Data\equity\usa\daily'
            
        # Setting the settings validator to None
        self.settings_validator = None
        
        # Initializing the meta validator to None
        self.meta_validator = None
        
        # Initializing the meta generator to None
        self.meta_generator = None
        
        # Setting an empty list
        self.empty_list = []
        
    def set_meta_generator(self, meta_generator):
        '''
        This method sets the meta generator
        
        Args:
            meta_generator (MetaGenerator): MetaGenerator instance
        '''
        
        # Setting the meta generator
        self.meta_generator = meta_generator
            
    def set_settings_validator(self, settings_validator):
        '''
        This method sets the settings validator
        
        Args:
            settings_validator (SettingsValidator): SettingsValidator instance
        '''
        
        # Setting the settings validator
        self.settings_validator = settings_validator
        
    def set_settings_generator(self, settings_generator):
        '''
        This method sets the settings generator
        
        Args:   
            settings_generator (SettingsGenerator): SettingsGenerator instance
        '''
        
        # Setting the settings generator
        self.settings_generator = settings_generator
        
    def set_universe_generator(self, universe_generator):
        '''
        This method sets the universe generator
        
        Args:   
            universe_generator (UniverseGenerator): UniverseGenerator instance
        '''
        
        # Setting the universe generator
        self.universe_generator = universe_generator
        
    def set_universe_validator(self, universe_validator):
        '''
        This method sets the universe validator
        
        Args:   
            universe_validator (UniverseValidator): UniverseValidator instance
        '''
        
        # Setting the universe validator
        self.universe_validator = universe_validator
    
    def set_indicator_generator(self, indicator_generator):
        '''
        This method sets the indicator generator
        
        Args:
            indicator_generator (IndicatorGenerator): IndicatorGenerator instance
        '''
        self.indicator_generator = indicator_generator
        
    def set_node_generator(self, node_generator):
        '''
        This method sets the node generator
        
        Args:   
            node_generator (NodeGenerator): NodeGenerator instance
        '''
        
        # Setting the node generator
        self.node_generator = node_generator
    
    def set_logic_validator(self, logic_validator):
        '''
        This method sets the logic validator
        
        Args:   
            logic_validator (LogicValidator): LogicValidator instance
        '''
        
        # Setting the logic validator
        self.logic_validator = logic_validator

    def load_json_file(self):
        '''
        This method loads the json file
        '''
        # Reading the json file
        with open(self.file_path, 'r') as file:
            
            # Loading the json file
            json_data = json.load(file)
            
            # Returning the json data
            return json_data
        
    @staticmethod
    def write_py_file(filename: str, meta_code_lines: dict, setting_code_dict: dict, universe_code_lines: str, allowed_symbols: list, logic_code_dict: dict) -> None:
        """
        Write a list of code lines to a .py file.

        Args:
            filename (str): Target file path (e.g., "output.py").
            code_lines (List[str]): List of code lines (without newlines).
        """
        
        # Check if the file is .py or not
        if not filename.endswith(".py"):
            
            # Append .py if not present
            filename += ".py"
            
        # header comment
        meta_header_comment = meta_code_lines["header_comment"]
        
        # Import statements
        meta_import_statements = "from AlgorithmImports import *\nfrom typing import Dict, List, Optional\nimport numpy as np\n"
        
        # Rebalance method code from settings
        rebalance_method_code = setting_code_dict['rebalance_method']
        
        # Strategy class and docstring
        meta_strategy_class_line = f"class {meta_code_lines['class_name']}(QCAlgorithm):\n    '''\n    {meta_code_lines['class_docstring']}\n    '''\n{rebalance_method_code}    def initialize(self):\n\n"
        
        # Settings initialization code
        setting_imports = "\n".join(setting_code_dict['required_imports']) + "\n\n"
        
        # setting code
        setting_code = setting_code_dict['settings_initialization_code']
        
        symbol_list = f"        self.symbols = {allowed_symbols}"
        
        # Fee model code from settings
        fee_model_code = setting_code_dict['fee_model']
        
        # Slippage model code from settings
        slippage_model_code = setting_code_dict['slippage_model']
                
        # Two blank lines string for readability
        two_blank_lines = "\n\n"
        
        # Get on data method code from logic field
        on_data_code = logic_code_dict['main_logic_code']
        
        # Get indicator initialization code from logic field
        indicator_initialization_code = logic_code_dict['indicator_initialization_code']
        
        security_check_function = logic_code_dict['security_check_function']
        
        embedded_indicator_classes = logic_code_dict['embedded_indicator_classes']
                        
        # Write to file
        with open(filename, "w", encoding="utf-8") as f:
            
            # Write header comment, imports and strategy class
            f.write(meta_header_comment + "\n")
            f.write(meta_import_statements + '\n')
            f.write(setting_imports)
            
            f.write(fee_model_code)
            f.write(slippage_model_code)
            f.write(embedded_indicator_classes)
            f.write(meta_strategy_class_line)
            f.write(setting_code)
            f.write(two_blank_lines)
            f.write(universe_code_lines)
            f.write(two_blank_lines)
            f.write(symbol_list)
            f.write(indicator_initialization_code)
            
            f.write(two_blank_lines)
            f.write(on_data_code)
            f.write(two_blank_lines)
            f.write(security_check_function)

    def set_meta_validator(self, meta_validator):
        '''
        This method sets the meta validator for the strategy compiler
        
        Args:
            meta_validator (MetaValidator): MetaValidator instance
        '''
        self.meta_validator = meta_validator
        
    def if_list_is_empty(self, list):
        '''
        This method checks if a list is empty
        
        Args:
            list (List): List to check
            
        Returns:
            True if list is empty, False otherwise
        '''
        
        return list == []
        
    def handle_validation_errors(self, is_valid, errors, warnings):
        '''
        This method handles the validation errors
        
        Args:
            is_valid (bool): True if validation is successful, False otherwise
            errors (List[str]): List of validation errors
            warnings (List[str]): List of validation warnings
            
        '''
        
        if not is_valid:
            
            if not self.if_list_is_empty(errors):
            
                print(f"\n\nValidation errors:\n")
                for error in errors:
                    print(f"  Error: {error}")
            
            if not self.if_list_is_empty(warnings):
            
                print(f"Validation warnings:\n")
                for warning in warnings:
                    print(f"  Warning: {warning}")
                    
    def check_if_dates_are_present(self, json_data: dict[str, any]) -> bool:
        '''
        Method to check if start and end dates are present in the strategy spec
        
        Args:
            json_data (Dict[str, Any]): strategy spec json data
            
        Returns:
            bool: True if start and end dates are present, False otherwise
        '''
        
        # Check if settings data is present
        settings_data = json_data.get('settings')
        
        # Check if settings data is not None
        if settings_data is None:
            return False
        
        # Check if start and end dates are present
        start_date = settings_data.get('start')
        end_date = settings_data.get('end')
        
        # Check if start and end dates are not None
        if start_date is None or end_date is None:
            return False
        
        return True
    
    def read_csv_from_zip(self, zip_path: str, csv_filename: str) -> pd.DataFrame:
        """Read CSV file from ZIP archive using pandas"""
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open(csv_filename) as csv_file:
                # Read as text and convert to StringIO for pandas
                csv_content = csv_file.read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                return df
        
    def add_start_and_end_dates(self, json_data: dict[str, any], allowed_symbols: list) -> dict[str, any]:
        '''
        Method to add start and end dates to the strategy spec if not present

        Args:
            json_data (Dict[str, Any]): strategy spec json data
            
        Returns:

            json_data (Dict[str, Any]): strategy spec json data with start and end dates
        '''
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dates_list = []
        
        if not self.check_if_dates_are_present(json_data):

            for symbol in allowed_symbols:
                
                zip_file_name = f"{symbol.lower()}.zip"
                
                csv_filename = f"{symbol.lower()}.csv"
                
                symbol_data_path = self.data_files_folder_path + "/" + zip_file_name
                
                if os.path.exists(symbol_data_path):
                    
                    pass
                    
                else:
                    
                    continue
                
                df = self.read_csv_from_zip(symbol_data_path, csv_filename)
                
                start_date = df.iloc[:,0].min()
                
                start_dates_list.append(start_date)
                
            if len(start_dates_list) == 0:
                
                print("Exiting because no start date found...")
                
                sys.exit()

            start_date = max(start_dates_list)
            
            start_date = start_date[0:4] + "-" + start_date[4:6] + "-" + start_date[6:8]

            json_data['settings']['start'] = start_date
            json_data['settings']['end'] = end_date
            
        return json_data

    def close_system_if_errors(self, is_valid: bool):
        """Close the system if there are errors
        
        Args:
            is_valid (bool): True if there are no errors, False otherwise
        """
        if not is_valid:
            print("Exiting...")
            sys.exit()

    # run method executes the strategy compiler sequence of tasks
    def start_compiler(self):
        '''
        This method executes the strategy compiler sequence of tasks
        '''
            
        # Loading the json file
        json_data = self.load_json_file()
        
        # Validate universe structure
        is_universe_valid, universe_errors, universe_warnings = self.universe_validator.validate_universe_property(json_data['universe'], self.file_path)
        
        # Handle validation errors
        self.handle_validation_errors(is_universe_valid, universe_errors, universe_warnings)
        
        # Close system if errors in universe field
        self.close_system_if_errors(is_universe_valid)
        
        # Get code from the universe generator
        universe_code_lines, allowed_symbols = self.universe_generator.generate_universe_setup(json_data['universe'])

        # Add start and end dates to the strategy spec if not present
        json_data = self.add_start_and_end_dates(json_data, allowed_symbols)
        
        # Validating the meta section of the json file
        is_meta_valid, meta_errors, meta_warnings = self.meta_validator.validate_meta_property(json_data["meta"], self.file_path)
        
        # Handling the validation errors
        self.handle_validation_errors(is_meta_valid, meta_errors, meta_warnings)
        
        # Close system if errors in meta field
        self.close_system_if_errors(is_meta_valid)
        
        # Get code from the meta generator
        meta_code_dict =self.meta_generator.process_meta(json_data["meta"])
        
        # Validate settings structure
        is_settings_valid, settings_errors= self.settings_validator.validate_settings(json_data['settings'])
        
        # Handle validation errors
        self.handle_validation_errors(is_settings_valid, settings_errors, self.empty_list)
        
        # Close system if errors in settings field
        self.close_system_if_errors(is_settings_valid)
        
        # Get code from the settings generator
        setting_code_dict = self.settings_generator.process_settings(json_data['settings'])
        
        # Validate logic field
        self.logic_validator.validate_logic(json_data['logic'], allowed_symbols)
        
        # Get logic field code from the logic generator
        logic_code_dict = self.node_generator.generate_logic_code(json_data['logic'], json_data.get('universe'))
        
        print("Generating Algorithm File...")

        # Merge code from all fields to create the algorithm file
        self.write_py_file(self.output_file_path, meta_code_dict, setting_code_dict, universe_code_lines,allowed_symbols, logic_code_dict)
        