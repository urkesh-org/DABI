#!/usr/bin/env python3
#
# DABI - Digital Analysis of Bibliographical Information
# Author: bF
# Usage: cd website_root_directory; DABI.py
#

import sys
from pathlib import Path
import time
from datetime import datetime
import logging
import configparser
import copy
from watchdog.observers import Observer  # file monitoring
from watchdog.events import PatternMatchingEventHandler
import pelican

import pelicanconf
from log import init_logging


__version__ = '1.0'
logger = logging.getLogger(__name__)

SETTINGS_FILE = '_DABI_config.ini'
LOG_FILE = '_DABI_log.txt'


def get_settings(settings_file):
    """import configuration from config_file"""

    settings = {}
    if not Path(settings_file).is_file():
        logger.warning(f'No config file found, using default configuration.')
    else:
        try:
            ini_parser = configparser.ConfigParser()
            ini_parser.read(settings_file)
            for key in ini_parser['DABI']:
                settings.update({key.upper(): ini_parser.get('DABI', key)})
            
            logger.info(f'Importing configuration: {settings.get("SITENAME")}.')
            
        except configparser.Error as err:
            raise UserWarning(f'Error in config {settings_file}: {err}.')

    settings = dict(copy.deepcopy(pelican.settings.DEFAULT_CONFIG), **settings)
    settings = pelican.settings.configure_settings(settings)

    # custom settings configurations
    if isinstance(settings.get('BOOKS'), str):
        settings['BOOKS'] = settings['BOOKS'].split(', ')
    # TODO: set custom default template
    
    return settings


class FileChangedHandler(PatternMatchingEventHandler):
    new_run = True

    def on_any_event(self, event):
        if FileChangedHandler.new_run:
            return
        
        # don't update on modified static file (hardlink)
        if not any(event.src_path.endswith(ext) for ext in ('.md', '.d', '.html', '.ini')):
            # ? and event.event_type == 'modified'
            return

        logger.info(f'File(s) changed ({str(datetime.now().astimezone().isoformat(timespec="seconds"))} '
                    f'{event.event_type} {event.src_path}). Re-generating.')
        FileChangedHandler.new_run = True


def main():
    """run custom pelican with autoreload"""
    
    init_logging(LOG_FILE, debug=True)  # TODO: read DEBUG from config
    
    print(f'''\
---------------------------------------------------------------------
 DABI: Digital Analysis of Bibliographical Information  (v{__version__})
---------------------------------------------------------------------

 Build website from templates and local databases.
 Keep the program open to auto-reload pages.
''')
    logger.debug('Python version: %s', sys.version.split()[0])

    # set custom settings
    custom_settings = pelican.settings.get_settings_from_module(pelicanconf)
    pelican.settings.DEFAULT_CONFIG.update(custom_settings)
    last_mtime_settings = 0

    # auto-reload
    my_handler = FileChangedHandler(patterns=['*'], ignore_patterns=['*/_website/*', LOG_FILE], ignore_directories=True,
                                    case_sensitive=False)
    observer = Observer()
    observer.schedule(my_handler, '.', recursive=True)
    observer.start()
    try:
        while True:
            # run pelican
            try:
                if FileChangedHandler.new_run:
                    FileChangedHandler.new_run = False

                    # new log
                    for handler in logger.parent.handlers:
                        handler.close()
                    logger.log(35, f'--- RUN at {str(datetime.now().astimezone().isoformat(timespec="seconds"))}')

                    try:
                        mtime_settings = Path(SETTINGS_FILE).stat().st_mtime
                    except FileNotFoundError:
                        mtime_settings = 1
                    if mtime_settings > last_mtime_settings:  # updates settings and build class
                        last_mtime_settings = mtime_settings
                        settings = get_settings(SETTINGS_FILE)
                        pelican_cls = pelican.Pelican(settings)
                    
                    settings['MONTH'] = datetime.now().strftime('%B %Y').title()
                    settings['YEAR'] = datetime.now().strftime("%Y")
                    pelican_cls.run()
                    # logger.log(35, '--- RUN Completed.')
                    
            except KeyboardInterrupt:
                raise
            except UserWarning as err:
                logger.critical(err)
            except Exception as err:  # logs any error with Traceback
                logger.critical(err, exc_info=True)

            finally:
                time.sleep(.5)  # sleep to avoid cpu load

    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    logger.warning('Program ended prematurely. Press ENTER to quit.')
    logging.shutdown()
    input()
    sys.exit(1)
    
    # TODO?: convert to UTF automatically
    # TODO: update db only if *.d modified
    # TODO: 404, sub-Bibl redirect to Bibl, anchor in Bibl
    
    '''
    if len(sys.argv) > 1:
    def livereload(c):
        """Automatically reload browser tab upon file modification."""
        from livereload import Server
        build(c)
        server = Server()
        # Watch the base settings file
        server.watch(CONFIG['settings_base'], lambda: build(c))
        # Watch content source files
        content_file_extensions = ['.md', '.rst']
        for extension in content_file_extensions:
            content_blob = '{0}/**/*{1}'.format(SETTINGS['PATH'], extension)
            server.watch(content_blob, lambda: build(c))
        # Watch the theme's templates and static assets
        theme_path = SETTINGS['THEME']
        server.watch('{}/templates/*.html'.format(theme_path), lambda: build(c))
        static_file_extensions = ['.css', '.js']
        for extension in static_file_extensions:
            static_file = '{0}/static/**/*{1}'.format(theme_path, extension)
            server.watch(static_file, lambda: build(c))
        # Serve output path on configured port
        server.serve(port=CONFIG['port'], root=CONFIG['deploy_path'])
    '''


if __name__ == '__main__':
    main()
