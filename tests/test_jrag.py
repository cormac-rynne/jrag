import copy

import pytest

import jrag

# --- Test Data ---

SIMPLE_DICT = {"a": 1, "b": "hello"}
NESTED_DICT = {
    "name": "Project X",
    "version": "1.2.0",
    "author": {"name": "Jane Doe", "email": "jane.doe@example.com"},
    "features": ["core", "api", "ui"],
    "enabled": True,
    "settings": None,
}
LIST_OF_DICTS = [
    {"id": 1, "value": "apple", "tags": ["fruit", "red"]},
    {"id": 2, "value": "banana", "tags": ["fruit", "yellow"]},
]
MIXED_LIST = ["item1", 100, True, None, {"key": "val"}, ["nested_list"]]


# --- Tests for jrag._format_value (Internal Helper) ---


def test_format_value_string():
    assert jrag._format_value("hello") == "hello"


def test_format_value_int():
    assert jrag._format_value(123) == "123"


def test_format_value_float():
    assert jrag._format_value(1.23) == "1.23"


def test_format_value_bool():
    assert jrag._format_value(True) == "True"
    assert jrag._format_value(False) == "False"


def test_format_value_none():
    assert jrag._format_value(None) == "null"


def test_format_value_simple_list():
    assert jrag._format_value(["a", 1, None]) == "[a, 1, null]"


def test_format_value_simple_dict():
    # Note: Dict order is guaranteed in Python 3.7+
    assert jrag._format_value({"a": 1, "b": "x"}) == "(a: 1, b: x)"


def test_format_value_nested_list():
    assert jrag._format_value(["a", [1, 2], "b"]) == "[a, [1, 2], b]"


def test_format_value_nested_dict():
    assert jrag._format_value({"a": 1, "b": {"c": 2, "d": "y"}}) == "(a: 1, b: (c: 2, d: y))"


def test_format_value_list_with_dict():
    assert jrag._format_value(["a", {"k": "v"}]) == "[a, (k: v)]"


def test_format_value_dict_with_list():
    assert jrag._format_value({"a": [1, 2]}) == "(a: [1, 2])"


# --- Tests for jrag._json_to_rag_string (Default Mode) ---


def test_default_simple_dict():
    expected = "a: 1 | b: hello"
    assert jrag._json_to_rag_string(SIMPLE_DICT) == expected


def test_default_nested_dict():
    expected = (
        "name: Project X | version: 1.2.0 | author: (name: Jane Doe, email: jane.doe@example.com) | "
        "features: [core, api, ui] | enabled: True | settings: null"
    )
    assert jrag._json_to_rag_string(NESTED_DICT) == expected


def test_default_empty_dict():
    assert jrag._json_to_rag_string({}) == ""


def test_default_custom_separator():
    expected = "a: 1 ;; b: hello"
    assert jrag._json_to_rag_string(SIMPLE_DICT, separator=" ;; ") == expected


def test_default_non_dict_list_input(capsys):
    # Test the fallback behavior and informational message
    expected_output = "[item1, 100, True, null, (key: val), [nested_list]]"
    result = jrag._json_to_rag_string(MIXED_LIST)
    assert result == expected_output
    captured = capsys.readouterr()
    assert "Info: _json_to_rag_string called in default mode with non-dictionary input" in captured.out


def test_default_non_dict_scalar_input(capsys):
    expected_output = "just a string"
    result = jrag._json_to_rag_string("just a string")
    assert result == expected_output
    captured = capsys.readouterr()
    assert "Info: _json_to_rag_string called in default mode with non-dictionary input" in captured.out


# --- Tests for jrag._json_to_rag_string (Config Mode) ---

CONFIG_BASIC = {
    "Project": "$.name",
    "Author Name": "$.author.name",
    "First Feature": "$.features[0]",
    "All Features": "$.features[*]",
    "Author Object": "$.author",
    "Missing": "$.settings.nonexistent",  # No match expected
}


def test_config_basic():
    expected = (
        "Project: Project X | Author Name: Jane Doe | First Feature: core | All Features: [core, api, ui] | "
        "Author Object: (name: Jane Doe, email: jane.doe@example.com)"
    )
    assert jrag._json_to_rag_string(NESTED_DICT, config=CONFIG_BASIC) == expected


def test_config_no_matches():
    config = {"Non Existent": "$.foo.bar"}
    assert jrag._json_to_rag_string(NESTED_DICT, config=config) == ""


def test_config_empty_input():
    assert jrag._json_to_rag_string({}, config=CONFIG_BASIC) == ""


def test_config_empty_config():
    assert jrag._json_to_rag_string(NESTED_DICT, config={}) == ""


def test_config_custom_separator():
    config = {"Project": "$.name", "Version": "$.version"}
    expected = "Project: Project X ## Version: 1.2.0"
    assert jrag._json_to_rag_string(NESTED_DICT, config=config, separator=" ## ") == expected


def test_config_invalid_path_syntax(capsys):
    # jsonpath-ng handles syntax errors during parse
    # Our code catches the exception and prints a warning
    config = {"Invalid Path": "$..[invalid?syntax"}
    result = jrag._json_to_rag_string(NESTED_DICT, config=config)
    assert result == "Invalid Path: Error Processing Path"
    captured = capsys.readouterr()
    assert "Warning: Error processing path" in captured.out
    assert "$..[invalid?syntax" in captured.out  # Check if path mentioned in warning


# --- Tests for jrag.to_text (Wrapper) ---


def test_to_text_calls_correctly():
    # Implicitly tested by jrag._json_to_rag_string tests, but can add explicit one
    expected = (
        "name: Project X | version: 1.2.0 | author: (name: Jane Doe, email: jane.doe@example.com) | "
        "features: [core, api, ui] | enabled: True | settings: null"
    )
    assert jrag.to_text(NESTED_DICT) == expected
    config = {"Project": "$.name"}
    expected_config = "Project: Project X"
    assert jrag.to_text(NESTED_DICT, config=config) == expected_config


def test_to_text_invalid_separator_type():
    with pytest.raises(TypeError, match="separator must be a string"):
        jrag.to_text(SIMPLE_DICT, separator=123)


def test_to_text_invalid_config_type():
    with pytest.raises(TypeError, match="config must be None or a dictionary"):
        jrag.to_text(SIMPLE_DICT, config=["invalid"])


# --- Tests for jrag.add_text (Wrapper) ---


def test_add_text_basic():
    data = copy.deepcopy(SIMPLE_DICT)  # Use copy to avoid modifying original test data
    expected_text = "a: 1 | b: hello"
    result = jrag.add_text(data)

    assert "jrag_text" in result
    assert result["jrag_text"] == expected_text
    assert result is data  # Should modify in place and return same object
    assert data["jrag_text"] == expected_text  # Verify original dict was modified


def test_add_text_custom_key():
    data = copy.deepcopy(NESTED_DICT)
    key = "my_text_field"
    expected_text = (
        "name: Project X | version: 1.2.0 | author: (name: Jane Doe, email: jane.doe@example.com) | "
        "features: [core, api, ui] | enabled: True | settings: null"
    )
    result = jrag.add_text(data, output_key=key)

    assert key in result
    assert result[key] == expected_text
    assert "jrag_text" not in result  # Default key shouldn't be there
    assert data[key] == expected_text  # Verify original dict was modified


def test_add_text_with_config():
    data = copy.deepcopy(NESTED_DICT)
    config = {"Project": "$.name"}
    expected_text = "Project: Project X"
    result = jrag.add_text(data, config=config)

    assert "jrag_text" in result
    assert result["jrag_text"] == expected_text


def test_add_text_overwrites_existing_key():
    key = "jrag_text"
    data = {"a": 1, key: "old_value"}
    expected_text = "a: 1 | jrag_text: old_value"  # New text generated
    result = jrag.add_text(data, output_key=key)  # Explicitly use the key

    assert result[key] == expected_text  # Should be overwritten


def test_add_text_invalid_input_type():
    with pytest.raises(TypeError, match="Input json_dict must be a dictionary"):
        jrag.add_text(["not", "a", "dict"])


def test_add_text_invalid_output_key_type():
    with pytest.raises(TypeError, match="output_key must be a non-empty string"):
        jrag.add_text(SIMPLE_DICT, output_key=123)


def test_add_text_invalid_output_key_empty():
    with pytest.raises(TypeError, match="output_key must be a non-empty string"):
        jrag.add_text(SIMPLE_DICT, output_key="")


# --- Tests for jrag.tag_list (Wrapper) ---
# Replace jrag.tag_list with your chosen name if different (e.g., enrich_list)


def test_tag_list_basic():
    data_list = copy.deepcopy(LIST_OF_DICTS)
    expected_texts = ["id: 1 | value: apple | tags: [fruit, red]", "id: 2 | value: banana | tags: [fruit, yellow]"]
    result_list = jrag.tag_list(data_list)

    assert len(result_list) == 2
    assert isinstance(result_list, list)
    for i, item in enumerate(result_list):
        assert isinstance(item, dict)
        assert "jrag_text" in item
        assert item["jrag_text"] == expected_texts[i]
    # Check if original list items were modified (they should be)
    assert data_list[0]["jrag_text"] == expected_texts[0]
    assert data_list[1]["jrag_text"] == expected_texts[1]


def test_tag_list_custom_key():
    data_list = copy.deepcopy(LIST_OF_DICTS)
    key = "generated_str"
    expected_texts = ["id: 1 | value: apple | tags: [fruit, red]", "id: 2 | value: banana | tags: [fruit, yellow]"]
    result_list = jrag.tag_list(data_list, output_key=key)

    assert len(result_list) == 2
    for i, item in enumerate(result_list):
        assert key in item
        assert item[key] == expected_texts[i]
        assert "jrag_text" not in item  # Default key shouldn't be there


def test_tag_list_with_config():
    data_list = copy.deepcopy(LIST_OF_DICTS)
    config = {"ItemID": "$.id", "FirstTag": "$.tags[0]"}
    expected_texts = ["ItemID: 1 | FirstTag: fruit", "ItemID: 2 | FirstTag: fruit"]
    result_list = jrag.tag_list(data_list, config=config)

    assert len(result_list) == 2
    for i, item in enumerate(result_list):
        assert "jrag_text" in item
        assert item["jrag_text"] == expected_texts[i]


def test_tag_list_empty_list():
    result_list = jrag.tag_list([])
    assert result_list == []


def test_tag_list_invalid_input_type():
    with pytest.raises(TypeError, match="Input json_list must be a list"):
        jrag.tag_list({"not": "a list"})


def test_tag_list_invalid_item_type():
    data_list = [{"id": 1}, "not a dict", {"id": 3}]
    with pytest.raises(TypeError, match="Item at index 1 in json_list is not a dictionary"):
        jrag.tag_list(data_list)


def test_tag_list_invalid_output_key():
    with pytest.raises(TypeError, match="output_key must be a non-empty string"):
        jrag.tag_list(LIST_OF_DICTS, output_key=None)


# --- Test jrag._json_to_rag_string Type Errors ---


def test_core_invalid_separator():
    with pytest.raises(TypeError, match="separator must be a string"):
        jrag._json_to_rag_string(SIMPLE_DICT, separator=None)


def test_core_invalid_config_type():
    with pytest.raises(TypeError, match="config must be None or a dictionary"):
        jrag._json_to_rag_string(SIMPLE_DICT, config=123)


def test_core_invalid_data_type_with_config():
    with pytest.raises(TypeError, match="json_data must be a dictionary or list when using a config"):
        jrag._json_to_rag_string(123, config={"key": "$.a"})
