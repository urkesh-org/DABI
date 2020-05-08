# Special logger that writes to sys.stdout using colors and saves to logfile
# Usage: logger = logging.getLogger(__name__)

import sys
import logging
import colorama


class BaseFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        FORMAT = '%(customlevelname)s%(message)s'
        super().__init__(fmt=FORMAT, datefmt=datefmt)

    def format(self, record):
        record.__dict__['customlevelname'] = self._get_levelname(record.levelname)
        
        if not hasattr(record, '_edited') and record.levelname != 'PRINT':
            record._edited = True
            # format multiline messages 'nicely' to make it clear they are together
            record.msg = record.msg.replace('\n', '\n  | ')
            record.args = tuple(arg.replace('\n', '\n  | ') if isinstance(arg, str) else
                                arg for arg in record.args)
            
        return super().format(record)

    def formatException(self, ei):
        """prefix traceback info for better representation"""
        s = super().formatException(ei)
        # fancy format traceback
        s = '\n'.join('  | ' + line for line in s.splitlines())
        # separate the traceback from the preceding lines
        s = '  |___\n{}'.format(s)
        return s

    def _get_levelname(self, name):
        """NOOP: overridden by subclasses"""
        return name


class TextFormatter(BaseFormatter):
    def _get_levelname(self, name):
        if name == 'INFO':
            return '-> '
        elif name == 'PRINT':
            return ''
        else:
            return name + ': '


class ColorFormatter(BaseFormatter):
    FORMATS = {'CRITICAL': colorama.Back.RED,
               'ERROR': colorama.Fore.RED,
               'WARNING': colorama.Fore.YELLOW,
               'PRINT': '',
               'INFO': colorama.Fore.CYAN,  # colorama.Fore.GREEN
               'DEBUG': colorama.Back.LIGHTWHITE_EX}

    def _get_levelname(self, name):
        if name == 'INFO':
            fmt = '{0}->{2} '
        elif name == 'PRINT':
            fmt = ''
        else:
            fmt = '{0}{1}{2}: '
        return fmt.format(self.FORMATS.get(name, ''), name, colorama.Style.RESET_ALL)


def init_logging(logfile, debug=False):
    """Customize log and send it to console and logfile"""
    
    logger = logging.getLogger()  # root logger
    if debug:
        logger.setLevel(logging.INFO)
    logging.addLevelName(35, 'PRINT')
    #logging.addLevelName(logging.ERROR, '[-]')
    colorama.init()

    # console handler
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)
    
    # file handler
    file_handler = logging.FileHandler(logfile, mode='a')
    file_handler.setFormatter(TextFormatter())
    logger.addHandler(file_handler)

