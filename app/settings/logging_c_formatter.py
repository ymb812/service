import logging
from colorama import Fore, Back


class CustomFormatter(logging.Formatter):
    blue = Fore.BLUE
    green = Fore.GREEN
    cyan = Fore.CYAN
    yellow = Fore.YELLOW
    red = Fore.RED
    fatal = Fore.WHITE + Back.RED
    reset = Fore.RESET + Back.RESET
    log_format = '  File: %(name)s.py - Date: %(asctime)s - Msg: %(message)s'

    FORMATS = {
        logging.DEBUG: blue + 'DEBUG:  ' + reset + log_format + reset,
        logging.INFO: green + 'INFO:   ' + reset + log_format + reset,
        logging.WARNING: yellow + 'WARNING:' + reset + log_format + reset,
        logging.ERROR: red + 'ERROR:  ' + reset + log_format + reset,
        logging.CRITICAL: fatal + 'FATAL:  ' + reset + log_format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomFormatterNoColor(CustomFormatter):
    FORMATS = {
        logging.DEBUG: 'DEBUG:  ' + CustomFormatter.log_format,
        logging.INFO:  'INFO:   ' + CustomFormatter.log_format,
        logging.WARNING: 'WARNING:' + CustomFormatter.log_format,
        logging.ERROR: 'ERROR:  ' + CustomFormatter.log_format,
        logging.CRITICAL: 'FATAL:  ' + CustomFormatter.log_format
    }
