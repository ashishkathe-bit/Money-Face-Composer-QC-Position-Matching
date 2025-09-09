import pytest
from unittest.mock import patch
from validators.logic_validator import LogicValidator, DEFAULT_ALLOWED_METRICS, METRICS_REQUIRE_PERIOD


# Global fixtures
@pytest.fixture
def validator():
    """Create a fresh LogicValidator instance for each test."""
    return LogicValidator()

@pytest.fixture
def allowed_symbols():
    """Default allowed symbols for testing."""
    return ["TQQQ", "SQQQ", "BSV", "SPY"]

@pytest.fixture
def allowed_metrics():
    """Default allowed metrics for testing."""
    return list(DEFAULT_ALLOWED_METRICS)


class TestValidateOrderNode:
    
    def test_valid_order_node_minimal(self, validator, allowed_symbols):
        """Test validation with minimal valid order node."""
        node = {
            "type": "order",
            "side": "long",
            "weights": {"SPY": 1.0},
            "allocation": "weighted"
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert errors == []
    
    def test_valid_order_node_complete(self, validator, allowed_symbols):
        """Test validation with complete order node."""
        node = {
            "id": "order_1",
            "type": "order",
            "side": "long",
            "size_type": "percent_equity",
            "size": 50.0,
            "allocation": "weighted",
            "weights": {"SPY": 0.6, "TQQQ": 0.4},
            "universe": ["SPY", "TQQQ"]
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert errors == []
    
    def test_order_node_not_dict(self, validator, allowed_symbols):
        """Test validation fails when node is not a dictionary."""
        test_cases = [None, [], "string", 123]
        
        for node in test_cases:
            is_valid, errors = validator.validate_order_node(node, allowed_symbols)
            assert is_valid is False
            assert any("order node must be a dict" in error for error in errors)
    
    def test_order_wrong_type(self, validator, allowed_symbols):
        """Test validation fails when type is not 'order'."""
        node = {
            "type": "condition",
            "side": "long",
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("node.type must be 'order'" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_side", [None, "", "buy", "sell", 123, []])
    def test_order_invalid_side(self, validator, allowed_symbols, invalid_side):
        """Test validation fails for invalid side values."""
        node = {
            "type": "order",
            "side": invalid_side,
            "weights": {"SPY": 1.0}
        }
        print(f"invalid_side: {invalid_side}")
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.side must be 'long' or 'short'" in error for error in errors)
    
    @pytest.mark.parametrize("valid_side", ["long", "short"])
    def test_order_valid_sides(self, validator, allowed_symbols, valid_side):
        """Test validation passes for valid side values."""
        node = {
            "type": "order",
            "side": valid_side,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert not any("order.side" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_size_type", [
        "percentage", "shares", "dollars", 123, [], None
    ])
    def test_order_invalid_size_type(self, validator, allowed_symbols, invalid_size_type):
        """Test validation fails for invalid size_type values."""
        node = {
            "type": "order",
            "side": "long",
            "size_type": invalid_size_type,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.size_type must be one of:" in error for error in errors)
    
    @pytest.mark.parametrize("valid_size_type", [
        "percent_equity", "fixed_qty", "fixed_value", "risk_based"
    ])
    def test_order_valid_size_types(self, validator, allowed_symbols, valid_size_type):
        """Test validation passes for valid size_type values."""
        node = {
            "type": "order",
            "side": "long",
            "size_type": valid_size_type,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert not any("order.size_type" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_allocation", [
        "proportional", "balanced", 123, [], None
    ])
    def test_order_invalid_allocation(self, validator, allowed_symbols, invalid_allocation):
        """Test validation fails for invalid allocation values."""
        node = {
            "type": "order",
            "side": "long",
            "allocation": invalid_allocation,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.allocation must be one of:" in error for error in errors)
    
    @pytest.mark.parametrize("valid_allocation", ["equal", "weighted", "custom"])
    def test_order_valid_allocations(self, validator, allowed_symbols, valid_allocation):
        """Test validation passes for valid allocation values."""
        node = {
            "type": "order",
            "side": "long",
            "allocation": valid_allocation,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert not any("order.allocation" in error for error in errors)
    
    def test_order_negative_size(self, validator, allowed_symbols):
        """Test validation fails for negative size."""
        node = {
            "type": "order",
            "side": "long",
            "size": -10.0,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.size must be >= 0" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_size", ["10.0", [], {}, "True"])
    def test_order_invalid_size_type(self, validator, allowed_symbols, invalid_size):
        """Test validation fails for non-numeric size types."""
        node = {
            "type": "order",
            "side": "long",
            "size": invalid_size,
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.size must be a number when provided" in error for error in errors)
    
    def test_order_no_symbols_found(self, validator, allowed_symbols):
        """Test validation fails when no symbols are found."""
        node = {
            "type": "order",
            "side": "long"
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("No symbols found" in error for error in errors)
    
    def test_order_invalid_symbols(self, validator, allowed_symbols):
        """Test validation fails for symbols not in allowed list."""
        node = {
            "type": "order",
            "side": "long",
            "weights": {"AAPL": 0.5, "GOOGL": 0.5}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("Symbols not allowed:" in error for error in errors)
    
    def test_order_missing_weights(self, validator, allowed_symbols):
        """Test validation fails when weights are missing for symbols."""
        node = {
            "type": "order",
            "side": "long",
            "universe": ["SPY", "TQQQ"],
            "weights": {"SPY": 0.5}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("Missing weight(s) for:" in error for error in errors)
    
    def test_order_negative_weight(self, validator, allowed_symbols):
        """Test validation fails for negative weights."""
        node = {
            "type": "order",
            "side": "long",
            "weights": {"SPY": -0.5}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("Weight for SPY must be >= 0" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_weight", [[], {}, True])
    def test_order_invalid_weight_type(self, validator, allowed_symbols, invalid_weight):
        """Test validation fails for non-numeric weight types."""
        node = {
            "type": "order",
            "side": "long",
            "weights": {"SPY": invalid_weight}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("Weight for SPY must be a number" in error for error in errors)
    
    def test_order_symbol_filter(self, validator, allowed_symbols):
        """Test validation with symbol_filter."""
        node = {
            "type": "order",
            "side": "long",
            "symbol_filter": "SPY",
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert errors == []
    
    def test_order_universe_list(self, validator, allowed_symbols):
        """Test validation with universe as list."""
        node = {
            "type": "order",
            "side": "long",
            "universe": ["SPY", "TQQQ"],
            "weights": {"SPY": 0.6, "TQQQ": 0.4}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is True
        assert errors == []
    
    def test_order_invalid_universe_type(self, validator, allowed_symbols):
        """Test validation fails for invalid universe type."""
        node = {
            "type": "order",
            "side": "long",
            "universe": "SPY",
            "weights": {"SPY": 1.0}
        }
        is_valid, errors = validator.validate_order_node(node, allowed_symbols)
        
        assert is_valid is False
        assert any("order.universe must be an array of strings" in error for error in errors)


class TestValidateGroupNode:
    
    def test_valid_group_node_minimal(self, validator):
        """Test validation with minimal valid group node."""
        node = {
            "type": "group",
            "children": [{"type": "condition"}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is True
        assert errors == []
    
    def test_valid_group_node_complete(self, validator):
        """Test validation with complete group node."""
        node = {
            "id": "group_1",
            "type": "group",
            "description": "Test group",
            "children": [
                {"type": "condition"},
                {"type": "order"}
            ]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is True
        assert errors == []
    
    def test_group_node_not_dict(self, validator):
        """Test validation fails when node is not a dictionary."""
        test_cases = [None, [], "string", 123]
        
        for node in test_cases:
            is_valid, errors = validator.validate_group_node(node)
            assert is_valid is False
            assert any("group node must be a dict" in error for error in errors)
    
    def test_group_wrong_type(self, validator):
        """Test validation fails when type is not 'group'."""
        node = {
            "type": "condition",
            "children": [{"type": "order"}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is False
        assert any("node.type must be 'group'" in error for error in errors)
    
    def test_group_invalid_id_type(self, validator):
        """Test validation fails for non-string id."""
        node = {
            "type": "group",
            "id": 123,
            "children": [{"type": "condition"}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is False
        assert any("group.id must be a string when provided" in error for error in errors)
    
    def test_group_invalid_description_type(self, validator):
        """Test validation fails for non-string description."""
        node = {
            "type": "group",
            "description": 123,
            "children": [{"type": "condition"}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is False
        assert any("group.description must be a string when provided" in error for error in errors)
    
    def test_group_empty_children(self, validator):
        """Test validation fails for empty children when required."""
        node = {
            "type": "group",
            "children": []
        }
        is_valid, errors = validator.validate_group_node(node, require_children=True)
        
        assert is_valid is False
        assert any("group must contain at least one child" in error for error in errors)
    
    def test_group_child_invalid_type(self, validator):
        """Test validation fails for invalid child type."""
        node = {
            "type": "group",
            "children": [{"type": "invalid_type"}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is False
        assert any("is not allowed here" in error for error in errors)
    
    def test_group_child_no_type(self, validator):
        """Test validation fails when child has no type."""
        node = {
            "type": "group",
            "children": [{}]
        }
        is_valid, errors = validator.validate_group_node(node)
        
        assert is_valid is False
        assert any("group.child[0].type must be a string" in error for error in errors)
    
    def test_group_require_description(self, validator):
        """Test validation with required description."""
        node = {
            "type": "group",
            "children": [{"type": "condition"}]
        }
        is_valid, errors = validator.validate_group_node(node, require_description=True)
        
        assert is_valid is False
        assert any("group.description is required" in error for error in errors)
    
    def test_group_valid_description_required(self, validator):
        """Test validation passes with valid required description."""
        node = {
            "type": "group",
            "description": "Valid description",
            "children": [{"type": "condition"}]
        }
        is_valid, errors = validator.validate_group_node(node, require_description=True)
        
        assert is_valid is True
        assert errors == []


class TestValidateConditionNode:
    
    def test_valid_condition_node_basic(self, validator, allowed_metrics, allowed_symbols):
        """Test validation with basic valid condition node."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is True
        assert errors == []
    
    def test_valid_condition_crosses(self, validator, allowed_metrics, allowed_symbols):
        """Test validation with crosses operator."""
        node = {
            "type": "condition",
            "operator": "crosses_above",
            "lhs": {"name": "sma", "args": {"period": 20}, "symbol": "SPY"},
            "rhs": {"name": "sma", "args": {"period": 50}, "symbol": "SPY"}
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is True
        assert errors == []
    
    def test_condition_node_not_dict(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when node is not a dictionary."""
        test_cases = [None, [], "string", 123]
        
        for node in test_cases:
            is_valid, errors = validator.validate_condition_node(
                node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
            )
            assert is_valid is False
            assert any("condition node must be a dict" in error for error in errors)
    
    def test_condition_wrong_type(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when type is not 'condition'."""
        node = {
            "type": "group",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("node.type must be 'condition'" in error for error in errors)
    
    @pytest.mark.parametrize("invalid_operator", [
        "greater_than", "less_than", "equals", "not_equals", 123, []
    ])
    def test_condition_invalid_operator(self, validator, allowed_metrics, allowed_symbols, invalid_operator):
        """Test validation fails for invalid operators."""
        node = {
            "type": "condition",
            "operator": invalid_operator,
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("condition.operator must be one of" in error for error in errors)
    
    @pytest.mark.parametrize("valid_operator", [
        "gt", "gte", "lt", "lte", "eq", "neq", "crosses_above", "crosses_below"
    ])
    def test_condition_valid_operators(self, validator, allowed_metrics, allowed_symbols, valid_operator):
        """Test validation passes for valid operators."""
        if valid_operator in ["crosses_above", "crosses_below"]:
            # Crosses operators require both operands to be metrics
            node = {
                "type": "condition",
                "operator": valid_operator,
                "lhs": {"name": "sma", "args": {"period": 20}, "symbol": "SPY"},
                "rhs": {"name": "sma", "args": {"period": 50}, "symbol": "SPY"}
            }
        else:
            node = {
                "type": "condition",
                "operator": valid_operator,
                "lhs": {"name": "current-price", "symbol": "SPY"},
                "rhs": 100.0
            }
        
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is True
        assert not any("condition.operator" in error for error in errors)
    
    def test_condition_missing_lhs_operator(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when both lhs and operator are missing or only one is present."""
        # Missing both
        node = {
            "type": "condition",
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        print(f"is_valid: {is_valid}, errors: {errors}")
        
        assert is_valid is True  # Both missing is allowed
        
        # Only lhs present
        node = {
            "type": "condition",
            "lhs": {"name": "current-price", "symbol": "SPY"}
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("All two of condition.lhs, and condition.operator are required" in error for error in errors)
    
    def test_condition_crosses_with_literal(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for crosses operators with literals."""
        node = {
            "type": "condition",
            "operator": "crosses_above",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("requires both lhs and rhs to be metrics" in error for error in errors)
    
    def test_condition_comparison_both_literals(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for comparison operators with both literals."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": 50.0,
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("requires at least one operand to be a metric" in error for error in errors)
    
    def test_condition_invalid_metric_name(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for invalid metric name."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "invalid-metric", "symbol": "SPY"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("is not in allowed_metrics" in error for error in errors)
    
    def test_condition_invalid_symbol(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for invalid symbol."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "AAPL"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("is not in allowed_symbols" in error for error in errors)
    
    def test_condition_missing_required_symbol(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when symbol is required but missing."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price"},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols,
            require_symbol_for_metrics=True
        )
        
        assert is_valid is False
        assert any("metric.symbol is required" in error for error in errors)
    
    def test_condition_metric_requires_period(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when metric requires period but it's missing."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "moving-average-price", "symbol": "SPY", "args": {}},
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("requires args.period as positive int" in error for error in errors)
    
    def test_condition_metric_invalid_period(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for invalid period values."""
        test_cases = [-1, 0, "10", 10.5]
        
        for period in test_cases:
            node = {
                "type": "condition",
                "operator": "gt",
                "lhs": {"name": "rsi", "symbol": "SPY", "args": {"period": period}},
                "rhs": 50.0
            }
            is_valid, errors = validator.validate_condition_node(
                node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
            )
            
            assert is_valid is False
            assert any("requires args.period as positive int" in error for error in errors)
    
    def test_condition_invalid_operand_type(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails for invalid operand types."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": "invalid",
            "rhs": 100.0
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols
        )
        
        assert is_valid is False
        assert any("operand must be a metric object or a numeric literal" in error for error in errors)
    
    def test_condition_with_else_branch(self, validator, allowed_metrics, allowed_symbols):
        """Test validation with else branch."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0,
            "children": [
                {"type": "group", "description": "then", "children": [{"type": "order"}]},
                {"type": "group", "description": "else", "children": [{"type": "order"}]}
            ]
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols,
            validate_else=True, else_label="else"
        )
        
        assert is_valid is True
        assert errors == []
    
    def test_condition_else_not_last(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails when else branch is not last."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0,
            "children": [
                {"type": "group", "description": "else", "children": [{"type": "order"}]},
                {"type": "group", "description": "then", "children": [{"type": "order"}]}
            ]
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols,
            validate_else=True, else_label="else", else_must_be_last=True
        )
        
        assert is_valid is False
        assert any("Else branch must be the last direct child" in error for error in errors)
    
    def test_condition_multiple_else_branches(self, validator, allowed_metrics, allowed_symbols):
        """Test validation fails with multiple else branches."""
        node = {
            "type": "condition",
            "operator": "gt",
            "lhs": {"name": "current-price", "symbol": "SPY"},
            "rhs": 100.0,
            "children": [
                {"type": "group", "description": "then", "children": [{"type": "order"}]},
                {"type": "group", "description": "else", "children": [{"type": "order"}]},
                {"type": "group", "description": "else", "children": [{"type": "order"}]}
            ]
        }
        is_valid, errors = validator.validate_condition_node(
            node, allowed_metrics=allowed_metrics, allowed_symbols=allowed_symbols,
            validate_else=True, else_label="else"
        )
        
        assert is_valid is False