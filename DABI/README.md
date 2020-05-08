# DABI: Digital Analysis of Bibliographical Information

Generate static website from .md files and databases, using metadata and MarkDown.


## Website structure

./                      -->  input files, .md are processed with templates and databases, all other files are copied
./_DABI_config.ini      -->  configuration for program
./_databases/*/*.d      -->  databases for custom pages (bibliography, notes, etc)
./_templates/*.html     -->  templates for generating the HTML from .md (written with jinja2 scripting)
((( ./archives/         -->  old versions of website, accessible from SITEURL/archives/ [NOT editable] )))

All filenames starting with "_" are ignored.



## Pages .md

All pages MUST have metadata at the top followed by the content (separated by a couple of new lines).

The content is in MarkDown, see here for documentation: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
Normal HTML is allowed.
For complicated or repetitive layout, make use of jinja2 scripting: https://jinja.palletsprojects.com/en/2.11.x/templates/

The HTML headers and menu are added automatically using the templates.



### Metadata for pages .md

AU author(s), separated by semicolon
D date (if missing last file modification date will be used)
T title
S (optional) subtitle
DE (optional) description, used for describing the page to Search Engines (as Google)



## Databases .d

See inside "_databases/" for the description of each database.
The files are processed by the program and are available to the pages using "{database_ID}file_name" inside the content.
Example: {B}Abusch2015Gilgamesh
Output:  <a href="bibl.htm#Abusch2015Gilgamesh">Abusch 2015 Gilgamesh</a>

(advanced) For direct access to the data use the database name as a python class in jinja2.
Example: {{ B.get('Abusch2015Gilgamesh').SA }}
Output:  Summary Author of Abusch2015Gilgamesh

