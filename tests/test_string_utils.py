from src.string_utils import slugify


def test_empty_string():
    assert slugify("") == ""


def test_punctuation_only():
    assert slugify("!!!???...") == ""


def test_basic_lowercase():
    assert slugify("Hello World") == "hello-world"


def test_trim_whitespace():
    assert slugify("  hello  ") == "hello"


def test_collapse_internal_spaces():
    assert slugify("a   b") == "a-b"


def test_underscore_to_hyphen():
    assert slugify("foo_bar") == "foo-bar"


def test_underscore_run():
    assert slugify("foo___bar") == "foo-bar"


def test_hyphen_run():
    assert slugify("foo---bar") == "foo-bar"


def test_mixed_separators():
    assert slugify("foo _-_ bar") == "foo-bar"


def test_strip_leading_trailing():
    assert slugify("--hello--") == "hello"


def test_remove_punctuation():
    assert slugify("Hello, World!") == "hello-world"


def test_keep_digits():
    assert slugify("version 1.2.3") == "version-123"


def test_digits_only():
    assert slugify("12345") == "12345"


def test_unicode_letters_preserved():
    assert slugify("Café Münchën") == "café-münchën"


def test_unicode_with_punctuation():
    assert slugify("Привет, мир!") == "привет-мир"
