# Validation rules configuration for story and epic fields
FIELD_VALIDATION_RULES = {
    "Summary": {
        "is_required": True
    },
    "Priority": {
        "is_required": True,
        "allowed_values": ["Highest", "High", "Medium", "Low", "Lowest"]
    },
    "Component": {
    },
    "Fix Version": {
        
    },
    "Label": {
    },
    "Acceptance Criteria": {

    },
    "Description": {

    },
    "Assignee": {

    },
    "Sprint": {

    },
    "Story Point Estimate": {

        "allowed_values": [1, 2, 3, 5, 8, 13, 21]
    },
    "Reporter": {

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