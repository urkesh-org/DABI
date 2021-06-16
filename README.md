# DABI: Digital Analysis of Bibliographical Information

Generate static website from .md pages, using flat-file databases, page metadata and MarkDown.


## How It Works

DABI uses [pelican](https://github.com/getpelican/pelican) with custom configuration (see `pelicanconf.py`),
custom start and autoreload (see `DABI.py`),
and custom plugin for database parsing (see `DABI_databases/`).


## Getting started

Required at least Python 3.7.

To install the program in the DABI directory:
```shell
git clone https://github.com/urkesh-org/DABI.git
cd DABI
python -m pip install -r requirements.txt
```

To run the program for the example website:
```shell
cd example
../DABI.py
```


## Website root directory structure

```
/_databases/*/*.d      -->  databases for custom pages (bibliography, notes, etc)
/_templates/*.html     -->  templates for HTML generaation (written with Jinja2 scripting)
/_website/*.*          -->  output of the program, NOT user editable
/_archives/*.*         -->  old versions of website, NOT editable
/_DABI.exe             -->  DABI program [TODO exe bundle]
/_DABI.log             -->  log of DABI program
/_DABI_config.ini      -->  configuration for DABI program
/*.*                   -->  input files, .md are processed and converted to .htm, other files are hardlinked
```

All input filenames starting with "_" are ignored by the the program.


### Pages .md

The MarkDown pages contains metadata at the top followed by the content.

The metadata is in the format `KEY value` for each line.  
The content is in MarkDown, also normal HTML is allowed.  
For complicated or repetitive layout, use [Jinja2](https://jinja.palletsprojects.com/) in templates.

The `.md` pages are converted to `.htm` using the templates, with headers and navigation.

For metadata and codes documentation see `example/_databases/_README_pages.md`.


### Databases .d

The flat-file databases are stored in `_databases/`.
Each `.d` file is processed by the program and the data is available to the templates
by the variables `database_bibl`, `chapters` and `database_topics`.

For metadata and codes documentation see `example/_databases/_README_Bibliography&Notes.md`.



## Authors

* **Bernardo Forni** - [fornib](https://github.com/fornib)
* **Nizar Mohammad**


## Licensing

MIT
