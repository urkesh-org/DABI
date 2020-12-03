import unittest

from DABI_databases.DABI_databases import parse_bibl


class TestDatabase(unittest.TestCase):
    
    file_id = ''
    sites_abbr = {'Lg': 'Akk-lg', 'A': 'Mes-art', 'L': 'Mes-lit', 'P': 'Mes-pol', 'R': 'Mes-rel'}
    settings = {'MARKDOWN':{
        'extension_configs': {'markdown.extensions.extra': {}, 'markdown.extensions.meta': {}, 'markdown_meta': {},
                              'markdown_comments': {}, 'markdown.extensions.smarty': {'smart_angled_quotes': True}},
        'output_format': 'html5',
        'extensions': ['markdown.extensions.extra', 'markdown.extensions.meta', 'markdown_meta', 'markdown_comments',
                       'markdown.extensions.smarty']}}
    authorship_dict = dict()
    
    def test_parse_bibl(self):
        text = """\
AU name, surname; other author
Y 2000
T "Title"
P publication

@@@L
SA summary author; other summary author
SD January 2020
TO topic; other topic; etc

Summary.
        """

        bibliography, notes = parse_bibl(text, self.file_id, self.sites_abbr, self.settings, self.authorship_dict)
        
        self.assertIn('other author', bibliography.AU)


if __name__ == '__main__':
    unittest.main()
