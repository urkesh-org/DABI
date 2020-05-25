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

logger = logging.getLogger(__name__)

linker_regex = re.compile(r"\{B\}(?P<site>[\w-]*?)\/(?P<id>[\w-]*)")
file_extensions = ['d']


@dataclasses.dataclass
class BibliographyEntry:
    sites: List[str]
    SA: List[str] = dataclasses.field(default_factory=list)
    SD: str = ''
    NR: List[str] = dataclasses.field(default_factory=list)
    TO: List[str] = dataclasses.field(default_factory=list)
    summary: str = ''


@dataclasses.dataclass
class Bibliography:
    ID: str
    ID_full: str  # ID with spaces
    OLD_ID: List[str] = dataclasses.field(default_factory=list)
    AU: List[str] = dataclasses.field(default_factory=list)
    AU_extra: str = ''
    Y: str = ''
    T: str = ''
    P: str = ''
    entries: List[BibliographyEntry] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Notes:  # TODO
    ID: str


@dataclasses.dataclass
class AuthorshipEntry:
    name: str
    link: str


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


def parse_bibl(text, file_id, sites_abbr, settings, authorship_dict):
    """ Parse a Database file, :return: Bibliography object."""

    bibliography = Bibliography(ID=file_id, ID_full=add_spaces_to_id(file_id))
    reading_summary = False

    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith(';'):  # skip comments
            continue

        # @@@ for different summary entries
        new_entry = re.fullmatch(r'@@@(?P<sites>.*)', line)
        if new_entry:
            sites = list(map(str.strip, new_entry.group('sites').strip().strip(',;').split(';')))
            for site in sites:
                if site not in sites_abbr:
                    raise UserWarning(f'unrecognised @@@ site reference "{site}" (line {line_number})')
            sites = [sites_abbr[site] for site in sites]
            
            bibliography.entries.append(BibliographyEntry(sites=sites))
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
            raise UserWarning(f'unrecognised key (line {line_number})')
        key = match.group(1)
        text = match.group(2).strip() if match.lastindex == 2 else ''

        if key not in ('SA', 'SD', 'NR', 'TO'):
            if bibliography.entries:
                raise UserWarning(f'found {key} after @@@ site reference (on line {line_number})')
            if key not in ('OLD_ID', 'AU'):  # str entries
                if getattr(bibliography, key):
                    if key not in ('T', 'P'):
                        raise UserWarning(f'found multiple keys "{key}" for same entry')
                    # add new line for same key of 'T' or 'P'
                    setattr(bibliography, key, getattr(bibliography, key) + '  \n' + text)
                else:
                    setattr(bibliography, key, text)
            else:  # list entries
                if key == 'AU':
                    match = re.fullmatch(r'(.*)\s?\((?P<extra>.*?)\)\s?\.?', text.strip().strip(',;'))
                    if match:
                        text = match.group(1)
                        setattr(bibliography, 'AU_extra', match.group('extra'))
                text = filter(None, map(str.strip, text.strip().strip(',;').split(';')))
                getattr(bibliography, key).extend(text)
        else:
            if not bibliography.entries:
                raise UserWarning(f'found key "{key}" before @@@ site reference (on line {line_number})')
            if key == 'SD':  # str entries
                if getattr(bibliography.entries[-1], key):
                    raise UserWarning(f'found multiple keys "{key}" for same entry')
                setattr(bibliography.entries[-1], key, text)
            else:  # list entries
                getattr(bibliography.entries[-1], key).extend(filter(None, map(str.strip, text.strip(',;').strip().split(';'))))

    # 'AU', 'T', 'Y', '@@@' are mandatory
    missing = []
    for key in ('AU', 'T', 'Y'):
        if not getattr(bibliography, key):
            missing.append(key)
    if not getattr(bibliography, 'entries'):
        missing.append('@@@')
    if missing:
        raise UserWarning(f'missing mandatory keys "{", ".join(missing)}"')

    # convert SA from Authorship
    for bibliography_entry in bibliography.entries:
        bibliography_entry.SA = [authorship_dict.get(SA, SA) for SA in bibliography_entry.SA]

    # Render Markdown in T, P, summary
    _md = Markdown(**settings['MARKDOWN'])  # use custom Markdown, without metadata extraction
    _md.preprocessors.deregister('meta')
    bibliography.T = _md.convert(bibliography.T)
    _md.reset()
    bibliography.P = _md.convert(bibliography.P)
    for bibliography_entry in bibliography.entries:
        _md.reset()
        bibliography_entry.summary = _md.convert(bibliography_entry.summary)
        bibliography_entry.summary = linker_regex.sub(replace_link_match, bibliography_entry.summary)
    
    return bibliography


def fetch_dabi_data(generators):
    settings = generators[0].settings  # all generators contain a reference to the Pelican settings
    path = Path(settings.get('PATH')) / settings.get('DATABASES_PATH', '_databases/')
    authorship_dict = authorship(path / 'Authorship.txt')

    bibl_dir = path / 'Bibliography'
    if not bibl_dir.is_dir():
        logger.warning(f'Bibliography directory not found in {path}')
        return

    sites_abbr = {settings['SITE'][site].get('ABBR', ''): site for site in settings['SITE'] if site}
    database_bibl = {site: [] for site in settings['SITE'] if site}  # {site: [bibliography,]}
    errors = []
    # TODO: cache already parsed content with mtime
    for file in bibl_dir.iterdir():
        if file.is_dir() or file.suffix[1:] not in file_extensions or file.name.startswith('_'):
            continue
        try:
            file_id = file.stem
            if ' ' in file_id:
                if re.search(r' [A-z]{2}[0-9]{3}', file_id):  # ignore files with date in filename (old file version)
                    continue
                raise UserWarning(f'spaces in filename allowed ONLY for dates (ZA000 format)')

            with file.open(mode='r', encoding='utf-8-sig') as handler:
                bibliography = parse_bibl(handler.read(), file_id, sites_abbr, settings, authorship_dict)
                for entry in bibliography.entries:
                    for site in entry.sites:
                        if bibliography not in database_bibl[site]:
                            database_bibl[site].append(bibliography)
            
        except UnicodeError as err:  # ? automatically convert to utf-8
            error = f'"{file.name}": bad characters in file, convert to UTF-8 (UnicodeError: {err}).'
            logger.error(error)
            errors.append(error)
        except UserWarning as error:
            error = f'"{file.name}": {error}.'
            logger.error(error)
            errors.append(error)
        except IOError:
            raise

    # ? website = True if filename.endswith('.dw') else False

    # ? sorting in template: sorted(fetched_articles, key=lambda x: x.get('AU'))  # TODO: UTF sorting with locale
    
    # generate author index
    database_bibl_short = {site: dict() for site in settings['SITE'] if site}  # {site: {AU: [bibliography,]}}
    for site in settings['SITE']:
        if site:
            for bibliography in database_bibl[site]:
                for AU in bibliography.AU:
                    database_bibl_short[site][AU] = database_bibl_short[site].get(AU, []) + [bibliography]
    
    # generate topic index
    database_bibl_topics = {site: dict() for site in settings['SITE'] if site}  # {site: {AU: [bibliography,]}}
    for site in settings['SITE']:
        if site:
            for bibliography in database_bibl[site]:
                for entry in bibliography.entries:
                    for TO in entry.TO:
                        database_bibl_topics[site][TO] = database_bibl_topics[site].get(TO, []) + [bibliography]

    for generator in generators:
        # add variables directly accessible in templates
        if isinstance(generator, PagesGenerator):
            generator.context['database_bibl'] = database_bibl
            generator.context['database_bibl_short'] = database_bibl_short
            generator.context['database_bibl_topics'] = database_bibl_topics
            generator.context['errors'] = errors


def update_localcontext(page_generator, content):
    content.site = content.settings['SITE'].get(content.folder,'')
    return 'test'


def replace_link_content(content):
    """Update link {B} in content and remove comments."""
    if isinstance(content, contents.Static):
        return
    if not content.content:
        return

    sites_abbr = {content.settings['SITE'][site].get('ABBR', ''): site for site in content.settings['SITE'] if site}

    # content.content is read-only, edit content._content
    content._content = linker_regex.sub(replace_link_match(sites_abbr), content._content)


def replace_link_match(sites_abbr):
    def f(match):
        # TODO: check if .d file exist
        
        site = sites_abbr.get(match.group("site"), match.group("site"))
        id_text = add_spaces_to_id(match.group("id"))
        html_code = f'<a href="{{filename}}/{site}/bibl.md#{match.group("id")}">{id_text}</a>'
        return html_code
    return f


def add_spaces_to_id(id):
    return re.sub(r'\B([A-Z]|[0-9]{4})', r' \1', id)


def register():
    """Pelican plugin registration"""
    signals.content_object_init.connect(replace_link_content)
    signals.all_generators_finalized.connect(fetch_dabi_data)  # before writing output read databases
    signals.page_generator_write_page.connect(update_localcontext)


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
