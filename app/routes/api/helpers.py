from flask import jsonify, request

def api_success(data, meta=None, status=200):
    response = {"success": True, "data": data}
    if meta is not None:
        response["meta"] = meta
    return jsonify(response), status

def api_error(code, message, details=None, status=400):
    error_payload = {
        "code": code,
        "message": message
    }
    if details is not None:
        error_payload["details"] = details
    return jsonify({"success": False, "error": error_payload}), status

def paginate_query(query, page=None, per_page=None, serialize_fn=None):
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = pagination.items
    if serialize_fn:
        serialized_items = [serialize_fn(item) for item in items]
    else:
        serialized_items = [item.to_dict() if hasattr(item, 'to_dict') else str(item) for item in items]
        
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages
    }
    
    return serialized_items, meta

def validate_payload(data, schema):
    errors = {}
    sanitized = {}
    for field, rule in schema.items():
        val = data.get(field)
        
        # Check required
        if rule.get('required', False) and val is None:
            errors[field] = "Pole jest wymagane"
            continue
            
        if val is None:
            sanitized[field] = None
            continue
            
        # Type coercion/checks
        expected_type = rule.get('type')
        if expected_type:
            if expected_type == int:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    errors[field] = "Musi być liczbą całkowitą"
                    continue
            elif expected_type == float:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    errors[field] = "Musi być liczbą"
                    continue
            elif expected_type == str:
                val = str(val)
                
        # String trimming
        if isinstance(val, str):
            val = val.strip()
            if rule.get('lowercase_email', False):
                val = val.lower()
                
        # Range/Values checks
        if 'min' in rule and val < rule['min']:
            errors[field] = f"Wartość minimalna to {rule['min']}"
            continue
        if 'max' in rule and val > rule['max']:
            errors[field] = f"Wartość maksymalna to {rule['max']}"
            continue
        if 'choices' in rule and val not in rule['choices']:
            errors[field] = f"Niedozwolona wartość. Wybierz spośród: {rule['choices']}"
            continue
            
        sanitized[field] = val
        
    return sanitized, errors
