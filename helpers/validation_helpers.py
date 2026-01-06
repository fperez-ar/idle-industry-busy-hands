"""Input validation and formatting utilities."""

from typing import Tuple, Union


def validate_numeric_field(value_str: str,
                           is_integer: bool = False,
                           min_val: float = -100.0,
                           max_val: float = 100.0) -> Union[int, float]:
    """
    Validate and convert numeric field value.

    Args:
        value_str: String value to validate
        is_integer: If True, return integer; if False, return float
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated numeric value (defaults to 0 if invalid)
    """
    if not value_str or value_str in ('-', '.', '-.'):
        return 0 if is_integer else 0.0

    try:
        value = float(value_str)
        value = max(float(min_val), min(float(max_val), value))
        if is_integer:
            return int(value)
        else:
            # Round to 2 decimal places
            return round(value, 2)
    except ValueError:
        return 0 if is_integer else 0.0




def format_numeric_input(current_value: str, new_char: str,
                        is_integer: bool = False) -> str:
    """
    Format numeric input for text fields.

    Args:
        current_value: Current string value in the field
        new_char: New character being added
        is_integer: If True, only allow integers; if False, allow floats

    Returns:
        Formatted string if valid, None if invalid
    """
    # Handle empty field
    if current_value in ('0', '0.0', '', '-0', '-0.0'):
        if new_char == '-':
            return '-'
        elif new_char == '.' and not is_integer:
            return '0.'
        elif new_char.isdigit():
            return new_char
        else:
            return None

    # Build potential new value
    potential = current_value + new_char

    # For integers, only allow digits and leading minus
    if is_integer:
        if new_char.isdigit():
            return potential
        elif new_char == '-' and current_value == '':
            return '-'
        else:
            return None

    # For floats, validate format
    if new_char.isdigit():
        return potential
    elif new_char == '-' and current_value == '':
        return '-'
    elif new_char == '.' and '.' not in current_value:
        return potential
    else:
        return None


def is_numeric_field(field_name: str) -> Tuple[bool, bool]:
    """
    Check if a field is numeric.

    Returns:
        (is_numeric, is_integer) tuple
    """
    if field_name in ('tier', 'year'):
        return (True, True)
    elif field_name.endswith('_value') or field_name.endswith('_amount'):
        return (True, False)
    return (False, False)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))
