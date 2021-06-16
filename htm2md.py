from DABI import get_settings, SETTINGS_FILE
from pathlib import Path
import shutil
from typing import Dict, List
import re
import copy
from distutils.file_util import copy_file
import logging
from log import init_logging

logger = logging.getLogger(__name__)
file_name = Path(__file__).stem
LOG_FILE = f'_{file_name}.log'

#create directory '_new_md' under the examples folder to contain the generated templates and .md files
#this script will lookup the files with frameset's and generate template from the left & content .md from the right
#the master template will become a new one with the name 'base_2.html'
NEW_MD = '_new_md'

#files with frameset's
LEFT_FRAME_REGEX = re.compile(r'\s+<frame\s{1}name="(?P<name>([a-zA-Z0-9.])+)"(\s{1}noresize)*\s{1}src="(?P<src>([a-zA-Z0-9._-])+)".*')

#extract the Title value for the .md file from html
TITLE_REGEX = re.compile(r'<(TITLE|title)>(?P<_T_>(.)+)</(TITLE|title)>')

#isolate the <body> content for templates and content files
BODY_REGEX = re.compile(r'<(body|BODY)\s{1}background="parchment.jpg"(\s{1}>|>)(?P<_body_>(.)+)(</body>|</html>)?(.)*', re.DOTALL)

def generate():
    init_logging(LOG_FILE)
    logger.info('generation .md files and templates..')
    path = Path('')
    
    new_md_path = path / NEW_MD # the new generated files path
    if new_md_path.is_dir():
        shutil.rmtree(new_md_path) # recreate the directory
    new_md_path.mkdir()

    original_base_path = path / "_templates/base_2.html"

    new_template_path = new_md_path / "_templates"
    new_template_path.mkdir()
    new_base_path = new_template_path / "base_2.html"

    try:
        copy_file(original_base_path.absolute().as_posix(), new_base_path.absolute().as_posix())
    except Exception as e:
        logger.error(e)
    settings = get_settings(SETTINGS_FILE) # lookup the site directories

    site_paths: List = [path / dir_name for dir_name in list(filter(lambda k: (path / k).is_dir(), settings['SITE'].keys()))]
    for site_path in site_paths:
        md_counterpart = new_md_path / site_path.name
        
        if md_counterpart.is_dir():
            md_counterpart.r.rmdir()
        md_counterpart.mkdir()
        for file in site_path.glob('*.HTM'):
            file_name: str = file.name
            if file_name.find(' ') == -1: # exclude htm files where names contains spaces
                try:
                    leftbar_file: str = '' # left iframe source page
                    content_file: str = '' # right content source page
                    with file.open(mode='r', encoding='utf-8') as handler:
                        text = handler.read()
                        for line_number, line in enumerate(text.splitlines(), 1):
                            match: re.Match = LEFT_FRAME_REGEX.fullmatch(line)
                            if match:
                                src = match.group('src')
                                name = match.group('name')

                                if name == 'leftSubFrame':
                                    leftbar_file = src
                                elif name == 'rightSubFrame':
                                    content_file = src

                    if leftbar_file:
                        is_content_md = False
                        template_file_path: Path = new_template_path / leftbar_file
                        if not template_file_path.is_file():
                            # the condition means that the template (i.e. left panel page) will not be
                            #  created again
                            original_src_path: Path = site_path / leftbar_file
                            with original_src_path.open(mode='r', encoding='utf-8') as src_handler:
                                src_content = src_handler.read()
                                se = re.search(BODY_REGEX, src_content)
                                g = se.group("_body_")
                                body = g
                                #make the generated template extend the master template
                                template_body = f'{{% extends "base_2.html" %}}\n{{% block main_left -%}}\n{body}\n{{%- endblock %}}\n{{% block main -%}}\n{{{{ page.content }}}}\n{{%- endblock %}}'
                                with template_file_path.open(mode='w', encoding='utf-8') as template_handler:
                                    template_handler.write(template_body)
                        original_content_path: Path = site_path / content_file
                        md_content_file: str = content_file.replace('.htm', '.md').replace('.HTM', '.md')
                        if not original_content_path.is_file() and not original_content_path.is_dir():
                            # the file is already a .md file, hence the src=xxx.htm file does not exist
                            original_content_path: Path = site_path / md_content_file
                            is_content_md = True
                        else:
                            # keep the file, here there is a problem that needs to be fixed for the
                            #  exixting .md files, since they are already linked to a chaine of templates
                            #  note tha the .md file can contain html markup
                            pass
                        
                        target_file_path: Path = md_counterpart / md_content_file
                        if not target_file_path.is_file():
                            # here there must be some more case study, if the file is referenced by more
                            #  than one frameset page
                            # currently only one reference is supported, hence the condition not to pre-exist
                            if original_content_path.is_file():
                                with original_content_path.open(mode='r', encoding='utf-8') as src_handler:
                                    src_content = src_handler.read()
                                    body = src_content
                                    if not is_content_md:
                                        _T_: str = None
                                        try:
                                            se = re.search(BODY_REGEX, src_content)
                                            g = se.group("_body_")
                                            _T_ = re.search(TITLE_REGEX, src_content).group('_T_')
                                            body = g
                                        except Exception as e1:
                                            # the file can be created with empty content if the original sourse
                                            #  is corrupted, or even empty
                                            logger.error(e1)
                                        template_name = leftbar_file.split('.')[0]
                                        title_line = f'T {_T_}\n' if _T_ else ''
                                        # further attributed must be extracted manually after generating the .md file
                                        body = f'HTML {template_name}\n{title_line}\n{body}'
                                    with target_file_path.open(mode='w', encoding='utf-8') as target_handler:
                                        target_handler.write(body)
                            

                except Exception as e2:
                    logger.error(e2)   

if __name__ == '__main__':
    generate()