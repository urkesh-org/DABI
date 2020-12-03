# DABI: Digital Analysis of Bibliographical Information

Generate static website from .md pages and .d databases, using metadata and MarkDown.


### Installation


### Usage

`cd website_root_directory; DABI.py`


--- pelican

## Website structure in root directory

```
/_databases/*/*.d      -->  databases for custom pages (bibliography, notes, etc)
/_templates/*.html     -->  templates for generating the HTML from .md (written with jinja2 scripting)
/_website/*.*          -->  output of the program, NOT user editable
/_archives/*.*         -->  old versions of website, NOT editable
/_DABI.exe             -->  DABI program
/_DABI.log             -->  log of DABI program
/_DABI_config.ini      -->  configuration for DABI program
/*.*                   -->  input files, .md are processed and converted to .htm, other files are hardlinked
```

All input filenames starting with "_" are ignored by the the program.



## Pages .md

All pages have metadata at the top followed by the content (separated by a couple of new lines).

The metadata is in the format `KEY value` for each line.

The content is in MarkDown, see here for documentation: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet  
Normal HTML is allowed.  
For complicated or repetitive layout, use jinja2 in templates.

The HTML headers and menu are added automatically using the templates.



### Metadata for pages .md

AU author(s), separated by semicolon
D date (if missing last file modification date will be used)
T title
TO (optional) topics (semicolon separated)
S (optional) subtitle
DE (optional) description, used for describing the page to Search Engines (as Google)
HTML (optional) custom template



## Databases .d

See inside "_databases/" for the description of each database.  
The files are processed by the program and are available to the templates in the `database_bibl`, `chapters`, and `database_topics` variable.

To reference other entries: `{B}site/ID_of_the_entry` (e.g. `{B}R/Abusch2015Gilgamesh` ).

