import inspect
from typing import get_type_hints, Any, Dict, Literal, get_origin, get_args, Union

def extract_description(docstring: str) -> str:
    """Extract the first paragraph of the docstring as the description."""
    if not docstring:
        return ""
    return docstring.strip().split("\n\n")[0]

def python_type_to_json_type(py_type: Any) -> Dict[str, Any]:
    """Convert a Python type to a JSON schema type definition."""
    # Handle Optional[T] which is Union[T, None]
    origin = get_origin(py_type)
    if origin is Union:
        args = get_args(py_type)
        # Filter out None to get the underlying type
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            # Recursively process the underlying type
            return python_type_to_json_type(non_none_args[0])

    if py_type == str:
        return {"type": "string"}
    elif py_type == int:
        return {"type": "integer"}
    elif py_type == float:
        return {"type": "number"}
    elif py_type == bool:
        return {"type": "boolean"}
    elif py_type == list or origin == list:
        args = get_args(py_type)
        item_type = args[0] if args else Any
        return {
            "type": "array",
            "items": python_type_to_json_type(item_type)
        }
    elif py_type == dict or origin == dict:
        return {"type": "object"}
    elif origin == Literal:
        return {
            "type": "string",
            "enum": list(get_args(py_type))
        }
    else:
        return {"type": "string"} # Default fallback

def generate_schema(func: Any) -> Dict[str, Any]:
    """
    Generate JSON schema from Python function type hints.
    """
    func_name = func.__name__
    func_doc = inspect.getdoc(func) or ""
    type_hints = get_type_hints(func)
    
    # Remove return type from hints if present
    if 'return' in type_hints:
        del type_hints['return']
        
    properties = {}
    required = []
    
    sig = inspect.signature(func)
    
    for param_name, param_type in type_hints.items():
        prop_schema = python_type_to_json_type(param_type)
        
        # Add description from docstring if possible (simplified here)
        # In a real implementation, we'd parse the docstring args
        
        properties[param_name] = prop_schema
        
        # Check if required (no default value)
        param = sig.parameters.get(param_name)
        if param and param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "name": func_name,
        "description": extract_description(func_doc),
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }
