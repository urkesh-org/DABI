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
LOG_FILE = '_DABI.log'


def get_settings(settings_file):
    """import configuration from config_file"""

    settings = {}
    if not Path(settings_file).is_file():
        logger.warning(f'No config file found, using default configuration.')
    else:
        try:
            ini_parser = configparser.ConfigParser()
            ini_parser.optionxform = lambda option: option  # keep case-sensitive
            ini_parser.read(settings_file)
            settings.update(ini_parser.items('DEFAULT'))

            # each section is the path of a custom site settings
            settings.update({'SITE': dict()})
            for section in ini_parser:
                settings['SITE'].update({section: dict(ini_parser.items(section))})

            # print more information if "DEBUG" in config
            if 'DEBUG' in ini_parser['DEFAULT']:
                logger.parent.setLevel(logging.DEBUG)
            else:
                logger.parent.setLevel(logging.INFO)
            
            logger.info(f'Importing configuration for "{settings.get("SITENAME")}".')
            
        except configparser.Error as err:
            raise UserWarning(f'Error in config {settings_file}: {err}.')

    settings = dict(copy.deepcopy(pelican.settings.DEFAULT_CONFIG), **settings)
    settings = pelican.settings.configure_settings(settings)
    
    return settings


class FileChangedHandler(PatternMatchingEventHandler):
    new_run = True

    def on_any_event(self, event):
        if FileChangedHandler.new_run:
            return
        
        # don't update on modified static file (hardlink)
        if event.event_type == 'modified' and not event.src_path.endswith(('.md', '.d', '.html', '.ini')):
            return

        logger.info(f'File(s) changed ({event.event_type} "{event.src_path}" at '
                    f'{str(datetime.now().astimezone().isoformat(timespec="seconds"))}). Re-generating.')
        FileChangedHandler.new_run = True


def main():
    """run custom pelican with autoreload"""
    
    init_logging(LOG_FILE)
    
    print(f'''\
---------------------------------------------------------------------
 DABI: Digital Analysis of Bibliographical Information  (v{__version__})
---------------------------------------------------------------------

 Build website from templates and local databases.
 Pages will be auto-regenerated while the program is running.
''')

    # set custom pelican settings
    custom_settings = pelican.settings.get_settings_from_module(pelicanconf)
    pelican.settings.DEFAULT_CONFIG.update(custom_settings)
    last_mtime_settings = 0

    # auto-reload observer
    my_handler = FileChangedHandler(patterns=['*'], ignore_patterns=['*/_website/*', LOG_FILE, '*/*.filepart'],
                                    ignore_directories=True, case_sensitive=False)
    observer = Observer()
    observer.schedule(my_handler, '.', recursive=True)
    observer.start()
    try:
        while True:
            try:
                if FileChangedHandler.new_run:
                    FileChangedHandler.new_run = False

                    # new log
                    for handler in logger.parent.handlers:
                        handler.close()

                    try:
                        mtime_settings = Path(SETTINGS_FILE).stat().st_mtime
                    except FileNotFoundError:
                        mtime_settings = 1
                    if mtime_settings > last_mtime_settings:  # update settings and build pelican class
                        last_mtime_settings = mtime_settings
                        settings = get_settings(SETTINGS_FILE)
                        pelican_cls = pelican.Pelican(settings)
                    
                    settings['MONTH'] = datetime.now().strftime('%B %Y').title()
                    settings['YEAR'] = datetime.now().strftime("%Y")
                    pelican_cls.run()  # update all pages
                    logger.log(35, f'Done: Run completed at {str(datetime.now().astimezone().isoformat(timespec="seconds"))}.\n')
                    
            except KeyboardInterrupt:
                raise
            except UserWarning as err:
                logger.critical(err)
            except FileNotFoundError as err:
                logger.debug(f'FileNotFoundError exception: {err}')
            except Exception as err:  # logs any error with Traceback
                logger.critical(err, exc_info=True)

            finally:
                time.sleep(.5)  # sleep to avoid cpu load

    except Exception as err:
        logger.warning(f'Program ended prematurely: {err}')
    except:
        logger.info('Terminating program.')
    observer.stop()
    observer.join()
    logging.shutdown()
    sys.exit(1)


if __name__ == '__main__':
    main()
