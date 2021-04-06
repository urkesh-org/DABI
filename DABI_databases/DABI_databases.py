from pathlib import Path
import codecs
import re
import logging
import locale
import dataclasses
import copy
from itertools import groupby
from datetime import datetime
from typing import List
import jinja2
from markdown import Markdown
from pelican import signals

logger = logging.getLogger(__name__)

META_REGEX = re.compile(r'^(?P<key>[A-Z]+)(\s|$)(?P<value>.*)')
LINKER_REGEX = re.compile(r"{(?P<page>[BN])}(?P<site>[\w\-]*?)/(?P<id>[\w\-\&\.]*(?<!\.))")  # \w or [A-Za-zÀ-ÖØ-öø-ÿ]
HTML_TAG_REGEX = re.compile(r'<[^>]+>')
file_extensions = ['d']


@dataclasses.dataclass
class TextWithLink:
    text: str
    link: str = ''


@dataclasses.dataclass
class BibliographyEntry:
    SA: List[TextWithLink] = dataclasses.field(default_factory=list)  # Summary Authors
    SD: str = ''  # Summary Date
    NR: List[TextWithLink] = dataclasses.field(default_factory=list)  # Note Reference
    TO: List[str] = dataclasses.field(default_factory=list)  # Topics
    text: str = ''
    sites: List[str] = dataclasses.field(default_factory=list)
    line_number: int = 0  # identifies the first line of the bibliography entry


@dataclasses.dataclass
class Bibliography:
    ID: str
    REF: str = ''  # Reference
    OLD_ID: List[str] = dataclasses.field(default_factory=list)
    AU: List[str] = dataclasses.field(default_factory=list)  # Authors
    AU_extra: str = ''
    W: bool = False  # is it a Website
    Y: str = ''  # Year
    T: str = ''  # Title
    P: str = ''  # Publication
    entries: List[BibliographyEntry] = dataclasses.field(default_factory=list)
    site: str = ''


@dataclasses.dataclass
class Note:
    ID: str
    file_ID: str
    NA: List[TextWithLink] = dataclasses.field(default_factory=list)  # Note Authors
    ND: str = ''  # Note Date
    CT: str = ''  # Category
    TO: List[str] = dataclasses.field(default_factory=list)  # Topics
    text: str = ''
    site: str = ''
    line_number: int = 0  # identifies the first line of the note


@dataclasses.dataclass
class Topic:
    TO: str  # Topic
    section: str = ''
    text: str = ''
    link: str = ''
    site: str = ''


@dataclasses.dataclass
class SubChapter:
    ID: str
    title: str
    notes: List[Note] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Chapter:
    ID: str
    title: str
    sub_chapters: List[SubChapter] = dataclasses.field(default_factory=list)
    site: str = ''


def linker(text, ID, sites_abbr, database_bibl, chapters, errors=None, add_to_NR=None, start_line=0):
    """Convert {B|N} links"""

    def capture_and_replace_link_match(match: re.Match):
        site = sites_abbr.get(match.group('site'), match.group('site'))
        id_text = match.group('id')
        error = False

        nonlocal start_line
        _lines = match.string[0:match.start()].count('\n')
        line_number = _lines + start_line

        if match.group('page') == 'B':
            try:
                bibliography = next(b for b in database_bibl if b.site == site and b.ID == id_text)
                ref = bibliography.REF
                if add_to_NR:
                    bibliography.entries[0].NR.append(add_to_NR)
            except StopIteration:  # entry not in bibliography
                error = True
                ref = re.sub(r'\B([A-Z]|[0-9]{4}|&|-)', r' \1', id_text)  # add spaces

            new_text = f'<a href="/{site}/bibl.htm#{id_text}">{ref}</a>'

        else:  # match.group('page') == 'N':
            ch = id_text.split('.', 1)[0]
            try:
                chapter = next(chapter for chapter in chapters if chapter.site == site and chapter.ID == ch)
                sub_chapter = next(sub_chapter for sub_chapter in chapter.sub_chapters if sub_chapter.ID == id_text)
            except StopIteration:  # entry not in notes
                error = True

            new_text = f'<a href="/{site}/Notes/{ch.zfill(2)}.htm#{id_text}">{id_text}</a>'

        if error:
            error_text = f'"{ID}": link reference "{match.group()}" not found in database (around line {line_number}).'
            logger.error(error_text)
            if errors is not None:
                errors.append(error_text)

        return new_text

    return LINKER_REGEX.sub(capture_and_replace_link_match, text)


def add_filters_to_context(page_generator):
    """Custom functions for Jinja2 templates"""

    def filter_site(database, site=''):
        return [entry for entry in database if entry.site == site]

    def select_chapter(chapters, ch, site=''):
        return next(chapter for chapter in chapters if chapter.site == site and chapter.ID == ch)

    def author_bibl_list(database_bibl):
        """generate short author index"""
        database_bibl_short = dict()  # {AU: [bibliography, ], }
        for bibliography in database_bibl:
            for AU in bibliography.AU:
                database_bibl_short[AU] = database_bibl_short.get(AU, []) + [bibliography]
            # ? AU + ' <small>(with ..)' / (eds.)
        return [(AU, database_bibl_short[AU]) for AU in sorted(database_bibl_short, key=locale.strxfrm)]

    def filter_SA(database_bibl, author):
        for bibl in database_bibl:
            if any(author == SA.text for b_entry in bibl.entries for SA in b_entry.SA):
                yield bibl

    def filter_NA(chapters, author):
        for chapter in chapters:
            for sub_chapter in chapter.sub_chapters:
                for i, note in enumerate(sub_chapter.notes):
                    if any(author == NA.text for NA in note.NA):
                        letter = chr(97 + i)  # letter note reference
                        yield note, letter

    def short_title(title):
        return HTML_TAG_REGEX.sub('', title.split('<br>', 1)[0].replace('&ldquo;', '').replace('&rdquo;', ''))

    @jinja2.environmentfilter
    def sorted_groupby(environment, value, attribute):
        expr = jinja2.filters.make_attrgetter(environment, attribute)
        return [jinja2.filters._GroupTuple(key, list(values)) for key, values in groupby(value, expr)]

    # add filters to context
    page_generator.env.filters.update({'filter_site': filter_site,
                                       'select_chapter': select_chapter,
                                       'author_bibl_list': author_bibl_list,
                                       'filter_SA': filter_SA, 'filter_NA': filter_NA,
                                       'short_title': short_title,
                                       'sorted_groupby': sorted_groupby, 'chr': chr})


def parse_authorship(file):
    """Generate authorship dictionary of initials from tab separated file."""
    authorship_dict = dict()

    if not file.is_file():
        logger.warning(f'No authorship file found: {file.name}')
        return authorship_dict

    try:
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

                authorship_dict[initials] = TextWithLink(text=name, link=link)

    except (OSError, UnicodeError) as err:
        raise UserWarning(f'"{file}": Can\'t parse authorship ({err}).')

    return authorship_dict


def parse_chapters(path):
    """Generate chapters list from one space separated files."""
    chapters = []

    for file in path.glob('*.txt'):
        if not file.is_file():
            continue
        try:
            with file.open(mode='r', encoding='utf-8-sig') as handler:
                for line_number, line in enumerate(handler.readlines(), 1):
                    line = line.strip()
                    if line.startswith(';') or not line:  # skip comments or empty lines
                        continue
                    try:
                        number, title = map(str.strip, line.split(' ', 1))
                        number = number.strip('.')
                    except ValueError:
                        logger.error(f'"{file}": missing chapter title (line {line_number}).')
                        continue

                    if '.' not in number:  # if chapter
                        chapters.append(Chapter(ID=number, title=title, site=file.stem))
                        chapters[-1].sub_chapters.append(SubChapter(ID=f'{number}', title=f''))
                    else:  # if sub-chapter
                        chapters[-1].sub_chapters.append(SubChapter(ID=number, title=title))

        except (IndexError, OSError, UnicodeError) as err:
            raise UserWarning(f'"{file}": Can\'t parse chapters ({err}).')

    # TODO: more error corrections? (eg: missing chapters, double references)
    return chapters


def parse_date(date):
    """Parse 'day Month Year' date, day is used only for sorting"""
    try:
        datetime.strptime(date, '%Y')
    except ValueError:
        try:
            return datetime.strptime(date, '%B %Y').replace(hour=1)
        except ValueError:
            return datetime.strptime(date, '%d %B %Y').replace(hour=2)


def parse_bibl(text, file_id, sites_abbr, authorship_dict, md):
    """Parse a Database file, :return: Bibliography object."""
    bibliography = Bibliography(ID=file_id)
    notes = []

    block = ''
    reading_text = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith(';'):  # skip comments
            continue

        # @@@ for different summary entries
        new_bibl_entry = re.fullmatch(r'@@@(?P<sites>.*)', line)
        if new_bibl_entry:
            sites = list(map(str.strip, new_bibl_entry.group('sites').split('; ')))
            for site in sites:
                if site not in sites_abbr:
                    raise UserWarning(f'unrecognised @@@ site reference "{site}" (line {line_number})')

            bibliography.entries.append(
                BibliographyEntry(sites=[sites_abbr[site] for site in sites]))
            block = 'summary'
            reading_text = False
            continue

        # @NOTES for different note entries
        new_note_entry = re.fullmatch(r'@NOTES (?P<site>[\w\-&]*?)/(?P<id>[\d.]*)', line)
        if new_note_entry:
            site = new_note_entry.group('site')
            if site not in sites_abbr:
                raise UserWarning(f'unrecognised @NOTES site reference "{site}" (line {line_number})')

            notes.append(
                Note(ID=new_note_entry.group('id'), file_ID=file_id, site=sites_abbr[site]))
            block = 'notes'
            reading_text = False
            continue

        if reading_text:
            if block == 'summary':
                bibliography.entries[-1].text += '\n' + line
            elif block == 'notes':
                notes[-1].text += '\n' + line
            continue
        
        if not line.strip():  # empty line, start reading text
            reading_text = True
            
            # save first line number (not precise, because text converted from Markdown)
            if block == 'summary':
                bibliography.entries[-1].line_number = line_number + 1
            elif block == 'notes':
                notes[-1].line_number = line_number + 1
            continue

        # otherwise parse metadata
        meta = META_REGEX.fullmatch(line)
        if not meta:
            raise UserWarning(f'can\'t parse metadata (line {line_number})')
        key = meta.group('key')
        value = meta.group('value').strip()

        if not block:
            if key not in ('OLD_ID', 'AU', 'W', 'Y', 'T', 'P'):
                raise UserWarning(f'unrecognised metadata key "{key}" (line {line_number})')

            if key in ('Y', 'T', 'P'):  # str entries
                if not getattr(bibliography, key):
                    setattr(bibliography, key, value)
                else:  # add new line for same key
                    setattr(bibliography, key, getattr(bibliography, key) + '<br>' + value)

            else:  # list entries
                if key == 'W':
                    setattr(bibliography, 'W', True)
                    key = 'AU'

                if key == 'AU':
                    match_AU_extra = re.fullmatch(r'(.*)\s+\((?P<extra>.*?)\)\s?\.?', value)
                    if match_AU_extra:
                        value = match_AU_extra.group(1)
                        setattr(bibliography, 'AU_extra', match_AU_extra.group('extra'))

                values = filter(None, map(str.strip, value.split('; ')))
                getattr(bibliography, key).extend(values)

        elif block == 'summary':
            if key not in ('SA', 'SD', 'NR', 'TO'):
                raise UserWarning(f'unrecognised metadata key "{key}" (line {line_number})')

            if key in ('SD',):  # str entries
                if getattr(bibliography.entries[-1], key):
                    raise UserWarning(f'found multiple keys "{key}" for same entry (line {line_number})')
                if key == 'SD' and value:
                    try:
                        value = parse_date(value)
                    except ValueError:
                        raise UserWarning(f'can\'t parse date "{value}" (line {line_number})')

                setattr(bibliography.entries[-1], key, value)

            else:  # list entries
                values = filter(None, map(str.strip, value.split('; ')))
                if key == 'SA':  # convert abbreviations
                    values = [authorship_dict.get(SA, TextWithLink(SA)) for SA in values]
                elif key == 'NR':  # (deprecated)
                    values = [TextWithLink(NR, link=f'Notes/{NR.split(".", 1)[0].zfill(2)}.htm#{NR}') if NR[0].isdigit()
                              else TextWithLink(md.reset().convert(NR)[len('<p>'):-len('</p>')]) for NR in values]
                getattr(bibliography.entries[-1], key).extend(values)

        elif block == 'notes':
            if key not in ('NA', 'ND', 'CT', 'TO'):
                raise UserWarning(f'unrecognised metadata key "{key}" (line {line_number})')

            if key in ('ND', 'CT'):  # str entries
                if getattr(notes[-1], key):
                    raise UserWarning(f'found multiple keys "{key}" for same entry (line {line_number})')
                if key == 'ND' and value:
                    try:
                        value = parse_date(value)
                    except ValueError:
                        raise UserWarning(f'can\'t parse date "{value}" (line {line_number})')

                setattr(notes[-1], key, value)

            else:  # list entries
                values = filter(None, map(str.strip, value.split('; ')))
                if key == 'NA':  # convert abbreviations to TextWithLink
                    values = [authorship_dict.get(NA, TextWithLink(NA)) for NA in values]
                getattr(notes[-1], key).extend(values)

    # render Markdown in text
    for bibliography_entry in bibliography.entries:
        bibliography_entry.text = md.reset().convert(bibliography_entry.text)
    for note in notes:
        note.text = md.reset().convert(note.text)

    if getattr(bibliography, 'entries'):  # if a summary is present
        # AU, T, Y are mandatory
        missing = [key for key in ('AU', 'Y', 'T') if not getattr(bibliography, key)]
        if missing:
            raise UserWarning(f'missing mandatory keys "{", ".join(missing)}"')

        bibliography.AU = [md.reset().convert(AU)[len('<p>'):-len('</p>')] for AU in bibliography.AU]
        bibliography.T = md.reset().convert(bibliography.T)
        bibliography.P = md.reset().convert(bibliography.P)

        # generate REF from ID
        if not bibliography.REF:
            bibliography.REF = re.sub(r'\B([A-Z]|[0-9]{4}|&|-)', r' \1', bibliography.ID)  # add spaces
            # try:
            #     bibliography.REF = re.search('^.*[0-9]{4}', bibliography.ID).group(0)
            # except AttributeError:
            #     bibliography.REF = bibliography.ID

    else:  # no bibliography
        return None, notes

    return bibliography, notes


def fetch_dabi_data(page_generator):
    """Read .d files, generate database_bibl, database_notes, database_topics"""
    settings = page_generator.settings  # Pelican settings
    md = Markdown(**settings['MARKDOWN'])  # Markdown renderer
    md.preprocessors.deregister('meta')  # no metadata extraction
    path: Path = Path(settings.get('PATH')) / settings.get('DATABASES_PATH', '_databases/')
    bibl_dir: Path = path / 'Bibliography'
    if not bibl_dir.is_dir():
        logger.warning(f'Bibliography directory not found in {path}')
        return

    authorship_dict = parse_authorship(path / 'Authorship.txt')
    sites_abbr = {settings['SITE'][site].get('ABBR', ''): site for site in settings['SITE'] if site}
    database_bibl = []  # ? set()
    chapters = parse_chapters(path / 'Chapters/')
    errors = []

    for file in bibl_dir.glob('**/[!_]*'):  # all subdir recursively, ignoring file and folders starting with '_'
        if not file.is_file() or file.suffix[1:] not in file_extensions:
            continue
        try:
            # TODO: ? cache already parsed content with mtime
            file_id = file.stem
            if ' ' in file_id:
                if re.search(r' [A-z]{2}[0-9]{3}', file_id):  # ignore files with date in filename (old file version)
                    continue
                file_id = file_id.replace(' ', '')

            try:
                with file.open(mode='r', encoding='utf-8-sig') as handler:
                    bibliography, notes = parse_bibl(handler.read(), file_id, sites_abbr, authorship_dict, md)
                    if bibliography:
                        if len(bibliography.entries) > 1 or len(bibliography.entries[0].sites) > 1:
                            # duplicate entries for each site
                            for site in sites_abbr.values():
                                if any(site in entry.sites for entry in bibliography.entries):
                                    bibliography_copy = copy.copy(bibliography)
                                    bibliography_copy.site = site
                                    bibliography_copy.entries = [copy.deepcopy(e) for e in bibliography.entries if
                                                                 site in e.sites]
                                    database_bibl.append(bibliography_copy)
                        else:
                            bibliography.site = bibliography.entries[0].sites[0]
                            database_bibl.append(bibliography)

                    if notes:
                        # add notes to chapters
                        for note in notes:
                            chapter_ID = note.ID.split('.', 1)[0]
                            try:
                                chapter = next(chapter for chapter in chapters
                                               if chapter.ID == chapter_ID and chapter.site == note.site)
                                sub_chapter = next(sub_chapter for sub_chapter in chapter.sub_chapters
                                                   if sub_chapter.ID == note.ID)
                            except StopIteration:
                                raise UserWarning(f'note reference "{note.site}/{note.ID}" not found in chapters '
                                                  f'(line {note.line_number})')

                            sub_chapter.notes.append(note)

            except UnicodeError:
                # try to convert to utf-8 from Windows-1252
                with codecs.open(str(file), mode='r', encoding='cp1252') as f:
                    text = f.read()
                with codecs.open(str(file), mode='w', encoding='utf-8') as f:
                    f.write(text)

        except (UserWarning, OSError, UnicodeError) as error:
            error = f'"{file.name}": {error}.'
            logger.error(error)
            errors.append(error)

    # convert {B|N} links and add them to NR
    for bibliography in database_bibl:
        for bibliography_entry in bibliography.entries:
            bibliography_entry.text = linker(bibliography_entry.text, bibliography.ID, sites_abbr, database_bibl,
                                             chapters, errors, start_line=bibliography_entry.line_number)
    for chapter in chapters:
        for sub_chapter in chapter.sub_chapters:
            for note in sub_chapter.notes:
                add_to_NR = TextWithLink(note.ID, link=f'Notes/{note.ID.split(".", 1)[0].zfill(2)}.htm#{note.ID}')
                note.text = linker(note.text, note.file_ID, sites_abbr, database_bibl, chapters, errors,
                                   add_to_NR=add_to_NR, start_line=note.line_number)

            # sort notes by ND
            sub_chapter.notes.sort(key=lambda note: note.ND or datetime(1, 1, 1))

    # sort bibliography by ID and Y; W for last
    database_bibl.sort(key=lambda b: (b.W, locale.strxfrm(b.ID), locale.strxfrm(b.Y)))

    # generate topic index
    database_topics = []
    for bibliography in database_bibl:
        for entry in bibliography.entries:
            for TO in entry.TO:
                database_topics.append(Topic(TO=TO, section='Bibliography', text=bibliography.REF,
                                             link=f'bibl.htm#{bibliography.ID}', site=bibliography.site))
    for chapter in chapters:
        for sub_chapter in chapter.sub_chapters:
            for note in sub_chapter.notes:
                for TO in note.TO:
                    database_topics.append(Topic(TO=TO, section='Notes', text=note.ID,
                                                 link=f'Notes/{chapter.ID.zfill(2)}.htm#{note.ID}', site=note.site))

    # add databases and filters to context
    page_generator.context['database_bibl'] = database_bibl
    page_generator.context['chapters'] = chapters
    page_generator.context['database_topics'] = database_topics
    page_generator.context['errors'] = errors
    add_filters_to_context(page_generator)


def update_page(page_generator):
    """Update {B|N} links in content, save references in bibliography, save topics"""
    sites_abbr = {page_generator.settings['SITE'][site].get('ABBR', ''): site for site in
                  page_generator.settings['SITE']}
    database_bibl = page_generator.context['database_bibl']
    chapters = page_generator.context['chapters']
    database_topics = page_generator.context['database_topics']

    for page in page_generator.pages:
        # content.content is read-only, edit content._content
        if not page._content:
            continue
        page._content = linker(page._content, page.save_as, sites_abbr, database_bibl, chapters)

    # TODO: save TO in database_topics, ? how to choose Section
    database_topics.sort(key=lambda t: (locale.strxfrm(t.TO), locale.strxfrm(t.section), locale.strxfrm(t.text)))


def update_localcontext(page_generator, content):
    """Add page.site variable to templates, used for custom titles"""
    content.site = content.settings['SITE'].get(content.folder, content.settings['SITE']['DEFAULT'])
    return


def register():
    """Pelican plugin registration"""
    signals.page_generator_init.connect(fetch_dabi_data)  # read databases before reading pages
    signals.page_generator_finalized.connect(update_page)  # update all pages with bibl data
    signals.page_generator_write_page.connect(update_localcontext)


'''
def initialized(pelican):
    """Set custom Pelican settings."""
    DEFAULT_CONFIG.setdefault('DABI_...', True)
    pelican.settings.setdefault('DABI_...', True)

#signals.initialized.connect(initialized)
'''
