from strategy_compiler import StrategyCompiler
from validators.settings_validator import SettingsValidator
from generators.settings_generator import SettingsGenerator
from validators.meta_validator import MetaValidator
from generators.meta_generator import MetaGenerator
from generators.universe_generator import UniverseGenerator
from validators.universe_validator import UniverseValidator
from generators.node_generator import NodeGenerator
from validators.logic_validator import LogicValidator
from generators.indicator_generator import IndicatorGenerator

# Driver class implements the logic of the strategy compiler sequence
class Driver:
    
    # Constructor
    def __init__(self):
        '''
        This method is constructor for the driver class
        '''
        
        # Setting the new objects to None
        self.strategy_compiler = None
        self.meta_validator = None
        self.settings_validator = None
        self.settings_generator = None
        self.universe_validator = None
        self.universe_generator = None
        self.node_generator = None
        self.logic_validator = None
        self.indicator_generator = None

        # Initializing new objects
        self.initialize_new_objects()

        # Setting the class instances for the strategy compiler
        self.set_class_instances_for_strategy_compiler()
  
    # initialize_new_objects method initializes the new objects to be used by the driver class
    def initialize_new_objects(self):
        '''
        This method initializes the new objects to be used by the driver class
        '''
        
        # Creating an instance of the strategy compiler class
        self.strategy_compiler = StrategyCompiler()
        
        # Creating an instance of the settings validator class
        self.settings_validator = SettingsValidator()
        
        # Creating an instance of the settings generator class
        self.settings_generator = SettingsGenerator()
        
        # Creating an instance of the meta validator class
        self.meta_validator = MetaValidator()
        
        # Creating an instance of the meta generator class
        self.meta_generator = MetaGenerator()
        
        # Creating an instance of the universe validator class
        self.universe_validator = UniverseValidator()
        
        # Creating an instance of the universe generator class
        self.universe_generator = UniverseGenerator()
        
        # Creating an instance of the indicator generator class
        self.indicator_generator = IndicatorGenerator()
        
        # Creating an instance of the node generator class
        self.node_generator = NodeGenerator(self.indicator_generator)
        
        # Creating an instance of the logic validator class
        self.logic_validator = LogicValidator()
        
    def set_class_instances_for_strategy_compiler(self):
        '''
        This method sets the class instances for the strategy compiler
        '''
        
        # Setting the settings validator for the strategy compiler
        self.strategy_compiler.set_settings_validator(self.settings_validator)
        
        # Setting the settings generator for the strategy compiler
        self.strategy_compiler.set_settings_generator(self.settings_generator)

        # Creating an instance of the meta validator class
        self.strategy_compiler.set_meta_validator(self.meta_validator)
        
        # Creating an instance of the meta generator class
        self.strategy_compiler.set_meta_generator(self.meta_generator)
        
        # Creating an instance of the universe validator class
        self.strategy_compiler.set_universe_validator(self.universe_validator)
        
        # Creating an instance of the universe generator class
        self.strategy_compiler.set_universe_generator(self.universe_generator)
        
        #Creating an instance of the indicator generator class
        self.strategy_compiler.set_indicator_generator(self.indicator_generator)
        
        # Creating an instance of the node generator class
        self.strategy_compiler.set_node_generator(self.node_generator)
        
        # Creating an instance of the logic validator class
        self.strategy_compiler.set_logic_validator(self.logic_validator)
        
    # run method executes the strategy compiler sequence of tasks
    def run(self):
        '''
        This method starts the strategy compiler sequence of tasks
        '''
        
        # Starting the compilation of the strategy
        self.strategy_compiler.start_compiler()
    
# Main method to run the driver class
if __name__ == "__main__":
    
    # Create an instance of the driver class
    driver = Driver()
    
    # Run the driver class
    driver.run()