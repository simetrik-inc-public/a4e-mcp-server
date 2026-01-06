"""
Schema Generator for A4E Agent Tools

Generates JSON schemas in the format expected by the A4E main application:

{
    "tool_name": {
        "function": {
            "name": "tool_name",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        },
        "returns": {
            "type": "object",
            "properties": {...}
        }
    }
}
"""
import inspect
import re
from typing import get_type_hints, Any, Dict, Literal, get_origin, get_args, Union, List


def extract_description(docstring: str) -> str:
    """Extract the first paragraph of the docstring as the description."""
    if not docstring:
        return ""
    return docstring.strip().split("\n\n")[0].strip()


def extract_param_descriptions(docstring: str) -> Dict[str, str]:
    """
    Extract parameter descriptions from docstring Args section.
    
    Handles both formats:
    - Standard: param_name: description
    - Params dict: - param_name: description (for params: Dict pattern)
    """
    descriptions = {}
    if not docstring:
        return descriptions
    
    # Find Args section
    args_match = re.search(r'Args:\s*\n(.*?)(?:\n\s*\n|\n\s*Returns:|\Z)', docstring, re.DOTALL)
    if not args_match:
        return descriptions
    
    args_text = args_match.group(1)
    
    # Pattern for "- param_name: description" (params dict style)
    for match in re.finditer(r'-\s*(\w+):\s*([^\n]+)', args_text):
        param_name = match.group(1).strip()
        description = match.group(2).strip()
        # Remove "(optional)" suffix if present
        description = re.sub(r'\s*\(optional\)\s*$', '', description)
        descriptions[param_name] = description
    
    # Pattern for "param_name: description" (traditional style)
    for match in re.finditer(r'^\s+(\w+):\s*([^\n]+)', args_text, re.MULTILINE):
        param_name = match.group(1).strip()
        if param_name not in descriptions:  # Don't override params dict style
            description = match.group(2).strip()
            descriptions[param_name] = description
    
    return descriptions


def extract_return_properties(docstring: str) -> Dict[str, Any]:
    """Extract return properties from docstring Returns section."""
    properties = {}
    if not docstring:
        return properties
    
    # Find Returns section
    returns_match = re.search(r'Returns:\s*\n(.*?)(?:\n\s*\n|\Z)', docstring, re.DOTALL)
    if not returns_match:
        return properties
    
    returns_text = returns_match.group(1)
    
    # Pattern for "- property: description" or "property: description"
    for match in re.finditer(r'-?\s*(\w+):\s*([^\n]+)', returns_text):
        prop_name = match.group(1).strip()
        description = match.group(2).strip()
        # Try to infer type from description
        json_type = "string"
        if "number" in description.lower() or "count" in description.lower():
            json_type = "number"
        elif "boolean" in description.lower() or "true/false" in description.lower():
            json_type = "boolean"
        elif "array" in description.lower() or "list" in description.lower():
            json_type = "array"
        elif "object" in description.lower() or "dict" in description.lower():
            json_type = "object"
        
        properties[prop_name] = {"type": json_type, "description": description}
    
    return properties


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
        return {"type": "string"}  # Default fallback


def generate_schema(func: Any) -> Dict[str, Any]:
    """
    Generate JSON schema from Python function for A4E main application.
    
    Handles both signature styles:
    1. params: Dict[str, Any] pattern (preferred for A4E)
    2. Individual parameters pattern (legacy)
    
    Returns schema in dictionary format expected by the backend:
    {
        "function": {
            "name": "tool_name",
            "description": "...",
            "parameters": {...}
        },
        "returns": {...}
    }
    """
    func_name = func.__name__
    func_doc = inspect.getdoc(func) or ""
    type_hints = get_type_hints(func)
    
    # Extract descriptions from docstring
    param_descriptions = extract_param_descriptions(func_doc)
    return_properties = extract_return_properties(func_doc)
    
    # Check if function uses params: Dict pattern
    sig = inspect.signature(func)
    params_list = list(sig.parameters.keys())
    uses_params_dict = len(params_list) == 1 and params_list[0] == "params"
    
    properties = {}
    required = []
    
    if uses_params_dict:
        # Extract parameter info from docstring for params: Dict pattern
        for param_name, description in param_descriptions.items():
            # Try to infer type from description
            json_type = "string"
            desc_lower = description.lower()
            if "number" in desc_lower or "integer" in desc_lower:
                json_type = "integer" if "integer" in desc_lower else "number"
            elif "boolean" in desc_lower or "true/false" in desc_lower:
                json_type = "boolean"
            elif "array" in desc_lower or "list" in desc_lower:
                json_type = "array"
            elif "object" in desc_lower or "dict" in desc_lower:
                json_type = "object"
            
            properties[param_name] = {
                "type": json_type,
                "description": description
            }
            
            # Parameters without "(optional)" in docstring are required
            if "(optional)" not in description.lower():
                required.append(param_name)
    else:
        # Remove return type from hints if present
        hints_copy = type_hints.copy()
        if 'return' in hints_copy:
            del hints_copy['return']
        
        for param_name, param_type in hints_copy.items():
            prop_schema = python_type_to_json_type(param_type)
            
            # Add description from docstring if available
            if param_name in param_descriptions:
                prop_schema["description"] = param_descriptions[param_name]
            
            properties[param_name] = prop_schema
            
            # Check if required (no default value)
            param = sig.parameters.get(param_name)
            if param and param.default == inspect.Parameter.empty:
                required.append(param_name)
    
    # Build the schema in A4E expected format
    schema = {
        "function": {
            "name": func_name,
            "description": extract_description(func_doc),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        },
        "returns": {
            "type": "object",
            "properties": return_properties if return_properties else {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        }
    }
    
    return schema


def generate_schemas_dict(schemas_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert a list of schemas to dictionary format with tool names as keys.
    
    This is the format expected by the A4E main application's
    get_tools_schemas_filtered function.
    """
    result = {}
    for schema in schemas_list:
        tool_name = schema.get("function", {}).get("name", "unknown")
        result[tool_name] = schema
    return result
