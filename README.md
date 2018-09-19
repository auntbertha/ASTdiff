# ASTdiff

Compare two commits in a git repository to guarantee that there are no semantic changes.

Use this tool to corroborate that formatting tools don't change the code. If `astdiff` returns 0, the Abstract Syntax 
Tree of the files changed in the commits is the same.


## Installation

Using `pip`:

```shell
pip install astdiff
```


### Development Installation

To audit the code, or to modify it, install `astdiff` in development mode. The tool uses [poetry](https://poetry.eustace.io/) to manage dependencies
and to build `pip` installable packages. 

```bash
$ git clone https://github.com/auntbertha/astdiff.git
$ cd astdiff
$ poetry develop
$ poetry run pytest
```

To build new packages:

```bash
$ poetry build
```

and distribute the wheel or tarball from the directory `dist/`.


## Usage

The most basic use of `astdiff` is to check that a reformatting tool didn't change the meaning of the code. When it's
called with no arguments `astdiff` compares the working tree against the HEAD of the current branch:

```bash
$ astdiff
Running: git diff --name-only 9d3219ba027d5a56040d23eb9ee3d23f7a410ad5
Checking astdiff/astdiff.py ... ok
✨ All files are equivalent! ✨
$ echo $?
0
```

`astdiff` returns 0 if the ASTs are the same, and returns 1 otherwise. The messages are printed to standard error.

`astdiff` can also check a given commit, a given commit and the working tree, or any pair of commits. It accepts the
names of the commits in the same way that `git` does.

Use `-h` or `--help` to get help:

```bash
$ astdiff -h
Usage: astdiff.py [OPTIONS] [COMMITS]...

  Compare the AST of all changed files between commits.

  With no arguments, compare between HEAD and the working tree.
  With one argument COMMIT, compare between COMMIT~1 and COMMIT.
  With two arguments, COMMIT1 and COMMIT2, compare between those two.

  (COMMIT2 can be a dot '.' to compare between COMMIT1 and the working tree)

Options:
  -h, --help  Show this message and exit.
```


## Algorithm

The comparison of the ASTs is a very simple recursive function that traverses the trees in a pre-order depth-first 
search. It can be audited to verify its correctness: `astdiff.compare_ast`.


## LICENSE

© 2018 Aunt Bertha