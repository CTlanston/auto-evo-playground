from src.string_utils import dedupe_words, slugify


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


def test_dedupe_empty_string():
    assert dedupe_words("") == ""


def test_dedupe_whitespace_only():
    assert dedupe_words("   \t\n  ") == ""


def test_dedupe_single_word():
    assert dedupe_words("hello") == "hello"


def test_dedupe_no_duplicates():
    assert dedupe_words("the quick brown fox") == "the quick brown fox"


def test_dedupe_consecutive_same_case():
    assert dedupe_words("hello hello world") == "hello world"


def test_dedupe_case_insensitive():
    assert dedupe_words("Hello hello world") == "Hello world"


def test_dedupe_three_in_a_row():
    assert dedupe_words("foo Foo FOO bar") == "foo bar"


def test_dedupe_nonconsecutive_kept():
    assert dedupe_words("cat dog cat") == "cat dog cat"


def test_dedupe_collapses_whitespace():
    assert dedupe_words("  hello    world  ") == "hello world"


def test_dedupe_collapses_tabs_and_newlines():
    assert dedupe_words("hello\t\thello\nworld") == "hello world"


def test_dedupe_punctuation_part_of_word():
    assert dedupe_words("hello, hello") == "hello, hello"


def test_dedupe_punctuation_with_match():
    assert dedupe_words("Wow! wow! done") == "Wow! done"


def test_dedupe_unicode_casefold():
    assert dedupe_words("Straße strasse") == "Straße"
