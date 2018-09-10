#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from typing import Union, List, Any, Sequence, Optional
import ast
import subprocess
import sys
import os

from six.moves import zip_longest
from six import string_types

import click
import colorful as c


NodeType = Union[ast.AST, List, str]


def compare_ast(left, right, left_lineno, right_lineno):
    # type: (NodeType, NodeType, int, int) -> None
    """Compare two abstract syntax trees.

    Return `None` if they are equal, and raise an exception otherwise.
    """
    assert_equal(type(left), type(right), left_lineno, right_lineno)

    if isinstance(left, ast.AST):
        left_fields = ast.iter_fields(left)
        right_fields = ast.iter_fields(right)
        for left_field, right_field in zip_longest(
            left_fields, right_fields, fillvalue=""
        ):
            left_name, left_values = left_field
            right_name, right_values = right_field
            assert_equal(left_name, right_name, left_lineno, right_lineno)
            compare_ast(
                left_values,
                right_values,
                getattr(left, "lineno", left_lineno),
                getattr(right, "lineno", right_lineno),
            )
    elif isinstance(left, list):
        for left_child, right_child in zip_longest(left, right, fillvalue=""):
            compare_ast(left_child, right_child, left_lineno, right_lineno)
    else:
        assert_equal(left, right, left_lineno, right_lineno)


def assert_equal(left, right, left_lineno, right_lineno):
    # type: (Any, Any, int, int) -> None
    """Compare two objects.

    Return `None` if equal, and raise an exception with the line number
    otherwise.
    """
    assert (
        left == right
    ), "different nodes at lines left:{}, and right:{}\n{} != {}".format(
        left_lineno, right_lineno, left, right
    )


def shell(cmd):
    # type: (str) -> string_types
    return (
        subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        .decode("utf-8")
        .strip()
    )


def get_object(commit, path):
    # type: (Optional[str], str) -> string_types
    """Get a file from git at a given commit.

    If `commit` is None, get the file from the working tree.
    """
    if commit is None:
        top_level = shell("git rev-parse --show-toplevel")
        file_path = os.path.join(top_level, path)
        with open(file_path) as f:
            return f.read()
    return shell("git show {}:{}".format(commit, path))


def collect_paths(from_commit, to_commit):
    # type: (str, Optional[str]) -> List[string_types]
    """Get the list of changed files between two commits.

    If `to_commit` is None, diff agains the current working tree.
    """
    cmd = "git diff --name-only {}".format(from_commit)

    if to_commit:
        cmd += " {}".format(to_commit)

    print("{c.lightSlateGray}Running: {cmd}".format(c=c, cmd=cmd))
    return shell(cmd).splitlines()


@click.command()
@click.argument("commits", nargs=-1)
def astdiff(commits):
    # type: (Sequence[str]) -> None
    """Compare the AST of all changed files between commits.

    \b
    With no arguments, compare between HEAD and the working tree.
    With one argument COMMIT, compare between COMMIT~1 and COMMIT.
    With two arguments, COMMIT1 and COMMIT2, compare between those two.

    (COMMIT2 can be a dot '.' to compare between COMMIT1 and the working tree)
    """

    if not commits:
        commit2 = None
        commit1 = "HEAD"
    elif len(commits) == 1:
        commit = commits[0]
        if commit == "@":
            commit2 = "HEAD"
            commit1 = "HEAD~1"
        else:
            commit2 = commit
            commit1 = "{}~1".format(commit2)
    elif len(commits) == 2:
        commit1, commit2 = commits
        if commit2 == ".":
            commit2 = None
    else:
        click.echo(click.get_current_context().get_help())
        sys.exit(1)

    try:
        paths = collect_paths(commit1, commit2)
    except subprocess.CalledProcessError as exc:
        print("Failed to collect files")
        print(exc)
        sys.exit(1)

    all_well = True
    for path in paths:
        if not path.endswith(".py"):
            continue

        try:
            print(
                "{c.cyan}Checking {path}{c.reset} ... ".format(c=c, path=path),
                end="",
            )
            old = get_object(commit1, path)
            new = get_object(commit2, path)
            compare_ast(ast.parse(old), ast.parse(new), 0, 0)
            print("{c.green}ok{c.reset}".format(c=c))
        except AssertionError as exc:
            print("{c.bold}{c.red}failed{c.reset}".format(c=c))
            print("{c.yellow}{exc}{c.reset}".format(c=c, exc=exc))
            all_well = False
        except SyntaxError:
            print("{c.bold}{c.red}failed to parse{c.reset}".format(c=c))
            all_well = False
        except subprocess.CalledProcessError as exc:
            print("{c.bold}{c.orange}git failed{c.reset}".format(c=c))
            print("{c.yellow}{exc}{c.reset}".format(c=c, exc=exc))
            all_well = False
    print()
    if all_well:
        print("✨ {c.green}All files are equivalent!{c.reset} ✨".format(c=c))
    else:
        print("💥 {c.red}Uh oh, some files are different{c.reset} 💥".format(c=c))
    sys.exit(0 if all_well else 1)


if __name__ == "__main__":
    astdiff()
