"""
Meta Data Extension for Python-Markdown
edited from <https://Python-Markdown.github.io/extensions/meta_data>
"""

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import logging

log = logging.getLogger('MARKDOWN')
#logger = logging.getLogger(__name__)

# Global Vars
META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+)\s\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')


class MetaExtension(Extension):
    """ Meta-Data extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Add MetaPreprocessor to Markdown instance. """
        md.registerExtension(self)
        self.md = md
        md.preprocessors.register(MetaPreprocessor(md), 'meta', 27)

    def reset(self):
        self.md.Meta = {}


class MetaPreprocessor(Preprocessor):
    """ Get Meta-Data. """

    def run(self, lines):
        """ Parse Meta-Data and store in Markdown.Meta. """
        meta = {}
        key = None
        if lines and BEGIN_RE.match(lines[0]):
            lines.pop(0)
        while lines:
            line = lines.pop(0)
            m1 = META_RE.match(line)
            if line.strip() == '' or END_RE.match(line):
                break  # blank line or end of YAML header - done
            if m1:
                key = m1.group('key').lower().strip()
                value = m1.group('value').strip()
                try:
                    meta[key].append(value)
                except KeyError:
                    meta[key] = [value]
            else:
                m2 = META_MORE_RE.match(line)
                if m2 and key:
                    # Add another line to existing key
                    meta[key].append(m2.group('value').strip())
                else:
                    lines.insert(0, line)
                    break  # no meta data - done
        if not meta.get('title') and meta.get('t'):
            meta['title'] = meta['t']
        if not meta.get('date') and meta.get('d'):
            meta['date'] = meta['d']
        if not meta.get('template') and meta.get('html'):
            meta['template'] = meta['html']
        self.md.Meta = meta
        return lines


def makeExtension(**kwargs):  # pragma: no cover
    return MetaExtension(**kwargs)
