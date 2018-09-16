import ast
from textwrap import dedent

import pytest


@pytest.fixture
def ast_a1():
    code = dedent(
        """
        x = (1, 2, 'foo')
        """
    )
    return ast.parse(code)


@pytest.fixture
def ast_a2():
    code = dedent(
        """
        x = (
            1,
            2, 
            "foo",
        )
        """
    )
    return ast.parse(code)


@pytest.fixture
def ast_b1():
    code = dedent(
        """
        x = tuple([1, 2, 'foo'])
        """
    )
    return ast.parse(code)


@pytest.fixture
def ast_set1():
    code = dedent(
        """
        x = {1, 2}
        """
    )
    return ast.parse(code)


@pytest.fixture
def ast_set2():
    code = dedent(
        """
        x = {2, 1}
        """
    )
    return ast.parse(code)


@pytest.fixture
def ast_line1():
    code = dedent(
        """
        x = {1,
        
        
             3}
        """
    )
    return ast.parse(code)
