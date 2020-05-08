import sys
from pathlib import Path
import re
import logging
import dataclasses
from typing import List
from pelican import signals, settings, contents
from markdown import Markdown
from pelican.generators import ArticlesGenerator, PagesGenerator
from pelican.utils import pelican_open

from write_file import WriterSave

logger = logging.getLogger(__name__)

linker_regex = re.compile(r"\{B\}(?P<link>.*?)[ \"\.\,\n]")
file_extensions = ['d']


@dataclasses.dataclass
class BibliographyEntry:
    book: str
    SA: List[str] = dataclasses.field(default_factory=list)
    SD: str = ''
    NR: List[str] = dataclasses.field(default_factory=list)
    TO: List[str] = dataclasses.field(default_factory=list)
    summary: str = ''


@dataclasses.dataclass
class Bibliography:
    ID: str
    OLD_ID: List[str] = dataclasses.field(default_factory=list)
    AU: str = ''
    Y: str = ''
    T: str = ''
    P: str = ''
    entries: List[BibliographyEntry] = dataclasses.field(default_factory=list)

    def total_entries(self) -> int:
        return len(self.entries)


@dataclasses.dataclass
class Notes:  # TODO
    ID: str


@dataclasses.dataclass
class AuthorshipEntry:
    name: str
    link: str


def parse_bibl(text, file_id, file, settings, authorship_dict):
    """ Parse a Database file, :return: Bibliography object."""

    bibliography = Bibliography(ID=file_id)
    books = settings.get('DATABASES_BOOKS', ['']) or ['']
    reading_summary = False

    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith(';'):  # skip comments
            continue

        # @@@ for different summary entries
        new_entry = re.fullmatch(r'@@@(?P<book>[A-z]*) *', line)
        if new_entry:
            book = new_entry['book'].strip()
            if book not in books:
                logger.error(f'"{file}": Unrecognised or missing book reference on line {line_number}.')
                return

            bibliography.entries.append(BibliographyEntry(book=book))
            reading_summary = False
            continue

        # is it summary
        if reading_summary:
            bibliography.entries[-1].summary += '\n' + line
            continue
        elif not line.strip():  # empty line, start reading summary
            if bibliography.entries:
                reading_summary = True
            continue

        # otherwise parse key and text
        match = re.fullmatch(r'(OLD_ID|W|AU|Y|T|P|SA|SD|NR|TO)(?:[ \t]+(.*))?', line)  # extract key and text
        if not match:
            logger.error(f'"{file}": Can\'t parse line {line_number}.')
            return
        key = match.group(1)
        text = match.group(2).strip() if match.lastindex == 2 else ''

        if key not in ('SA', 'SD', 'NR', 'TO'):
            if bibliography.entries:
                logger.error(f'"{file}": Found {key} (on line {line_number}) after @@@ book reference.')
                return
            if key not in ('OLD_ID'):  # str entries
                if getattr(bibliography, key):
                    if key not in ('T', 'P'):
                        logger.error(f'"{file}": Found multiple {key} for same entry.')
                        return
                    setattr(bibliography, key,
                            getattr(bibliography, key) + '\n' + text)  # add new line for same key of 'T' or 'P'
                else:
                    setattr(bibliography, key, text)
            else:  # list entries
                getattr(bibliography, key).extend(filter(None, map(str.strip, text.split(';'))))
        else:
            if not bibliography.entries:
                logger.error(f'"{file}": Found {key} (on line {line_number}) before @@@ book reference.')
                return
            if key == 'SD':  # str entries
                if getattr(bibliography.entries[-1], key):
                    logger.error(f'"{file}": Found multiple {key} for same entry.')
                    return
                setattr(bibliography.entries[-1], key, text)
            else:  # list entries
                getattr(bibliography.entries[-1], key).extend(filter(None, map(str.strip, text.split(';'))))

    # 'AU', 'T', 'Y' are mandatory
    missing = []
    for key in ('AU', 'T', 'Y'):
        if not getattr(bibliography, key):
            missing += key
    if missing:
        logger.error(f'"{file}": Missing mandatory key(s): {", ".join(missing)}.')
        return

    # convert SA from Authorship
    for bibliography_entry in bibliography.entries:
        bibliography_entry.SA = [authorship_dict.get(SA, SA) for SA in bibliography_entry.SA]

    # Render Markdown in T, P, summary
    _md = Markdown(**settings['MARKDOWN'])
    _md.preprocessors.deregister('meta')  # prevent metadata extraction in fields
    bibliography.T = _md.convert(bibliography.T)
    _md.reset()
    bibliography.P = _md.convert(bibliography.P)
    for bibliography_entry in bibliography.entries:
        _md.reset()
        bibliography_entry.summary = _md.convert(bibliography_entry.summary)
        bibliography_entry.summary = linker_regex.sub(replace_link_match, bibliography_entry.summary)

    return bibliography


def authorship(file):
    """Generate authorship dictionary of initials from tab separated file."""
    authorship_dict = {}
    with file.open(mode='r', encoding='utf-8-sig') as handler:
        for line_number, line in enumerate(handler.readlines(), 1):
            line = line.strip()
            if line.startswith(';') or not line:  # skip comments or empty lines
                continue
            try:
                initials, name, link = map(str.strip, line.split('\t'))
            except ValueError:
                logger.error(f'"{file}": failed to parse line {line_number}.')
                continue
            if initials in authorship_dict.values():
                logger.error(f'"{file}": multiple initials "{initials}"')
                continue

            authorship_dict[initials] = AuthorshipEntry(name=name, link=link)

    return authorship_dict


def fetch_dabi_data(generators):
    settings = generators[0].settings  # all generators contain a reference to the Pelican settings
    path = Path(settings.get('PATH')) / settings.get('DATABASES_PATH', '_databases/')
    authorship_dict = authorship(path / 'Authorship.txt')

    bibl_dir = path / 'Bibliography'
    if not bibl_dir.is_dir():
        logger.warning(f'Bibliography directory not found in {path}')
        return

    database_bibl = []
    for file in bibl_dir.iterdir():
        if file.is_dir() or file.suffix[1:] not in file_extensions or file.name.startswith('_'):
            continue
        file_id = file.stem
        if ' ' in file_id:
            logger.warning(f'No spaces allowed in filename: {file}')
            file_id.replace(' ', '')
        if file_id in [b.ID for b in database_bibl]:
            logger.error(f'Multiple files found with same ID: "{file_id}" in "{path}".')
            continue

        # TODO: cache already parsed content with mtime
        try:
            with file.open(mode='r', encoding='utf-8-sig') as handler:
                bibliography = parse_bibl(handler.read(), file_id, file, settings, authorship_dict)
                if bibliography:
                    database_bibl.append(bibliography)
        except UnicodeError as err:  # TODO: automatically convert to utf-8
            logger.error(f'Could not process {file}, convert bad characters to UTF-8.\n'
                         f'UnicodeError: {err}')
        except IOError:
            raise

    # ? website = True if filename.endswith('.dw') else False

    # database_bibl = sorted(fetched_articles, key=lambda x: x.get('AU'))  # TODO: UTF sorting with locale

    for generator in generators:
        # if isinstance(generator, PagesGenerator):
        generator.context['database_bibl'] = database_bibl  # variable directly accessible in all templates


def substitute_link_in_content(content):
    """Update link {B} in content."""
    if isinstance(content, contents.Static):
        return
    if not content._content:
        return

    # content.content is read-only, edit content._content
    content._content = linker_regex.sub(replace_link_match, content._content)


def replace_link_match(match):
    # TODO: check if .d file exist
    # TODO: {B.SA}Abusch2015Gilgamesh
    html_code = f'<a href="Bibl.htm#{match.link}>{match.link}</a>"'
    return html_code


# TODO: ? set output to readonly


# monkeypatch Pelican _write_file to write only if change and rename old file
def save_file(pelican):
    return WriterSave


def register():
    """Pelican plugin registration"""
    signals.content_object_init.connect(substitute_link_in_content)
    signals.all_generators_finalized.connect(fetch_dabi_data)  # just before writing output
    signals.get_writer.connect(save_file)


'''
def initialized(pelican):
    """Set custom Pelican settings."""
    DEFAULT_CONFIG.setdefault('DABI_...', True)
    pelican.settings.setdefault('DABI_...', True)

#signals.initialized.connect(initialized)
'''

'''
class DabiReader(BaseReader):
    """Reader for .d files. Written using the core MarkdownReader as a template."""
    file_extensions = ['d']

    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)

    def _parse(self, meta):
        """Process the metadata dict from top to bottom, textilizing the value of the keys 'S', 'T' and 'P'."""
        output = {}
        for name, value in meta.items():
            name = name.lower()
            # if name == "summary":
            #    value = textile(value)  # TODO: run Markdown on it
            output[name] = self.process_metadata(name, value)
        return output

    # pelican read method: takes a filename, returns content and metadata.
    def read(self, source_path):
        """Pelican method: take filename, return content and metadata of dabi_data files."""

        with pelican_open(source_path) as text:

            parts = text.split('----', 1)
            if len(parts) == 2:
                headerlines = parts[0].splitlines()
                headerpairs = map(lambda l: l.split(':', 1), headerlines)
                headerdict = {pair[0]: pair[1].strip()
                              for pair in headerpairs
                              if len(pair) == 2}
                metadata = self._parse(headerdict)
                content = parts[1]
            else:
                metadata = {}
                content = text

            ## read md file - create a MarkdownReader
            #md_reader = MarkdownReader(self.settings)
            #content, metadata = md_reader.read(md_filename)

        return content, metadata

def add_reader(readers):
    readers.reader_classes['d'] = DabiReader

#signals.readers_init.connect(add_reader)
'''

""" ---------------- CSV loader (not very useful...)
def csv_loader(csv_elem, curpath, delim=','):

    if "'''" in csv_elem:
        filename = None
        doc = csv_elem.split("'''")[1]
    else:
        filename = csv_elem.split("'")[1]  # {% csv 'data-sbp.csv' %}
        filepath = os.path.join('content', curpath, filename)
        with open(filepath, 'r', encoding='utf-8') as f:  # TODO: check for encoding?
            doc = f.read()

    csv_list = filter(None, doc.splitlines())  # lines, and remove empty line
    csv_string = '<table>'

    for i, row in enumerate(csv_list):
        if i == 0:
            csv_string += '<tr><th>{}</th></tr>'.format('</th><th>'.join(row.split(delim)))
        else:
            csv_string += '<tr><td>{}</td></tr>'.format('</td><td>'.join(row.split(delim)))

    if filename:
        csv_string += f'<tr><td colspan="{len(list(csv_list)[0].split(delim))}" class="data-link"><a href="{filename}">data link</a></td></tr>'

    csv_string += '</table>'

    return csv_string


def write_data(data_passed_from_pelican):
    '''read through each page and post as it comes through from Pelican, find all instances of triple-backtick (```...```) code blocks, and add an HTML wrapper to each line of each of those code blocks'''

    if not data_passed_from_pelican._content:
        return  # skip static files

    updated_page_content = data_passed_from_pelican._content  # NOTE: `data_passed_from_pelican.content` seems to be read-only, whereas `data_passed_from_pelican._content` is able to be overwritten. (Mentioned by Jacob Levernier in his Better Code-Block Line Numbering Plugin)
    curpath = os.path.dirname(data_passed_from_pelican.get_relative_source_path())

    all_csv_elements = re.findall('{% csv .*? %}', updated_page_content, re.DOTALL)  # dot matches newline too

    for csv_elem in all_csv_elements:
        replacement = csv_loader(csv_elem, curpath)
        updated_page_content = updated_page_content.replace(csv_elem, replacement)

        data_passed_from_pelican._content = updated_page_content

def register():
    signals.content_object_init.connect(write_data)
"""

''' jinja2content
class JinjaContentMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # will look first in 'JINJA2CONTENT_TEMPLATES', by default the
        # content root path, then in the theme's templates
        local_dirs = self.settings.get('JINJA2CONTENT_TEMPLATES', ['.'])
        local_dirs = [os.path.join(self.settings['PATH'], folder)
                      for folder in local_dirs]
        theme_dir = os.path.join(self.settings['THEME'], 'templates')

        loaders = [FileSystemLoader(_dir) for _dir
                   in local_dirs + [theme_dir]]
        if 'JINJA_ENVIRONMENT' in self.settings: # pelican 3.7
            jinja_environment = self.settings['JINJA_ENVIRONMENT']
        else:
            jinja_environment = {
                'trim_blocks': True,
                'lstrip_blocks': True,
                'extensions': self.settings['JINJA_EXTENSIONS']
            }
        self.env = Environment(
            loader=ChoiceLoader(loaders),
            **jinja_environment)


    def read(self, source_path):
        with pelican_open(source_path) as text:
            text = self.env.from_string(text).render()

        with NamedTemporaryFile(delete=False) as f:
            f.write(text.encode())
            f.close()
            content, metadata = super().read(f.name)
            os.unlink(f.name)
            return content, metadata


class JinjaMarkdownReader(JinjaContentMixin, MarkdownReader):
    pass

class JinjaRstReader(JinjaContentMixin, RstReader):
    pass

class JinjaHTMLReader(JinjaContentMixin, HTMLReader):
    pass

def add_reader(readers):
    for Reader in [JinjaMarkdownReader, JinjaRstReader, JinjaHTMLReader]:
        for ext in Reader.file_extensions:
            readers.reader_classes[ext] = Reader

def register():
    signals.readers_init.connect(add_reader)

'''


