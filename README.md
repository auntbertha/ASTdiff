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
