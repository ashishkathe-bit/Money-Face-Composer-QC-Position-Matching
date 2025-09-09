import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from .indicator_generator import IndicatorGenerator


class NodeGenerator:
    """
    Generates Python code from logic node trees.
    
    Converts complex node structures (condition, filter, order, exit, expression, weight, group)
    into executable Python code for QuantConnect Lean algorithms.
    """
    
    # Operator mapping to Python operators
    OPERATOR_MAPPING = {
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=", 
        "eq": "==",
        "neq": "!=",
        "crosses_above": "_crosses_above",
        "crosses_below": "_crosses_below"
    }
    
    # Size type mapping to implementation approaches
    SIZE_TYPE_MAPPING = {
        "percent_equity": "portfolio_percent",
        "fixed_qty": "fixed_quantity",
        "fixed_value": "fixed_dollar",
        "risk_based": "risk_adjusted"
    }
    
    def __init__(self, indicator_generator=None):
        """Initialize the NodeGenerator with default settings."""
        self.indicator_generator = IndicatorGenerator()
        self.symbols_referenced = set()
        self.helper_methods_needed = set()
        self.variables_created = set()
        self.condition_counter = 0
        self.filter_counter = 0
        self.order_counter = 0
        
    def generate_logic_code(self, logic: Any, universe: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to generate Python code from logic tree.
        
        Args:
            logic: Logic tree (single node or array of nodes)
            universe: Universe array for symbol validation
            
        Returns:
            Dictionary containing generated code components
        """
        self._reset_counters()
        self.indicator_generator.reset_variables()
        
        # Extract universe symbols
        universe_symbols = set()
        if universe:
            universe_symbols = {
                asset.get('symbol', '').upper()
                for asset in universe
                if isinstance(asset, dict) and asset.get('symbol')
            }
        
        # Generate the main logic code
        main_logic_code = self._generate_node_code(logic, depth=0, universe_symbols=universe_symbols)
        
        on_data_header = "    def OnData(self, data: Slice) -> None:\n        '''Main algorithm logic executed on each data point'''\n"
        
        main_logic_code = on_data_header + main_logic_code
        
        indicator_init_code = self._generate_indicator_initialization()
        
        # Get embedded indicator classes if available
        embedded_classes = self.indicator_generator.get_embedded_indicator_classes()
        
        return {
            "main_logic_code": main_logic_code,
            "indicator_initialization_code": indicator_init_code,
            "indicators_used": list(self.indicator_generator.indicators_used),
            "symbols_referenced": list(self.symbols_referenced),
            "variables_created": list(self.variables_created),
            'security_check_function': self._create_security_check_function(),
            "embedded_indicator_classes": embedded_classes
        }
    
    def _reset_counters(self) -> None:
        """Reset all internal counters and tracking variables."""
        self.symbols_referenced.clear()
        self.helper_methods_needed.clear()
        self.variables_created.clear()
        self.condition_counter = 0
        self.filter_counter = 0
        self.order_counter = 0
    
    def _generate_node_code(self, node: Any, depth: int = 0, universe_symbols: Set[str] = None) -> str:
        """Generate code for a single node or array of nodes."""
        if universe_symbols is None:
            universe_symbols = set()
            
        indent = "    " * (depth + 2)  # Base indent for algorithm methods
        
        if isinstance(node, list):
            # Handle array of nodes
            code_blocks = []
            for i, child_node in enumerate(node):
                child_code = self._generate_node_code(child_node, depth, universe_symbols)
                if child_code.strip():
                    code_blocks.append(child_code)
            return "\n\n".join(code_blocks)
        
        elif isinstance(node, dict):
            node_type = str(node.get('type', '')).lower()
            
            if node_type == "condition":
                return self._generate_condition_code(node, depth, universe_symbols)
            elif node_type == "filter":
                return self._generate_filter_code(node, depth, universe_symbols)
            elif node_type == "order":
                return self._generate_order_code(node, depth, universe_symbols)
            elif node_type == "exit":
                return self._generate_exit_code(node, depth, universe_symbols)
            elif node_type == "expression":
                return self._generate_expression_code(node, depth, universe_symbols)
            elif node_type == "weight":
                return self._generate_weight_code(node, depth, universe_symbols)
            elif node_type == "group":
                return self._generate_group_code(node, depth, universe_symbols)
            else:
                return f"{indent}# Unknown node type: {node_type}"
        
        return f"{indent}# Invalid node structure"
    
    def _generate_condition_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for condition nodes."""
        indent = "    " * (depth + 2)
        self.condition_counter += 1
        condition_id = f"condition_{self.condition_counter}"
        
        # Check if this is a comparison condition or container condition
        has_comparison_fields = any(field in node for field in ['lhs', 'operator', 'rhs'])
        has_children = 'children' in node and node['children']
        
        code_lines = []
        
        if has_comparison_fields:
            # This is a comparison condition - generate actual comparison
            lhs_code = self._generate_operand_code(node.get('lhs'), universe_symbols)
            operator = str(node.get('operator', 'gt')).lower()
            rhs_code = self._generate_operand_code(node.get('rhs'), universe_symbols)
            
            # Map operator to Python code
            if operator in self.OPERATOR_MAPPING:
                op_code = self.OPERATOR_MAPPING[operator]
                if operator in ["crosses_above", "crosses_below"]:
                    # Special handling for crossover indicators
                    self.helper_methods_needed.add(operator)
                    condition_expr = f"self.{op_code}({lhs_code}, {rhs_code})"
                else:
                    condition_expr = f"{lhs_code} {op_code} {rhs_code}"
            else:
                condition_expr = f"{lhs_code} > {rhs_code}  # Unknown operator: {operator}"
            
            code_lines.append(f"{indent}# {node.get('description', 'Condition comparison')}")
            
            # Use condition directly - IndicatorGenerator handles readiness checks internally
            code_lines.append(f"{indent}if {condition_expr}:")
            
            # Generate children code (true branch)
            if has_children:
                children_code = self._generate_node_code(node['children'], depth + 1, universe_symbols)
                code_lines.append(children_code)
            else:
                code_lines.append(f"{indent}    # No action defined for true condition")
                
        elif has_children:
            # This is a container condition - process children based on structure
            description = node.get('description', 'Conditional logic container')
            
            # Don't add generic "Conditional logic container" comments
            if 'conditional logic' not in description.lower() or 'container' not in description.lower():
                code_lines.append(f"{indent}# {description}")
            
            children = node['children'] if isinstance(node['children'], list) else [node['children']]
            
            if len(children) == 1:
                # Single child - just execute it directly without any if wrapper
                children_code = self._generate_node_code(children[0], depth, universe_symbols)
                code_lines.append(children_code)
            else:
                # Multiple children - detect if this is actually an if-else structure
                # Look for patterns indicating if-else vs sequential execution
                has_else_branches = any(child.get('description', '').lower() == 'else branch' for child in children[1:])
                
                if has_else_branches:
                    # This is an if-else structure - first child contains the condition, others are else branches
                    for i, child in enumerate(children):
                        if i == 0:
                            # First child should contain the actual condition logic
                            child_code = self._generate_node_code(child, depth, universe_symbols)
                            code_lines.append(child_code)
                        else:
                            # Subsequent children are else branches - add else without comment clutter
                            code_lines.append(f"{indent}else:")
                            child_code = self._generate_node_code(child, depth + 1, universe_symbols)
                            code_lines.append(child_code)
                else:
                    # Sequential execution - no if-else structure needed
                    for child in children:
                        child_code = self._generate_node_code(child, depth, universe_symbols)
                        if child_code.strip():
                            code_lines.append(child_code)
        else:
            # Invalid condition node
            code_lines.append(f"{indent}# Invalid condition node - no comparison fields or children")
        
        return "\n".join(code_lines)
    
    def check_if_all_lines_are_comment(self, code_lines: List[str]) -> bool:
        
        for line in code_lines:
            
            line = line.strip()
            
            if line == '' or line.startswith('#'):
                
                continue
            
            return False
        
        return True
    
    def _generate_filter_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for filter nodes."""
        indent = "    " * (depth + 2)
        self.filter_counter += 1
        filter_id = f"filter_{self.filter_counter}"
        
        # Extract filter parameters
        universe = node.get('universe', [])
        select_type = str(node.get('select', 'top')).lower()
        selection = node.get('selection', {})
        n_select = selection.get('n', 1)
        metric = node.get('metric', {})
        
        # Track symbols
        for symbol in universe:
            if isinstance(symbol, str):
                self.symbols_referenced.add(symbol.upper())
        
        for symbol in universe:

            metric['symbol'] = symbol
            
            # Generate metric calculation code
            metric_code = self._generate_operand_code(metric, universe_symbols)
        
        code_lines = []
        code_lines.append(f"{indent}# {node.get('description', 'Filter logic')}")
        
        # Calculate metrics for each symbol individually (performance optimized)
        code_lines.append(f"{indent}symbol_scores = {{}}")
        
        # Generate individual symbol assignments for better performance
        for symbol in universe:
            # Create metric config for this specific symbol
            symbol_metric = metric.copy()
            symbol_metric['symbol'] = symbol
            
            # Use IndicatorGenerator for optimized value access
            metric_calculation = self.indicator_generator.get_indicator_value_code(symbol_metric)
            
            code_lines.append(f"{indent}if '{symbol}' in self.Securities:")
            code_lines.append(f"{indent}    symbol_scores['{symbol}'] = {metric_calculation}")
        
        # Sort and select
        if select_type == "top":
            code_lines.append(f"{indent}selected_symbols = sorted(symbol_scores.items(), key=lambda x: x[1], reverse=True)[:{n_select}]")
        elif select_type == "bottom":
            code_lines.append(f"{indent}selected_symbols = sorted(symbol_scores.items(), key=lambda x: x[1])[:{n_select}]")
        else:  # middle
            code_lines.append(f"{indent}sorted_symbols = sorted(symbol_scores.items(), key=lambda x: x[1])")
            code_lines.append(f"{indent}mid_start = max(0, len(sorted_symbols) // 2 - {n_select // 2})")
            code_lines.append(f"{indent}selected_symbols = sorted_symbols[mid_start:mid_start + {n_select}]")
        
        # Handle allocation
        allocation_type = str(node.get('allocation', 'equal')).lower()
        size = node.get('size', 100.0)
        
        if allocation_type == "equal":
            code_lines.append(f"{indent}if selected_symbols:")
            code_lines.append(f"{indent}    weight_per_symbol = {size / 100.0} / len(selected_symbols)")
            code_lines.append(f"{indent}    for symbol, score in selected_symbols:")
            code_lines.append(f"{indent}        if self._is_security_ready_for_trading(symbol):")
            code_lines.append(f"{indent}            self.SetHoldings(symbol, weight_per_symbol)")
        
        elif allocation_type == "weighted":
            weights = node.get('weights', {})
            code_lines.append(f"{indent}for symbol, score in selected_symbols:")
            code_lines.append(f"{indent}    if self._is_security_ready_for_trading(symbol):")
            
            # Generate weight lookup
            weight_conditions = []
            for symbol, weight in weights.items():
                weight_conditions.append(f"'{symbol}': {weight * size / 100.0}")
            
            if weight_conditions:
                weights_dict = "{" + ", ".join(weight_conditions) + "}"
                code_lines.append(f"{indent}        weights = {weights_dict}")
                code_lines.append(f"{indent}        weight = weights.get(symbol, 0)")
                code_lines.append(f"{indent}        if weight > 0:")
                code_lines.append(f"{indent}            self.SetHoldings(symbol, weight)")
        
        return "\n".join(code_lines)
    
    def _generate_order_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for order nodes."""
        indent = "    " * (depth + 2)
        self.order_counter += 1
        order_id = f"order_{self.order_counter}"
        
        # Extract order parameters
        side = str(node.get('side', 'long')).lower()
        size_type = str(node.get('size_type', 'percent_equity')).lower()
        size = node.get('size', 100.0)
        allocation = str(node.get('allocation', 'equal')).lower()
        weights = node.get('weights', {})
        symbol_filter = node.get('symbol_filter')
        
        code_lines = []
        code_lines.append(f"{indent}# {node.get('description', 'Order execution')}")
        
        # Determine target symbols
        if symbol_filter:
            target_symbols = [symbol_filter]
            self.symbols_referenced.add(symbol_filter.upper())
        elif weights:
            target_symbols = list(weights.keys())
            for symbol in target_symbols:
                self.symbols_referenced.add(symbol.upper())
        else:
            # Default to universe symbols
            target_symbols = list(universe_symbols)
        
        # Generate position sizing logic
        if size_type == "percent_equity":
            total_weight = size / 100.0
            
            if allocation == "equal" and len(target_symbols) > 0:
                weight_per_symbol = total_weight / len(target_symbols)
                code_lines.append(f"{indent}target_weight = {weight_per_symbol}")
                
                for symbol in target_symbols:
                    code_lines.append(f"{indent}if self._is_security_ready_for_trading('{symbol}'):")
                    if side == "long":
                        code_lines.append(f"{indent}    self.SetHoldings('{symbol}', target_weight)")
                    else:  # short
                        code_lines.append(f"{indent}    self.SetHoldings('{symbol}', -target_weight)")
            
            elif allocation == "weighted":
                total_weights = sum(weights.values()) if weights else 1.0
                normalization_factor = total_weight / total_weights
                
                for symbol, weight in weights.items():
                    normalized_weight = weight * normalization_factor
                    code_lines.append(f"{indent}if self._is_security_ready_for_trading('{symbol}'):")
                    if side == "long":
                        code_lines.append(f"{indent}    self.SetHoldings('{symbol}', {normalized_weight})")
                    else:  # short
                        code_lines.append(f"{indent}    self.SetHoldings('{symbol}', -{normalized_weight})")
        
        elif size_type == "fixed_qty":
            code_lines.append(f"{indent}target_quantity = {int(size)}")
            for symbol in target_symbols:
                code_lines.append(f"{indent}if self._is_security_ready_for_trading('{symbol}'):")
                if side == "long":
                    code_lines.append(f"{indent}    self.MarketOrder('{symbol}', target_quantity)")
                else:  # short
                    code_lines.append(f"{indent}    self.MarketOrder('{symbol}', -target_quantity)")
        
        elif size_type == "fixed_value":
            code_lines.append(f"{indent}target_value = {size}")
            for symbol in target_symbols:
                code_lines.append(f"{indent}if self._is_security_ready_for_trading('{symbol}'):")
                code_lines.append(f"{indent}    current_price = self.Securities['{symbol}'].Price")
                code_lines.append(f"{indent}    if current_price > 0:")
                quantity_calc = "int(target_value / current_price)"
                if side == "short":
                    quantity_calc = f"-{quantity_calc}"
                code_lines.append(f"{indent}        self.MarketOrder('{symbol}', {quantity_calc})")
        
        return "\n".join(code_lines)
    
    def _generate_exit_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for exit nodes."""
        indent = "    " * (depth + 2)
        
        exit_type = str(node.get('exit_type', 'signal_based')).lower()
        qty_percent = node.get('qty_percent', 100.0)
        
        code_lines = []
        code_lines.append(f"{indent}# {node.get('description', 'Exit logic')}")
        
        if exit_type == "signal_based":
            # Exit all positions based on signal
            if qty_percent >= 100.0:
                code_lines.append(f"{indent}self.Liquidate()")
            else:
                # Partial liquidation
                liquidation_factor = qty_percent / 100.0
                code_lines.append(f"{indent}for symbol in list(self.Portfolio.Keys):")
                code_lines.append(f"{indent}    holding = self.Portfolio[symbol]")
                code_lines.append(f"{indent}    if holding.Invested:")
                code_lines.append(f"{indent}        target_qty = int(holding.Quantity * {liquidation_factor})")
                code_lines.append(f"{indent}        if target_qty != 0:")
                code_lines.append(f"{indent}            self.MarketOrder(symbol, -target_qty)")
        
        elif exit_type == "stop_loss":
            # Basic stop loss implementation
            stop_loss_percent = node.get('threshold', 0.05)  # Default 5% stop loss
            code_lines.append(f"{indent}for symbol in list(self.Portfolio.Keys):")
            code_lines.append(f"{indent}    holding = self.Portfolio[symbol]")
            code_lines.append(f"{indent}    if holding.Invested:")
            code_lines.append(f"{indent}        unrealized_pnl_pct = holding.UnrealizedProfitPercent")
            code_lines.append(f"{indent}        if unrealized_pnl_pct < -{stop_loss_percent}:")
            code_lines.append(f"{indent}            self.Liquidate(symbol)")
        
        elif exit_type == "take_profit":
            # Basic take profit implementation
            take_profit_percent = node.get('threshold', 0.10)  # Default 10% take profit
            code_lines.append(f"{indent}for symbol in list(self.Portfolio.Keys):")
            code_lines.append(f"{indent}    holding = self.Portfolio[symbol]")
            code_lines.append(f"{indent}    if holding.Invested:")
            code_lines.append(f"{indent}        unrealized_pnl_pct = holding.UnrealizedProfitPercent")
            code_lines.append(f"{indent}        if unrealized_pnl_pct > {take_profit_percent}:")
            code_lines.append(f"{indent}            self.Liquidate(symbol)")
        
        return "\n".join(code_lines)
    
    def _generate_expression_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for expression nodes."""
        indent = "    " * (depth + 2)
        
        expression = node.get('expression', '')
        if not expression:
            return f"{indent}# Empty expression"
        
        code_lines = []
        code_lines.append(f"{indent}# {node.get('description', 'Expression evaluation')}")
        
        # Basic expression parsing and conversion
        # This could be enhanced with a full expression parser
        processed_expr = self._process_expression(expression, universe_symbols)
        
        code_lines.append(f"{indent}if {processed_expr}:")
        code_lines.append(f"{indent}    # Expression condition is true")
        code_lines.append(f"{indent}    pass  # Add specific actions here")
        
        return "\n".join(code_lines)
    
    def _generate_weight_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for weight nodes."""
        indent = "    " * (depth + 2)
        
        weights = node.get('weights', {})
        
        code_lines = []
        code_lines.append(f"{indent}# {node.get('description', 'Portfolio weighting')}")
        
        for symbol, weight in weights.items():
            self.symbols_referenced.add(symbol.upper())
            code_lines.append(f"{indent}if '{symbol}' in self.Securities:")
            code_lines.append(f"{indent}    self.SetHoldings('{symbol}', {weight})")
        
        # Process all children sequentially
        if 'children' in node and node['children']:
            children_code = self._generate_node_code(node['children'], depth, universe_symbols)
            code_lines.append(children_code)
        
        return "\n".join(code_lines)
    
    def _generate_group_code(self, node: Dict[str, Any], depth: int, universe_symbols: Set[str]) -> str:
        """Generate code for group nodes."""
        indent = "    " * (depth + 2)
        
        code_lines = []
        
        # Only add description as comment if it's meaningful (not generic or "Else branch")
        description = node.get('description', '')
        meaningful_descriptions = [
            'else branch', 'group logic', 'group: wt-cash-equal', 
            'conditional logic', 'group:', 'alternative branch'
        ]
        
        # Add comment only if description provides real value
        if (description and 
            description.lower().strip() not in meaningful_descriptions and
            not description.lower().startswith('group:') and
            not description.lower().startswith('conditional logic')):
            code_lines.append(f"{indent}# {description}")
        
        # Process all children sequentially
        if 'children' in node and node['children']:
            children_code = self._generate_node_code(node['children'], depth, universe_symbols)
            code_lines.append(children_code)
        
        return "\n".join(code_lines)
    
    # Note: Readiness checks are now handled by IndicatorGenerator's get_indicator_value_code() method
    
    def _generate_operand_code(self, operand: Any, universe_symbols: Set[str]) -> str:
        """Generate code for condition operands (indicators or literals)."""
        # Handle numeric literals
        if isinstance(operand, (int, float)):
            return str(operand)
        
        # Handle string literals
        if isinstance(operand, str):
            return f'"{operand}"'
        
        # Handle boolean literals
        if isinstance(operand, bool):
            return str(operand)
        
        # Handle None
        if operand is None:
            return "0"
        
        # Must be a dictionary (indicator definition)
        if not isinstance(operand, dict):
            return f"0  # Unsupported operand type: {type(operand).__name__}"
        
        return self.indicator_generator.get_indicator_value_code(operand)
        
    def _process_expression(self, expression: str, universe_symbols: Set[str]) -> str:
        """Process mathematical expressions and convert to Python code."""
        # Basic expression processing - could be enhanced significantly
        processed = expression
        
        # Replace common indicator references (using modern direct access)
        processed = re.sub(r'\b(rsi|sma|ema)_(\w+)_(\d+)\b', r"self.\2_\1_\3", processed)
        
        # Replace logical operators
        processed = processed.replace(' AND ', ' and ')
        processed = processed.replace(' OR ', ' or ')
        processed = processed.replace(' NOT ', ' not ')
        
        return processed
    
    def _generate_indicator_initialization(self) -> str:
        """Generate indicator initialization code using IndicatorGenerator."""
        return self.indicator_generator.generate_initialization_code()
    
    def _create_security_check_function(self):
        return f"""
    def _is_security_ready_for_trading(self, symbol: str) -> bool:
        '''Check if security is ready for trading with accurate price data.'''
        # Check if symbol exists in securities
        if symbol not in self.Securities:
            return False
        
        # Check if current slice contains data for this symbol
        if not self.current_slice or not self.current_slice.contains_key(symbol):
            return False
            
        # Check if slice data is not None
        if not self.current_slice[symbol]:
            return False
            
        # Check if security has valid price
        security = self.Securities[symbol]
        if not hasattr(security, 'Price') or security.Price <= 0:
            return False
            
        return True
            """

