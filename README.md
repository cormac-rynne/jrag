<div align="center">

<img src="./images/jrag_logo.png" width="300" height="300" alt="jrag logo"><br>
<h3><strong>jRAG</strong></h3>
A lightweight Python library to flatten and extract text from JSON-like data, suitable for Retrieval-Augmented Generation (RAG) pipelines.
</p>

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1KAYyCeIsiu9Cl-e8NJNmLCvcpVezvAMv?usp=sharing)
[![PyPI version](https://img.shields.io/pypi/v/jrag.svg)](https://pypi.org/project/jrag/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://choosealicense.com/licenses/mit/)
[![Python version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/release/python-380/)
<br>
[![Downloads](https://static.pepy.tech/badge/jrag)](https://pepy.tech/project/jrag)
[![Downloads](https://static.pepy.tech/badge/jrag/month)](https://pepy.tech/project/jrag)
<br>
### [Try in Colab](https://colab.research.google.com/drive/1KAYyCeIsiu9Cl-e8NJNmLCvcpVezvAMv?usp=sharing)
</div>



## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [`to_text`](#to_text)
  - [`add_text`](#add_text)
  - [`tag_list`](#tag_list)
- [Configuration Example](#using-configuration)
- [Notes and Limitations](#notes-and-limitations)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

`jrag` is a Python library that takes a dictionary or list (representing JSON data) and converts it to a text string. This is particularly useful for preparing data to be ingested by large language models in Retrieval-Augmented Generation (RAG) workflows or other text-based systems.

**Why `jrag`?**
- Offers optional fine-grained control using `jsonpath-ng` expressions.
- Simplifies JSON (or JSON-like) data into a single string.
- Preserves nested structures in a human-readable format.



## Features

- **Config-Driven Extraction**
  Allows you to define exactly which parts of your JSON-like data to extract and how to label them, via `jsonpath-ng` expressions.

- **Default Flattening**
  Recursively flattens dictionaries and lists into a readable string, handling nested objects and arrays in a simple bracket/parentheses format.

- **Easy Injection Back into Data**
  The converted text can be inserted right back into the original dictionary, enabling a "tagging" workflow.

```python
# Example usage overview (also shown in detail below)
import jrag

data = {"name": "Example", "items": [1, {"a": True}]}
text1 = jrag.to_text(data)
# text1 -> 'name: Example | items: [1, (a: True)]'

```

## Installation
```bash
pip install jrag
```

## Quick Start

```python
import jrag

# Sample data
data = {
    "name": "Example Project",
    "version": "1.0",
    "components": [
        {"id": "comp1", "status": "active"},
        {"id": "comp2", "status": "inactive", "details": {"priority": 5}}
    ],
    "metadata": None
}

# 1. Default Flattening
# Converts the entire dictionary structure recursively
text_default = jrag.to_text(data)
print("Default Flattening:")
print(text_default)
# Expected Output: "name: Example Project | version: 1.0 | components: [(id: comp1, status: active), (id: comp2, status: inactive, details: (priority: 5))] | metadata: null"

# 2. Config-based Extraction
# Extracts specific fields using JSONPath expressions
config = {
    "Project Name": "$.name",
    "Active Component IDs": "$.components[?(@.status == 'active')].id",
    "Second Component Priority": "$.components[1].details.priority"
}
text_config = jrag.to_text(data, config=config)
print("\nConfig-based Extraction:")
print(text_config)
# Expected Output: "Project Name: Example Project | Active Component IDs: [comp1] | Second Component Priority: 5"

# 3. Add text back to the dictionary
data_with_text = jrag.add_text(data.copy(), output_key="rag_string") # Use copy to preserve original
print("\nDictionary with added text:")
print(data_with_text['rag_string'])
# Expected Output: name: Example Project | version: 1.0 | components: [(id: comp1, status: active), (id: comp2, status: inactive, details: (priority: 5))] | metadata: null

# 4. Process a list of dictionaries
list_data = [
    {"id": 1, "val": "a"},
    {"id": 2, "val": "b"}
]
tagged_list = jrag.tag_list(list_data, output_key="text_repr")
print("\nTagged List:")
print(tagged_list)
# Expected Output: [{'id': 1, 'val': 'a', 'text_repr': 'id: 1 | val: a'}, {'id': 2, 'val': 'b', 'text_repr': 'id: 2 | val: b'}]
```

## Usage

### to_text
#### `jrag.to_text(data, config=None, separator=' | ')`

This is the core function for converting Python objects (dictionaries or lists) into a flattened string.

**Parameters:**

* `json_data (Union[Dict, List, Any])`: The Python dictionary, list, or scalar value to convert. While any type can be passed in default mode, config mode requires a dictionary or list. Default mode works best with dictionaries.
* `config (Optional[Dict[str, str]])`: An optional dictionary mapping output labels (strings) to jsonpath-ng expressions (strings). If None (default), the function uses default recursive flattening.
* `separator (str)`: The string used to join key-value pairs or extracted values in the output string. Defaults to " | ".

**Returns**:
* `str`: The flattened string representation of the input data.

**Raises**:
* `TypeError`: If the input data is not a dictionary or list when using config mode.

### add_text
#### `jrag.add_text(data, config=None, separator=' | ', output_key='jrag_text')`

Converts a dictionary to its flattened string representation using `to_text` and adds this string back into the dictionary under a specified key. This modifies the original dictionary in place.

**Parameters:**

* `json_data (Union[Dict, List, Any])`: The Python dictionary, list, or scalar value to convert. While any type can be passed in default mode, config mode requires a dictionary or list. Default mode works best with dictionaries.
* `config (Optional[Dict[str, str]])`: An optional dictionary mapping output labels (strings) to jsonpath-ng expressions (strings). If None (default), the function uses default recursive flattening.
* `separator (str)`: The string used to join key-value pairs or extracted values in the output string. Defaults to " | ".
* `output_key (str)`: The key under which the flattened string will be stored in the original dictionary. Defaults to 'jrag_text'.

**Returns**:
* `Dict[str, Any]`: The input dictionary, now modified to include the `output_key` with the generated text.

**Raises**:
* `TypeError`: If the input data is not a dictionary or list when using config mode.

### tag_list
#### `jrag.tag_list(data, config=None, separator=' | ', output_key='jrag_text')`

Converts a dictionary to its flattened string representation using `to_text` and adds this string back into the dictionary under a specified key. This modifies the original dictionary in place.

**Parameters:**

* `json_data (Union[Dict, List, Any])`: The Python dictionary, list, or scalar value to convert. While any type can be passed in default mode, config mode requires a dictionary or list. Default mode works best with dictionaries.
* `config (Optional[Dict[str, str]])`: An optional dictionary mapping output labels (strings) to jsonpath-ng expressions (strings). If None (default), the function uses default recursive flattening.
* `separator (str)`: The string used to join key-value pairs or extracted values in the output string. Defaults to " | ".
* `output_key (str)`: The key under which the flattened string will be stored in the original dictionary. Defaults to 'jrag_text'.

**Returns**:
* `List[Dict[str, Any]]`:  The input list, where each dictionary element has been modified to include the `output_key` with its generated text.

**Raises**:
* `TypeError`: If the input data is not a dictionary or list when using config mode.

## Using Configuration

When using the config parameter in `to_text`, `add_text`, or `tag_list`, the values within the config dictionary must be strings containing valid JSONPath expressions. This library uses the [jsonpath-ng](https://pypi.org/project/jsonpath-ng/) implementation to parse and execute these expressions against the input json_data.

This allows for highly specific and flexible extraction of data points from your JSON-like structures. You can select specific fields, elements within arrays, filter based on values, and more. The keys in the config dictionary serve as the labels for the extracted data in the final output string.

For detailed information on the syntax and capabilities of the JSONPath expressions supported, please refer to the jsonpath-ng project documentation:


### Key points about configuration:

* Each key-value pair in config must have string keys (labels) and string values (JSONPath expressions).
* If a JSONPath expression matches multiple values, they are formatted as a list [val1, val2] in the output string.
* If a JSONPath expression doesn't find any match, that label is simply omitted from the output.
* If an error occurs while processing a specific path (e.g., invalid syntax), a warning is printed, and placeholder text (Label: Error Processing Path) is included in the output for that label.

## Notes and Limitations
* Dependency: The configuration feature (config parameter) requires the jsonpath-ng library to be installed. The default flattening mode does not have this external dependency.
* Default Formatting: The default recursive flattening uses a specific format:
  * Dictionaries are enclosed in parentheses (...).
  * Lists are enclosed in square brackets [...].
  * None values are represented as the string "null".
  * Other basic types are converted using str().
* In-place Modification: The add_text and tag_list functions modify the input dictionaries directly. If you need to preserve the original data, pass copies (e.g., data.copy() or [d.copy() for d in list_data]).
* Error Handling: Basic type checks are performed for arguments. Errors during JSONPath processing in config mode are caught per-path, logged as warnings, and produce placeholder text, allowing the overall conversion to continue. * More complex errors (like extreme recursion depth on highly nested data) might still occur.
* Complexity: Very deeply nested structures might lead to long output strings or hit recursion limits in Python during default flattening. Config-based extraction can mitigate this by targeting specific fields.

## Contributing
Contributions are welcome! Please feel free to:

* Report bugs or suggest features by opening an issue on the repository (if applicable).
* Submit pull requests with improvements or fixes.

## License
[MIT License](https://choosealicense.com/licenses/mit/)
