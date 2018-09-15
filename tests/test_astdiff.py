import pytest
import ast

from astdiff import __version__
from astdiff.astdiff import compare_ast, assert_equal


def test_version():
    assert __version__ == '0.1.0'


def test_assert_equal_is_equal():
    assert assert_equal(1, 1, 0, 0) is None
    assert assert_equal("hello", "hello", 0, 0) is None


def test_assert_equal_raises():
    with pytest.raises(AssertionError):
        assert_equal(0, 1, 0, 0)
    with pytest.raises(AssertionError):
        assert_equal("foo", "bar", 0, 0)


def test_compare_equal_strings():
    assert compare_ast("foo", "foo", 0, 0) is None


def test_compare_equal_lists():
    assert compare_ast([], [], 0, 0) is None
    assert compare_ast(["foo", "bar"], ["foo", "bar"], 0, 0) is None


def test_compare_different_length_lists():
    with pytest.raises(AssertionError):
        assert compare_ast(["foo"], ["spam", "eggs"], 0, 0)


def test_compare_equal_values():
    node = ast.parse("x = 0")
    assert compare_ast(node, node, 0, 0) is None


def test_compare_different_values():
    node1 = ast.parse("x = 1")
    node2 = ast.parse("y = 1")
    with pytest.raises(AssertionError):
        compare_ast(node1, node2, 0, 0)


def test_compare_formatting(ast_a1, ast_a2):
    assert compare_ast(ast_a1, ast_a2, 0, 0) is None


def test_compare_different_formatting(ast_a1, ast_b1):
    with pytest.raises(AssertionError):
        compare_ast(ast_a1, ast_b1, 0, 0)


def test_compare_sets(ast_set1, ast_set2):
    with pytest.raises(AssertionError):
        compare_ast(ast_set1, ast_set2, 0, 0)


def test_compare_different_nodes():
    node1 = ast.parse("x = 1")
    node2 = ast.parse("import foo")
    with pytest.raises(AssertionError):
        compare_ast(node1, node2, 0, 0)
