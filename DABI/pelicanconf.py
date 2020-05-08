#!/usr/bin/env python3
from pathlib import Path

#DEBUG = True  # for unknown errors

SITENAME = ''  # 'Urkesh'
SITEURL = ''  # 'http://urkesh.org'
SITETITLE = ''  # 'Urkesh'
#SITESUBTITLE = ''
#SITE_DESCRIPTION = 'Structural, Digital and Philosophical Aspects of the Excavated Record'
VERSION = '01'
#AUTHOR = ''  # default Author
#DEFAULT_METADATA = {'Title': 'No title',}

DEFAULT_LANG = 'en'
LOCALE = (DEFAULT_LANG, 'en', 'en_US', '')
TIMEZONE = 'UTC'  # for Atom and RSS
DEFAULT_DATE = 'fs'  # file system mtime
DEFAULT_DATE_FORMAT = '%B %Y'

# updated on program run
MONTH = ''  # datetime.now().strftime('%B %Y').title()
YEAR = ''  # datetime.datetime.now().strftime("%Y")


# --- File locations ---
PATH = '.'  # current working directory, all paths are relative to this
IGNORE_FILES = ['_*', '*/_*']  # ignore all files and directories starting with "_"
OUTPUT_PATH = ''  # or OUTPUT_PATH = '_website/'
DELETE_OUTPUT_DIRECTORY = False  # or DELETE_OUTPUT_DIRECTORY = True
RELATIVE_URLS = True
READERS = {'html': None, 'htm': None, 'rst': None, 'markdown': None, 'mkd': None, 'mdown': None}  # only *.md rendering
FILENAME_METADATA = '(?P<title>.*)'  # get title from filename
PATH_METADATA = '(?P<path_no_ext>.*)\..*'  # also '(?P<path_no_file>.*?)[^/]*'
# USE_FOLDER_AS_CATEGORY = True  # example: 01 / Introduction / sidebartitle
SLUGIFY_SOURCE = 'basename'  # slug = filename
SLUG_REGEX_SUBSTITUTIONS = []

STATIC_PATHS = []  # or STATIC_PATHS = ['']  # copy directly
#STATIC_EXCLUDES = ['_*']
#STATIC_CREATE_LINKS = True  # create hardlinks
#STATIC_CHECK_IF_MODIFIED = True  # compare mtimes (instead of hardlinks)

PAGE_PATHS = ['']
#PAGE_EXCLUDES = ['_*']
#PAGE_DIRNAME = '.'  # TODO: what does it do?
PAGE_URL = '{path_no_ext}.htm'
PAGE_SAVE_AS = '{path_no_ext}.htm'  # or '{path_no_ext}/index.html'
#PAGE_LANG_URL = '{path_no_ext}-{lang}.htm'
PAGE_TRANSLATION_ID = None
#PAGE_ORDER_BY = 'basename'  # or metadata, for {{pages}}


ARTICLE_PATHS = []  # '_articles/'
ARTICLE_SAVE_AS = ''  # {slug}.htm or news.htm
DEFAULT_PAGINATION = False
ARTICLE_TRANSLATION_ID = None
INDEX_SAVE_AS = ''
DRAFT_PAGE_SAVE_AS = ''  # '_drafts/*'
ARCHIVES_SAVE_AS = ''  # 'news/- archives.html'
AUTHOR_SAVE_AS = ''
TAG_SAVE_AS = ''
CATEGORY_SAVE_AS = ''
DIRECT_TEMPLATES = []  # ['index', 'menu_list', 'archives', 'categories', ..]
#TEMPLATE_PAGES = {'_templates/sitemap.xml': 'sitemap.xml'}  # custom direct_templates


######INTRASITE_LINK_REGEX = '[{|](?P<what>.*?)[|}]'  # TODO: implement {B}




# --- Theme --- https://docs.getpelican.com/en/stable/themes.html#common-variables
THEME = '_templates'
THEME_TEMPLATES_OVERRIDES = ['_templates']  # first import templates from here
#TEMPLATE_EXTENSIONS = ['.html']
#THEME_STATIC_PATHS = ['static']  # files to copy directly to THEME_STATIC_DIR
#THEME_STATIC_DIR = ''
#CSS_FILE = 'main.css'
#MENUITEMS = [(Title, URL)]

# JINJA_ENVIRONMENT = {'trim_blocks': True, 'lstrip_blocks': True, 'extensions': []}  # custom extensions
# JINJA_FILTERS = {'urlencode': urlencode_filter}

# https://python-markdown.github.io/reference/#markdown
MARKDOWN = {
    'extension_configs': {
        #'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
        'markdown_meta': {},
        'markdown.extensions.nl2br': {},
        'markdown.extensions.smarty': {'smart_angled_quotes': True},  # https://python-markdown.github.io/extensions/smarty/
        # 'markdown.extensions.toc': {},
        # 'markdown.extensions.tables': {},
        # app:MyExt: {},
    },
    'output_format': 'html5',
}


# --- DABI ---
DATABASES_PATH = '_databases/'
#DB_FORMATTED_FIELDS = ['S']  # see pelican FORMATTED_FIELDS (Markdown formatted)
DATABASES_BOOKS = []


# --- Plugins ---
PLUGIN_PATHS = [Path(__file__).parent]  # same as program path  # TODO: check if it works in .exe bundle
PLUGINS = ['DABI_databases']  # also: 'optimize_images', 'minify'



#LOG_FILTER = [(logging.WARN, 'TAG_SAVE_AS is set to False')]  # logs to be ignored




# Cache only in memory
LOAD_CONTENT_CACHE = False
#CONTENT_CACHING_LAYER = 'reader'  # cache raw content
#CHECK_MODIFIED_METHOD = 'mtime'
#CACHE_CONTENT = False
#CACHE_PATH = '_cache'  # ? in the program folder



# NO Feed generation
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None



""" Pelican themes:
https://docs.getpelican.com/en/4.2.0/themes.html
https://github.com/getpelican/pelican-themes/blob/master/graymill/templates/base.html
"""


