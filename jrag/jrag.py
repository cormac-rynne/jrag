"""
Core conversion logic for the 'jrag' library.

This module provides functions to flatten complex Python objects (dictionaries,
lists, scalars, representing JSON-like data) into single-string representations.
This is primarily useful for preparing structured data for ingestion into text-based
systems like Retrieval-Augmented Generation (RAG) models.

Features:
- Default recursive flattening of dictionaries and lists into a readable format.
- Configurable data extraction using jsonpath-ng expressions for precise control.
- Helper functions to inject the generated text back into dictionaries or lists
  of dictionaries.

Main Functions (exposed via the 'jrag' package):
- `to_text`: The primary function to convert data to a string.
- `add_text`: Converts a dictionary to text and adds it back under a specific key.
- `tag_list`: Processes a list of dictionaries, applying `add_text` to each.

Example Usage:
    import jrag

    data = {"name": "Example", "items": [1, {"a": True}]}
    config = {"Name": "$.name", "First Item": "$.items[0]"}

    # Default flattening
    text1 = jrag.to_text(data)
    # >>> 'name: Example | items: [1, (a: True)]'

    # Config-based extraction
    text2 = jrag.to_text(data, config=config)
    # >>> 'Name: Example | First Item: 1'

Assumes 'jsonpath-ng' library is installed as a dependency.
"""

from typing import Any, Dict, List, Optional, Union

from jsonpath_ng.ext import parse  # Use the extended parser for more features


def _format_value(value: Any) -> str:
    """
    Recursively formats a Python value into a specific string representation.

    Handles basic types, None, lists, and dictionaries with specific syntax
    (brackets for lists, parentheses for dictionaries).

    Args:
        value: The Python value (scalar, list, or dict) to format.

    Returns:
        The formatted string representation of the value.
    """
    if isinstance(value, dict):
        items = [f"{k}: {_format_value(v)}" for k, v in value.items()]
        return f"({', '.join(items)})"
    elif isinstance(value, list):
        items = [_format_value(item) for item in value]
        return f"[{', '.join(items)}]"
    elif isinstance(value, str):
        return value
    elif value is None:
        return "null"
    else:
        return str(value)


def _flatten_json_default(data: Any, separator: str = " | ") -> str:
    """
    Flattens a Python object using default formatting (no config).

    If 'data' is a dictionary, formats it as 'key1: val1 | key2: val2 ...',
    using _format_value for nested structures. If 'data' is not a dictionary,
    it formats the data directly using _format_value.

    Args:
        data: The Python object (ideally dict) representing JSON data.
        separator: The string used to separate key-value pairs (if data is dict).

    Returns:
        The flattened string representation using default formatting.
    """
    if not isinstance(data, dict):
        return _format_value(data)

    parts = []
    for key, value in data.items():
        formatted_value = _format_value(value)
        parts.append(f"{key}: {formatted_value}")

    return separator.join(parts)


def _flatten_json_config(data: Union[Dict[str, Any], List[Any]], config: Dict[str, str], separator: str = " | ") -> str:
    """
    Flattens a Python object based on a jsonpath_ng configuration dictionary.

    Extracts data using JSONPath expressions from the config, formats the
    results using _format_value, and joins them with the separator. Assumes
    jsonpath-ng is installed.

    Args:
        data: The Python dictionary or list representing JSON data.
        config: Dictionary mapping output labels (str) to jsonpath-ng
                expressions (str).
        separator: The string used to separate extracted parts.

    Returns:
        The flattened string representation based on the config.

    Raises:
        Exception: Can raise exceptions from jsonpath_ng parsing/finding if
                   expressions are invalid beyond the basic checks, or other
                   unexpected errors occur during processing. Standard errors
                   like RecursionError are also possible for deeply nested data.
    """
    parts = []
    for label, path_expr_str in config.items():
        try:
            # Basic validation of config item format (can be enhanced)
            if not isinstance(label, str) or not isinstance(path_expr_str, str):
                print(
                    f"Warning: Skipping invalid config item pair: ({label!r}, {path_expr_str!r}). "
                    "Both must be strings."
                )
                continue

            # Use 'parse' directly (imported at module level)
            path_expr = parse(path_expr_str)
            matches = path_expr.find(data)

            if not matches:
                continue  # Skip if no match

            found_values = [match.value for match in matches]

            if len(found_values) == 1:
                formatted_value = _format_value(found_values[0])
                parts.append(f"{label}: {formatted_value}")
            else:
                formatted_list = [_format_value(val) for val in found_values]
                parts.append(f"{label}: [{', '.join(formatted_list)}]")

        except Exception as e:
            # Catch potential errors during jsonpath processing for robustness
            print(f"Warning: Error processing path '{path_expr_str}' for label '{label}': {e}")
            parts.append(f"{label}: Error Processing Path")

    return separator.join(parts)


def _json_to_rag_string(
    json_data: Union[Dict[str, Any], List[Any], Any], config: Optional[Dict[str, str]] = None, separator: str = " | "
) -> str:
    """
    Converts a Python object (from JSON) into a flattened string suitable for RAG.

    Uses default recursive flattening if 'config' is None. Otherwise, uses
    jsonpath-ng expressions from the 'config' dictionary for extraction.
    Assumes jsonpath-ng is installed if config is used.

    Args:
        json_data: The Python object representing the JSON data. Can be a
                   dictionary, list, or scalar value. Default mode works
                   best with dictionaries, config mode requires dict or list.
        config: Optional dictionary mapping desired output labels (str) to
                jsonpath-ng expressions (str). If None, uses default flattening.
        separator: The string used to separate key-value pairs or configured
                   extractions. Must be a string.

    Returns:
        The flattened string representation.

    Raises:
        TypeError: If 'config' is provided but 'json_data' is not a dict/list.
                   If 'config' is not None or a dict.
                   If 'separator' is not a string.
                   If items within 'config' are not str:str pairs (logged as warning).
        # No longer raises ImportError for jsonpath-ng specifically.
        # Other exceptions from jsonpath-ng or recursion possible.
    """
    # Validate separator type early
    if not isinstance(separator, str):
        raise TypeError("separator must be a string.")

    if config is not None:
        # Validate config type
        if not isinstance(config, dict):
            raise TypeError("config must be None or a dictionary.")

        # Validate json_data type compatibility with config mode
        if not isinstance(json_data, (dict, list)):
            raise TypeError(f"json_data must be a dictionary or list when using a config (got {type(json_data)}).")

        # Delegate directly to config-based function
        # Assumes jsonpath-ng is imported at the top level
        return _flatten_json_config(json_data, config, separator)
    else:
        # --- Default Mode ---
        if not isinstance(json_data, dict):
            print(
                f"Info: _json_to_rag_string called in default mode with non-dictionary input ({type(json_data)}). "
                "Formatting value directly."
            )
            return _format_value(json_data)
        else:
            return _flatten_json_default(json_data, separator)


def to_text(
    json_data: Union[Dict[str, Any], List[Any]], config: Optional[Dict[str, str]] = None, separator: str = " | "
) -> str:
    """
    Converts a Python dictionary or list (from JSON) into a flattened string.

    This is a direct wrapper around the core json_to_rag_string function.

    Args:
        json_data: The Python dictionary or list to convert.
        config: Optional dictionary mapping labels to jsonpath_ng expressions.
                If None, uses default recursive flattening.
        separator: The string used to separate elements in the output string.

    Returns:
        The flattened string representation.

    Raises:
        TypeError: If input types are invalid (e.g., separator not a string,
                   config is not None or a dict). See json_to_rag_string
                   for more specific input validation details.
        ImportError: If jsonpath-ng is not installed and config is provided.

    Example:
        >>> data = {"name": "Test", "values": [1, 2]}
        >>> to_text(data)
        'name: Test | values: [1, 2]'
        >>> config = {"Item Name": "$.name"}
        >>> to_text(data, config=config)
        'Item Name: Test'
    """
    # Basic type validation for wrapper arguments
    if not isinstance(separator, str):
        raise TypeError("separator must be a string.")
    if config is not None and not isinstance(config, dict):
        raise TypeError("config must be None or a dictionary.")
    if config is not None:
        for key, value in config.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("config dictionary keys and values must be strings.")

    # json_to_rag_string handles core validation of json_data based on config presence
    return _json_to_rag_string(json_data, config=config, separator=separator)


def add_text(
    json_dict: Dict[str, Any],
    config: Optional[Dict[str, str]] = None,
    separator: str = " | ",
    output_key: str = "jrag_text",
) -> Dict[str, Any]:
    """
    Converts a dictionary to a flattened string and adds it back to the
    dictionary under the specified key.

    Modifies the input dictionary in place and also returns it.

    Args:
        json_dict: The Python dictionary to process. Must be a dictionary.
        config: Optional dictionary mapping labels to jsonpath_ng expressions
                for the text conversion.
        separator: The string used to separate elements in the generated text.
        output_key: The key under which the generated text will be stored
                    in the dictionary. Defaults to 'jrag_text'.

    Returns:
        The input dictionary, modified to include the generated text.

    Raises:
        TypeError: If json_dict is not a dictionary, or if other arguments
                   have invalid types (see to_text).
        ImportError: If jsonpath-ng is not installed and config is provided.

    Example:
        >>> data = {"name": "Test", "values": [1, 2]}
        >>> result = add_text(data)
        >>> print(result)
        {'name': 'Test', 'values': [1, 2], 'jrag_text': 'name: Test | values: [1, 2]'}
        >>> print(data['jrag_text'])
        name: Test | values: [1, 2]
    """
    if not isinstance(json_dict, dict):
        raise TypeError("Input json_dict must be a dictionary.")
    if not isinstance(output_key, str) or not output_key:
        raise TypeError("output_key must be a non-empty string.")

    # Generate the text using the validated to_text function
    # This re-uses the validation logic within to_text for config/separator
    generated_text = to_text(json_dict, config=config, separator=separator)

    # Add the text to the dictionary (overwrites if key exists)
    json_dict[output_key] = generated_text

    return json_dict


def tag_list(
    json_list: List[Dict[str, Any]],
    config: Optional[Dict[str, str]] = None,
    separator: str = " | ",
    output_key: str = "jrag_text",
) -> List[Dict[str, Any]]:
    """
    Applies the add_text function to each dictionary in a list.

    Modifies the dictionaries within the input list in place and also
    returns the modified list.

    Args:
        json_list: A list where each element is a Python dictionary.
        config: Optional dictionary mapping labels to jsonpath_ng expressions
                for the text conversion (applied to each dictionary).
        separator: The string used to separate elements in the generated text.
        output_key: The key under which the generated text will be stored
                    in each dictionary. Defaults to 'jrag_text'.

    Returns:
        The input list, where each dictionary has been modified to include
        the generated text.

    Raises:
        TypeError: If json_list is not a list, if any item in the list is not
                   a dictionary, or if other arguments have invalid types
                   (see add_text).
        ImportError: If jsonpath-ng is not installed and config is provided.

    Example:
        >>> data_list = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
        >>> result_list = tag_list(data_list)
        >>> print(result_list)
        [{'id': 1, 'val': 'a', 'jrag_text': 'id: 1 | val: a'}, {'id': 2, 'val': 'b', 'jrag_text': 'id: 2 | val: b'}] # noqa E501
    """
    if not isinstance(json_list, list):
        raise TypeError("Input json_list must be a list.")
    if not isinstance(output_key, str) or not output_key:
        raise TypeError("output_key must be a non-empty string.")

    # Validate config/separator types once before the loop (add_text will also check)
    if config is not None and not isinstance(config, dict):
        raise TypeError("config must be None or a dictionary.")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string.")

    # Process each dictionary in the list
    processed_list = []
    for index, item in enumerate(json_list):
        if not isinstance(item, dict):
            raise TypeError(f"Item at index {index} in json_list is not a dictionary (got {type(item)}).")
        # Call add_text, which handles its own validation and modification
        # We re-use the validated args: config, separator, output_key
        processed_list.append(
            add_text(
                json_dict=item,  # item is validated to be a dict here
                config=config,
                separator=separator,
                output_key=output_key,
            )
        )
        # Note: Since add_text modifies item in-place, the original list is also modified.
        # We return a new list reference here for clarity, matching list comprehension behavior.

    return processed_list  # Or return json_list, as it's modified in-place. Returning result of the loop is cleaner.
