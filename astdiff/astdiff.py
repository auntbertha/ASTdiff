#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from typing import Union, List, Any, Sequence, Optional, Tuple, Dict
import ast
import subprocess
import sys
import os

from six.moves import zip_longest
from six import string_types
import click
import colorful as c


NodeType = Union[ast.AST, List, str]


# noinspection PyUnresolvedReferences
color = c.format


def compare_ast(left, right, line_counter=None):
    # type: (NodeType, NodeType, Optional[Dict[str, int]]) -> None
    """Compare two abstract syntax trees.

    Return `None` if they are equal, and raise an exception otherwise.
    """
    if line_counter is None:
        line_counter = {}

    assert_equal(type(left), type(right), line_counter)

    if isinstance(left, ast.AST):
        line_counter["left"] = getattr(
            left, "lineno", line_counter.get("left", 1)
        )
        line_counter["right"] = getattr(
            right, "lineno", line_counter.get("right", 1)
        )

        left_fields = ast.iter_fields(left)
        right_fields = ast.iter_fields(right)
        for left_field, right_field in zip_longest(
            left_fields, right_fields, fillvalue=""
        ):
            left_name, left_values = left_field
            right_name, right_values = right_field
            assert_equal(left_name, right_name, line_counter)
            compare_ast(left_values, right_values, line_counter)
    elif isinstance(left, list):
        for left_child, right_child in zip_longest(left, right, fillvalue=""):
            compare_ast(left_child, right_child, line_counter)
    else:
        assert_equal(left, right, line_counter)


def assert_equal(left, right, line_counter):
    # type: (Any, Any, Dict[str, int]) -> None
    """Compare two objects.

    Return `None` if equal, and raise an exception with the line number
    otherwise.
    """
    assert left == right, (
        "different nodes:\n"
        "line {} in first commit: {}\n"
        "line {} in second commit: {}".format(
            line_counter.get("left", 0),
            nice(left),
            line_counter.get("right", 0),
            nice(right),
        )
    )


def nice(obj):
    # type: (Any) -> str
    """Get a nice repr of AST objects, or the usual `str` otherwise. """

    if isinstance(obj, ast.AST):
        return type(obj).__name__
    if isinstance(obj, type):
        return obj.__name__
    return str(obj)


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

    If `to_commit` is None, diff against the current working tree.
    """
    cmd = "git diff --name-only {}".format(from_commit)

    if to_commit:
        cmd += " {}".format(to_commit)

    # noinspection PyUnresolvedReferences
    stderr(c.lightSlateGray | "Running: {cmd}".format(cmd=cmd))
    return shell(cmd).splitlines()


def get_ref(commit):
    # type: (Optional[str]) -> Optional[str]
    """Convert a commit to its hash.

    It handles the syntax for references, such as special names like HEAD or
    @, parents commits, and many more. See `git help rev-parse` for full
    reference.

    Return `None` if the input is `None`.
    """
    if commit is None:
        return None
    return shell("git rev-parse {}".format(commit))


def get_commits(commits):
    # type: (Sequence[str]) -> Tuple[str, Optional[str]]
    """Process the commit references given as parameters to the command.

    Return a pair of hashes identifying the range that we want to compare.
    The second commit equal to `None` signals that we want to compare against
    the working tree.
    """
    if not commits:
        commit2 = None
        commit1 = "HEAD"
    elif len(commits) == 1:
        commit2 = commits[0]
        commit1 = "{}~1".format(get_ref(commit2))
    elif len(commits) == 2:
        commit1, commit2 = commits
        if commit2 == ".":
            commit2 = None
    else:
        raise ValueError("invalid commit references: {}".format(commits))
    return get_ref(commit1), get_ref(commit2)


def stderr(*messages, **kwargs):
    # type: (Any, Any) -> None
    """Send messages to stderr.

    Print one argument per line, and support colored arguments.
    `kwargs` are passed to the `print` function.
    """
    print(
        color("\n".join(str(msg) for msg in messages if str(msg))),
        file=sys.stderr,
        **kwargs
    )


def error(*messages):
    # type: (str) -> None
    stderr("💥 🔥 💥", *messages)


def shell_error(message, exc):
    # type: (str, subprocess.CalledProcessError) -> None
    """Display an error from a shell command. """
    _, cmd = exc.args
    # noinspection PyUnresolvedReferences
    error(message, c.orange | "'{}' failed".format(" ".join(cmd)))


# noinspection PyUnresolvedReferences
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
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

    try:
        commit1, commit2 = get_commits(commits)
    except ValueError as exc:
        error(c.red | str(exc))
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        shell_error("Failed to compute commits", exc)
        sys.exit(1)

    try:
        paths = collect_paths(commit1, commit2)
    except subprocess.CalledProcessError as exc:
        shell_error("Failed to collect files", exc)
        sys.exit(1)

    ok = 0
    fails = 0
    errors = 0
    for path in paths:
        if not path.endswith(".py"):
            continue

        try:
            stderr(
                "{c.cyan}Checking {path}{c.reset} ... ".format(c=c, path=path),
                end="",
            )
            old = get_object(commit1, path)
            new = get_object(commit2, path)
            compare_ast(ast.parse(old), ast.parse(new))
            stderr(c.green | "ok")
            ok += 1
        except AssertionError as exc:
            stderr(c.bold & c.red | "failed", exc)
            fails += 1
        except SyntaxError as exc:
            stderr(c.bold & c.orange | "failed to parse", exc)
            errors += 1
        except subprocess.CalledProcessError as exc:
            stderr("git failed")
            shell_error("", exc)
            errors += 1

    if fails == errors == 0:
        stderr(c.green | "✨ All files are equivalent! ✨")
        sys.exit(0)
    else:
        error(
            c.red | "Uh-oh, there are errors:",
            c.cyan | "{} files ok".format(ok) if ok else "",
            c.red | "{} files failed".format(fails) if fails else "",
            c.orange | "{} errors".format(errors) if errors else "",
        )
        sys.exit(1)


if __name__ == "__main__":
    astdiff()
