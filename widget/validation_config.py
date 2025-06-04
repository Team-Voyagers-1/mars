# Validation rules configuration for story and epic fields
FIELD_VALIDATION_RULES = {
    "Summary": {
        "is_required": True,
        "field_type": "string",
        "min_length": 10,
        "max_length": 255
    },
    "Priority": {
        "is_required": True,
        "allowed_values": ["Highest", "High", "Medium", "Low", "Lowest"],
        "field_type": "string"
    },
    "Component": {
        "is_required": True,
        "field_type": "string"
    },
    "Fix Version": {
        "is_required": False,
        "field_type": "string"
    },
    "Label": {
        "is_required": False,
        "field_type": "string"
    },
    "Acceptance Criteria": {
        "is_required": True,
        "field_type": "string",
        "min_length": 20
    },
    "Description": {
        "is_required": True,
        "field_type": "string",
        "min_length": 50
    },
    "Assignee": {
        "is_required": True,
        "field_type": "string"
    },
    "Sprint": {
        "is_required": False,
        "field_type": "string"
    },
    "Story Point Estimate": {
        "is_required": True,
        "field_type": "number",
        "allowed_values": [1, 2, 3, 5, 8, 13, 21]
    },
    "Reporter": {
        "is_required": True,
        "field_type": "string"
    }
}

def get_required_fields():
    """
    Get list of all required fields
    """
    return [field for field, rules in FIELD_VALIDATION_RULES.items() 
            if rules.get("is_required", False)]

def get_fields_with_allowed_values():
    """
    Get dictionary of fields that have allowed values
    """
    return {field: rules["allowed_values"] 
            for field, rules in FIELD_VALIDATION_RULES.items() 
            if "allowed_values" in rules} 