from typing import Dict, Iterable, Set
from typing import Any, Dict, Iterable, Optional, Set, List, Tuple
import sys

_CONDITION_OPS = {"gt","gte","lt","lte","eq","neq","crosses_above","crosses_below"}


allowed_metrics = [
    "current-price",
    "sma",
    "ema",
    "rsi",
    "cumulative-return",
    "moving-avg-price",
    "moving-avg-return",
    "std-dev-price",
    "std-dev-return",
    "max-drawdown",
    "volatility",
    "returns",
    "drawdown",
    "vix",
    "month",
    "day-of-week",
    "day-of-month",
    "day-of-year",
    "moving-average-price",
    "exponential-moving-average-price",
    "standard-deviation-price",
]
allowed_symbols = ["TQQQ","SQQQ","BSV","SPY"]

# Defaults (hyphenated)
DEFAULT_ALLOWED_METRICS: Set[str] = set(allowed_metrics)


# All node types allowed by your schema
_SCHEMA_NODE_TYPES: Set[str] = {
    "group", "condition", "filter", "order", "exit", "expression", "weight"
}


# Metrics that typically require a positive integer 'period' in args
METRICS_REQUIRE_PERIOD: Set[str] = {
    "sma", "ema", "rsi",
    "moving-avg-price", "moving-avg-return",
    "std-dev-price", "std-dev-return",
    "volatility", "returns", "drawdown",
}

class LogicValidator:

    @staticmethod
    def validate_order_node(node: Dict, allowed_tickers: Iterable[str]) -> Dict:
        """
        Validate a single 'order' node against basic rules + an allowed tickers list.

        Enforced:
        - node['type'] == 'order'
        - side in {'long','short'}
        - size_type in {'percent_equity','fixed_qty','fixed_value','risk_based'}
        - allocation in {'equal','weighted','custom'}
        - Symbols referenced by the node must be a subset of allowed_tickers
        - Every referenced symbol must have a weight (explicitly)
        - If allocation == 'weighted', weights must be >=0 and sum to 1.0 (±1e-6)

        Returns:
        A normalized dict: {'symbols': [..], 'weights': {sym: float, ...}} for downstream use.

        Raises:
        ValueError with a precise message when the node is invalid.
        """
        
        error_lines = []
        
        if not isinstance(node, dict):
            error_lines.append("order node must be a dict")
            
            return False, error_lines
            
        node_id = node.get("id")

        # --- Basic required fields ---
        if node.get("type") != "order":
            error_lines.append("For order '{node_id}', node.type must be 'order'")
            
            return False, error_lines

        id_string = node.get("id")
        if id_string and not isinstance(id_string, str):
            error_lines.append("order.id must be a string when provided")

        side = node.get("side")
        
        if not isinstance(side, str):
            
            error_lines.append("For order '{node_id}', order.side must be a string")

            side = ""            
        
        if side not in {"long", "short"}:
            error_lines.append(f"For order '{node_id}', order.side must be 'long' or 'short'")
            
        size_type = node.get("size_type", "percent_equity")        
    
        
        if size_type not in {"percent_equity", "fixed_qty", "fixed_value", "risk_based"}:
            error_lines.append(f"For order '{node_id}', order.size_type must be one of: percent_equity, fixed_qty, fixed_value, risk_based")

        allocation = node.get("allocation", "equal")
        
        if not isinstance(allocation, str):
            
            error_lines.append("For order '{node_id}', order.allocation must be a string")

            allocation = ""
        
        if allocation not in {"equal", "weighted", "custom"}:
            error_lines.append(f"For order '{node_id}', order.allocation must be one of: equal, weighted, custom")

        # size is generally required except for some risk models; enforce when present
        if "size" in node and not isinstance(node["size"], (int, float)):
            error_lines.append("For order '{node_id}', order.size must be a number when provided")
        
        elif "size" in node and float(node["size"]) < 0:
            error_lines.append("For order '{node_id}', order.size must be >= 0")

        # --- Determine symbols referenced by the node ---
        weights = node.get("weights") or {}

        if not isinstance(weights, dict):
            error_lines.append("For order '{node_id}', order.weights must be an object/dict when provided")

        # Symbols may come from weights keys, or a single symbol_filter, or a universe array.
        symbols = set()  # type: Set[str]

        if weights:
            symbols |= {str(s).upper() for s in weights.keys()}

        symbol_filter = node.get("symbol_filter")
        if symbol_filter:
            symbols.add(str(symbol_filter).upper())



        universe = node.get("universe") or []
        if universe:
            if not isinstance(universe, list) or not all(isinstance(s, str) for s in universe):
                error_lines.append("For order '{node_id}', order.universe must be an array of strings when provided")
            symbols |= {s.upper() for s in universe}

        if not symbols:
            error_lines.append("For order '{node_id}', No symbols found: provide at least one via weights, symbol_filter, or universe")

        

        # --- Allowed tickers check ---
        allowed = {str(s).upper() for s in allowed_tickers}
        invalid = sorted(sym for sym in symbols if sym not in allowed)
        if invalid:
            error_lines.append(f"For order '{node_id}', Symbols not allowed: {', '.join(invalid)}")

        # --- Weight requirements ---
        # Requirement from spec: for every symbol provided there should be a weight.
        # So we require explicit weights for ALL referenced symbols (even if symbol_filter/universe used).
        missing_weights = [sym for sym in symbols if sym not in {k.upper() for k in weights.keys()}]
        if missing_weights:
            error_lines.append(f"For order '{node_id}', Missing weight(s) for: {', '.join(sorted(missing_weights))}")

        # Coerce weights to floats; validate non-negativity
        norm_weights: Dict[str, float] = {}
        for k, v in weights.items():
            sym = str(k).upper()
            if sym not in symbols:
                # If someone passed an extra weight for a symbol not referenced elsewhere, forbid it
                error_lines.append(f"For order '{node_id}', Unexpected weight for symbol not referenced by node: {sym}")
            try:
                
                if isinstance(v, list) or isinstance(v, dict) or isinstance(v, bool):
                    
                    error_lines.append(f"For order '{node_id}', Weight for {sym} must be a number")
                    
                    continue
                
                w = float(v)
            except Exception:
                error_lines.append(f"For order '{node_id}', Weight for {sym} must be a number")
            if w < 0:
                error_lines.append(f"For order '{node_id}', Weight for {sym} must be >= 0")
            norm_weights[sym] = w

        # If weighted allocation, enforce sum to 1.0 (± tolerance)
        # if allocation == "weighted":
        #     total = sum(norm_weights.get(sym, 0.0) for sym in symbols)
        #     if abs(total - 1.0) > 1e-6:
        #         error_lines.append(f"Weighted allocation requires weights to sum to 1.0; got {total:.6f}")

        # For 'equal' or 'custom' we still enforce "every symbol has a weight" per your requirement,
        # but we don't force the sum to 1.0. If you want to enforce a specific sum there too, add it here.
        
        is_valid = len(error_lines) == 0
        
        return is_valid, error_lines

    @staticmethod
    def validate_group_node(
        node: Dict[str, Any],
        *,
        require_children: bool = True,
        allowed_child_types: Optional[Iterable[str]] = None,
        require_description: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate a single 'group' node and the shape of its immediate children.

        Checks:
        - node is a dict and node['type'] == 'group'
        - optional: description must be a non-empty string (require_description)
        - children is a list (if present/required)
        - each direct child is a dict with a valid 'type'
        - if allowed_child_types is provided, each child.type ∈ allowed_child_types

        Returns:
        {
            "id": str|None,
            "description": str|None,
            "child_count": int,
            "child_types": [str, ...]
        }

        Raises:
        ValueError with clear messages if invalid.
        """
        
        error_lines = []
        
        if not isinstance(node, dict):
            error_lines.append("group node must be a dict")
            return False, error_lines
            
        node_id = node.get("id")

        if node.get("type") != "group":
            error_lines.append("For order '{node_id}', node.type must be 'group'")

        node_id = node.get("id")
        if node_id is not None and not isinstance(node_id, str):
            error_lines.append("For order '{node_id}', group.id must be a string when provided")

        desc = node.get("description")
        if require_description:
            if not isinstance(desc, str) or not desc.strip():
                error_lines.append("For order '{node_id}', group.description is required and must be a non-empty string")
        else:
            if desc is not None and not isinstance(desc, str):
                error_lines.append("For order '{node_id}', group.description must be a string when provided")

        children = node.get("children", [])
        if children is None:
            children = []

        if require_children and not isinstance(children, list):
            error_lines.append("For order '{node_id}', group.children must be an array when provided")

        if require_children and len(children) == 0:
            error_lines.append("For order '{node_id}', group must contain at least one child")

        if not isinstance(children, list):
            # if not required and absent, normalize to empty list
            error_lines.append("For order '{node_id}', group.children must be an array if present")

        allowed_types: Set[str] = _SCHEMA_NODE_TYPES

        child_types: List[str] = []
        for idx, child in enumerate(children):
            if not isinstance(child, dict):
                error_lines.append(f"For order '{node_id}', group.child[{idx}] must be an object")
            ctype = child.get("type")
            if not isinstance(ctype, str):
                error_lines.append(f"For order '{node_id}', group.child[{idx}].type must be a string")

            if ctype not in allowed_types:
                error_lines.append(
                    f"For order '{node_id}', group.child[{idx}].type '{ctype}' is not allowed here (allowed: {sorted(allowed_types)})"
                    )
                
            child_types.append(ctype)

        is_valid = len(error_lines) == 0
        
        return is_valid, error_lines

    @staticmethod
    def validate_condition_node(
        node: Dict[str, Any],
        *,
        allowed_metrics: Optional[Iterable[str]] = None,
        allowed_symbols: Optional[Iterable[str]] = None,
        require_symbol_for_metrics: bool = True,
        # ---- Else-branch validation knobs ----
        validate_else: bool = True,
        else_required: bool = False,
        else_label: str = "Else branch",     # case-insensitive match on child.description
        else_must_be_last: bool = True,
        else_require_children: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a single 'condition' node (and its immediate Else branch if present),
        collecting all issues into an errors list instead of raising exceptions.

        Returns:
        {
            "ok": bool,             # False if any errors were collected
            "errors": [str, ...],   # human-readable error messages
            "normalized": {         # only present when ok=True
            "id": str|None,
            "description": str|None,
            "operator": str,
            "lhs": {"kind":"metric","name":...,"args":{...},"symbol":...} | {"kind":"literal","value":float},
            "rhs": {...},
            "symbols_used": [..],
            "else_branch": {
                "present": bool,
                "index": int|None,
                "child_count": int|None
            }
            }
        }
        """
        errors: List[str] = []

        def _fail(msg: str) -> Dict[str, Any]:
            errors.append(msg)
            return {"ok": False, "errors": errors}

        if not isinstance(node, dict):
            errors.append("condition node must be a dict")
            return False, errors
        
        node_id = node.get("id")

        if node.get("type") != "condition":
            errors.append("For condition '{node_id}', node.type must be 'condition'")

        op = node.get("operator")
        
        
        flag_check_for_operator = True
        
        if not(("lhs" not in node and "operator" not in node) or ("lhs" in node and "operator" in node)):
            
            errors.append(f"For condition '{node_id}', All two of condition.lhs, and condition.operator are required")
            
        elif "lhs" not in node and "operator" not in node:
            
                flag_check_for_operator = False
                    
        if flag_check_for_operator and not isinstance(op, str):
            
            errors.append("For condition '{node_id}', condition.operator must be a string")
            
            op = ""
        
        if flag_check_for_operator and op is not None and op not in _CONDITION_OPS:
            errors.append(f"condition.operator must be one of {sorted(_CONDITION_OPS)}")

        allowed_metrics_set: Optional[Set[str]] = set(m.lower() for m in allowed_metrics) if allowed_metrics else None
        allowed_symbols_set: Optional[Set[str]] = set(s.upper() for s in allowed_symbols) if allowed_symbols else None

        # ---- helpers ----
        def _is_number(x: Any) -> bool:
            return isinstance(x, (int, float)) and not isinstance(x, bool)

        def _validate_metric(m: Any, side: str) -> Tuple[Optional[Dict[str, Any]], None]:
            if not isinstance(m, dict):
                errors.append(f"For condition '{node_id}', {side}: metric operand must be an object")
                return None, None
            name = m.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"For condition '{node_id}', {side}: metric.name must be a non-empty string")
                return None, None
            lname = name.strip().lower()

            if allowed_metrics_set is not None and lname not in allowed_metrics_set:
                errors.append(f"For condition '{node_id}', {side}: metric.name '{name}' is not in allowed_metrics")

            args = m.get("args", {})
            if args is None:
                args = {}
            if not isinstance(args, dict):
                errors.append(f"For condition '{node_id}', {side}: metric.args must be a dict when provided")
                args = {}

            sym = m.get("symbol")
            sym_norm = None
            if require_symbol_for_metrics:
                if not isinstance(sym, str) or not sym.strip():
                    errors.append(f"For condition '{node_id}', {side}: metric.symbol is required and must be a non-empty string")
                else:
                    sym_norm = sym.strip().upper()
            elif isinstance(sym, str) and sym.strip():
                sym_norm = sym.strip().upper()

            if allowed_symbols_set is not None and sym_norm is not None and sym_norm not in allowed_symbols_set:
                errors.append(f"For condition '{node_id}', {side}: symbol '{sym_norm}' is not in allowed_symbols")

            # minimal metric-specific checks (extend as needed)
            if lname in {"moving-average-price", "rsi"}:
                period = args.get("period")
                if not isinstance(period, int) or period <= 0:
                    errors.append(f"For condition '{node_id}', {side}: metric '{name}' requires args.period as positive int")

            return {"kind": "metric", "name": name, "args": args, "symbol": sym_norm}, None

        def _parse_operand(x: Any, side: str) -> Dict[str, Any]:
            # metric object?
            if isinstance(x, dict) and "name" in x:
                parsed, _ = _validate_metric(x, side)
                if parsed is None:
                    return {"kind": "invalid"}
                return parsed
            # numeric literal?
            if _is_number(x):
                return {"kind": "literal", "value": float(x)}
            errors.append(f"For condition '{node_id}', {side}: operand must be a metric object or a numeric literal")
            return {"kind": "invalid"}

        # ---- parse operands ----
        
        if "lhs" in node:
        
            lhs_norm = _parse_operand(node["lhs"], "lhs")
            
        else:
            
            lhs_norm = {"kind": "invalid"}
            
        if "rhs" in node:
            
            rhs_norm = _parse_operand(node["rhs"], "rhs")
            
        else:
            
            rhs_norm = {"kind": "invalid"}
            
        node_id = node.get("id")
                

        # ---- operator-specific constraints ----
        if flag_check_for_operator and op in {"crosses_above", "crosses_below"}:
            if lhs_norm.get("kind") != "metric" or rhs_norm.get("kind") != "metric":
                errors.append(f"For condition '{node_id}',{op} requires both lhs and rhs to be metrics (no literals)")

        if flag_check_for_operator and op in {"gt","gte","lt","lte","eq","neq"}:
            if lhs_norm.get("kind") == "literal" and rhs_norm.get("kind") == "literal":
                errors.append(f"For condition '{node_id}', {op} requires at least one operand to be a metric")

        # ---- optional id/description ----
        node_id = node.get("id")
        if node_id is not None and not isinstance(node_id, str):
            errors.append(f"For condition '{node_id}', condition.id must be a string when provided")
            node_id = None

        desc = node.get("description")
        if desc is not None and not isinstance(desc, str):
            errors.append("For condition '{node_id}', condition.description must be a string when provided")
            desc = None

        # ---- Else branch validation (only immediate children) ----
        else_info = {"present": False, "index": None, "child_count": None}

        if validate_else:
            children = node.get("children", [])
            if children is None:
                children = []
            if not isinstance(children, list):
                errors.append(f"For condition '{node_id}', condition.children must be an array when provided")
                children = []

            # Find groups labeled as Else branch (case-insensitive match)
            label_norm = (else_label or "").strip().lower()

            def _is_else_group(c: Any) -> bool:
                if not isinstance(c, dict):
                    return False
                if c.get("type") != "group":
                    return False
                d = c.get("description")
                return isinstance(d, str) and d.strip().lower() == label_norm

            else_idxs: List[int] = [i for i, c in enumerate(children) if _is_else_group(c)]

            if else_required and not else_idxs:
                errors.append(f"For condition '{node_id}', condition requires an Else branch group but none was found")

            if len(else_idxs) > 1:
                errors.append(f"For condition '{node_id}',condition has multiple Else branch groups; only one is allowed")

            if else_idxs:
                idx = else_idxs[0]
                else_node = children[idx]
                if else_must_be_last and idx != len(children) - 1:
                    errors.append(f"For condition '{node_id}',Else branch must be the last direct child of the condition")

                eb_children = else_node.get("children", [])
                if eb_children is None:
                    eb_children = []
                if not isinstance(eb_children, list):
                    errors.append(f"For condition '{node_id}',Else branch 'children' must be an array")
                    eb_children = []
                if else_require_children and len(eb_children) == 0:
                    errors.append(f"For condition '{node_id}',Else branch must contain at least one child")

                # ensure there's at least one non-Else direct child (THEN branch)
                if len(children) - 1 < 1:
                    errors.append("Condition must have at least one non-Else child as the THEN branch")

                else_info.update({"present": True, "index": idx, "child_count": len(eb_children)})

        # ---- collect symbols used ----
        symbols_used: List[str] = []
        for side in (lhs_norm, rhs_norm):
            if side.get("kind") == "metric" and side.get("symbol"):
                symbols_used.append(side["symbol"])
        symbols_used = sorted(set(symbols_used))

        is_valid = len(errors) == 0

        return is_valid, errors

    @staticmethod
    def validate_filter_node(
        node: Dict[str, Any],
        *,
        allowed_metrics: Optional[Iterable[str]] = None,
        allowed_symbols: Optional[Iterable[str]] = None,
        require_universe_nonempty: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a single 'filter' node. Does not recurse into grandchildren.

        Checks:
        - node.type == 'filter'
        - id/description types (if present)
        - universe: list[str], (optionally) non-empty, all in allowed_symbols (if provided), no duplicates
        - select ∈ {'top','bottom','middle'}
        - selection: requires integer 'n' with 1 <= n <= len(universe)
        - metric:
            * metric.name in allowed_metrics (hyphenated names)
            * metric.args is dict
            * if metric.name requires 'period', enforce positive int period
            * (No symbol here; metric is applied to each candidate in universe)

        Returns:
        {
            "ok": bool,
            "errors": [str, ...],
            "normalized": {             # only when ok=True
            "id": str|None,
            "description": str|None,
            "universe": [str, ...],   # uppercased, unique, order-preserving
            "select": str,            # 'top'|'bottom'|'middle'
            "n": int,
            "metric": {"name": str, "args": dict}
            }
        }
        """
        errors: List[str] = []

        # --- basic node shape ---
        if not isinstance(node, dict):
            
            errors.append("filter node must be a dict")
            
            return False. errors

        node_id = node.get("id")

        if node.get("type") != "filter":
            errors.append(f"For filter '{node_id}', node.type must be 'filter'")

        node_id = node.get("id")
        if node_id is not None and not isinstance(node_id, str):
            errors.append(f"For filter '{node_id}', filter.id must be a string when provided")
            node_id = None

        desc = node.get("description")
        if desc is not None and not isinstance(desc, str):
            errors.append(f"For filter '{node_id}', filter.description must be a string when provided")
            desc = None

        # --- universe ---
        raw_universe = node.get("universe", [])
        if raw_universe is None:
            raw_universe = []
        if not isinstance(raw_universe, list) or not all(isinstance(s, str) for s in raw_universe):
            errors.append(f"For filter '{node_id}', filter.universe must be an array of strings")
            raw_universe = []

        # normalize: uppercase, preserve order, drop duplicates
        seen: Set[str] = set()
        universe: List[str] = []
        for s in raw_universe:
            sym = s.strip().upper()
            if sym and sym not in seen:
                seen.add(sym)
                universe.append(sym)

        if require_universe_nonempty and len(universe) == 0:
            errors.append(f"For filter '{node_id}', filter.universe must contain at least one symbol")

        if allowed_symbols is not None:
            allowed_set = {a.strip().upper() for a in allowed_symbols}
            invalid = [s for s in universe if s not in allowed_set]
            if invalid:
                errors.append(f"For filter '{node_id}', filter.universe contains symbols not allowed: {', '.join(invalid)}")

        # --- select & selection.n ---
        select = node.get("select")
        if select not in {"top", "bottom", "middle"}:
            errors.append(f"For filter '{node_id}', filter.select must be one of: 'top', 'bottom', 'middle'")

        selection = node.get("selection", {})
        if selection is None or not isinstance(selection, dict):
            errors.append(f"For filter '{node_id}', filter.selection must be an object with at least 'n'")
            selection = {}
        n = selection.get("n")
        if not isinstance(n, int) or n <= 0:
            errors.append(f"For filter '{node_id}', filter.selection.n must be a positive integer")
        if isinstance(n, int) and n > len(universe) and len(universe) > 0:
            errors.append(f"For filter '{node_id}', filter.selection.n ({n}) cannot exceed universe size ({len(universe)})")

        # --- metric ---
        metric = node.get("metric")
        metric_name = None
        metric_args: Dict[str, Any] = {}

        if not isinstance(metric, dict):
            errors.append(f"For filter '{node_id}', filter.metric must be an object")
        else:
            metric_name = metric.get("name")
            if not isinstance(metric_name, str) or not metric_name.strip():
                errors.append(f"For filter '{node_id}', filter.metric.name must be a non-empty string")
            else:
                metric_name = metric_name.strip().lower()

                allowed_set = set(allowed_metrics) if allowed_metrics is not None else DEFAULT_ALLOWED_METRICS
                if metric_name not in allowed_set:
                    errors.append(f"For filter '{node_id}', filter.metric.name '{metric_name}' is not allowed")

            # symbol is not expected in filter.metric (ranking over universe)
            if "symbol" in metric and isinstance(metric["symbol"], str) and metric["symbol"].strip():
                errors.append(f"For filter '{node_id}', filter.metric.symbol should not be provided for a filter; metric applies to each universe symbol")

            metric_args = metric.get("args", {})
            if metric_args is None:
                metric_args = {}
            if not isinstance(metric_args, dict):
                errors.append(f"For filter '{node_id}', filter.metric.args must be an object when provided")
                metric_args = {}

            # period requirement (only if name parsed correctly)
            if metric_name in METRICS_REQUIRE_PERIOD:
                period = metric_args.get("period")
                if not isinstance(period, int) or period <= 0:
                    errors.append(f"For filter '{node_id}', filter.metric '{metric_name}' requires 'args.period' as a positive integer")

        is_valid = len(errors) == 0
        
        return is_valid, errors

    @staticmethod
    def validate_weight_node(node: Dict, allowed_symbols: Iterable[str]) -> Dict:
        """
        Validate a single 'weight' node.

        Args:
            node (Dict): _description_
            allowed_symbols (Iterable[str]): _description_

        Returns:
            Dict: _description_
        """
        
        ALLOCATION_METHODS = ["explicit_weights", "inverse_volatility"]
        
        type_of_node = node.get("type")
        
        error_lines = []
        
        if not isinstance(node, dict):
            
            error_lines.append("Weight node must be a dict")
            
            return False, error_lines
        
        node_id = node.get("id")
        
        if type_of_node != "weight":
            
            error_lines.append(f"For weight {node_id}, Weight node must be a type 'weight'")
            
        allocation_method = node.get("allocation_method")
        
        if allocation_method is None:
            
            error_lines.append(f"For weight {node_id}, Weight node must have an allocation_method")
            
        elif allocation_method not in ALLOCATION_METHODS:
            
            error_lines.append(f"For weight {node_id}, Weight node allocation_method must be one of: {', '.join(ALLOCATION_METHODS)}")

        is_valid = len(error_lines) == 0
        
        return is_valid, error_lines

    @staticmethod
    def handle_validation_errors(is_valid, errors):
        """_summary_

        Args:
            is_valid (bool): _description_
            errors (_type_): _description_
        """
        
        if not is_valid:
            
            for error in errors:
                
                print(f"Error: {error}")
                
            
            sys.exit()

    @staticmethod
    def check_node_type_and_validate(data, allowed_symbols):
        """_summary_

        Args:
            data (_type_): _description_
            allowed_symbols (_type_): _description_
        """
        
        # Get node type
        type_of_node = data.get('type')
            
        # Validate node type
        if type_of_node == 'condition':
            
            # Validate condition node
            is_valid, errors = LogicValidator.validate_condition_node(data)
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(is_valid, errors)
            
        # Validate group node
        elif type_of_node == 'group':
            
            # Validate group node
            is_valid, errors = LogicValidator.validate_group_node(data)
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(is_valid, errors)
            
        # Validate order node
        elif type_of_node == 'order':
            
            # Validate order node
            is_valid, errors = LogicValidator.validate_order_node(data, allowed_symbols)
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(is_valid, errors)
            
        # Validate filter node
        elif type_of_node == 'filter':
            
            # Validate filter node
            is_valid, errors = LogicValidator.validate_filter_node(data, allowed_symbols=allowed_symbols)
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(is_valid, errors)
            
        elif type_of_node == 'weight':
            
            # Validate weight node
            is_valid, errors = LogicValidator.validate_weight_node(data, allowed_symbols=allowed_symbols)
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(is_valid, errors)
            
        else:
            
            # Unknown node type
            errors = [f"Unknown node type: {type_of_node}"]
            
            # Handle validation errors
            LogicValidator.handle_validation_errors(False, errors)
    
    def __init__(self):
        
        pass
    
    @staticmethod
    def trace_json_data_recursive(data: Any, allowed_symbols: list) -> str:
        """
        This method is used to recursively trace the JSON data and validate it against the allowed symbols.

        Args:
            data (Any): _description_
            allowed_symbols (list): _description_

        """
        
        # Check if children exist
        if 'children' in data:
            
            # Get children data
            chidren_data = data['children']
            
            # Check if children data is a list
            if isinstance(chidren_data, list):
                
                # Iterate over each child
                for item in chidren_data:
                    
                    # Check if item is a dictionary
                    if isinstance(item, dict):
                        
                        # Validate and trace the child
                        LogicValidator.check_node_type_and_validate(item, allowed_symbols)
                    
                        # Recursively trace the child
                        LogicValidator.trace_json_data_recursive(item, allowed_symbols)
                
            # Check if children data is a dictionary
            elif isinstance(chidren_data, dict):
                
                # Validate and trace the children
                LogicValidator.check_node_type_and_validate(chidren_data, allowed_symbols)
                
                # Recursively trace the children
                LogicValidator.trace_json_data_recursive(chidren_data, allowed_symbols)
                
            
        else:
            
            # Validate and trace the data
            LogicValidator.check_node_type_and_validate(data, allowed_symbols)
            
    
    def validate_logic(self, logic: Any, allowed_symbols: list) -> Dict[str, Any]:
        
        LogicValidator.trace_json_data_recursive(logic, allowed_symbols)