# coding=utf-8
"""
Licensed under WTFPL.
http://www.wtfpl.net/about/
"""
import logging
from logging import config
from logging.handlers import SysLogHandler, TimedRotatingFileHandler
from pathlib import Path
import socket


def _get_logging_dict(app_name):
    return {
        'version': 1,
        'formatters': {
            'logfile': {
                'format': '%(asctime)s [%(levelname)7s] | %(module)s : %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %Z'
            },
            'syslog': {
                'format': f'%(asctime)s [%(levelname)7s] | {socket.gethostname()} | %(module)s : %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %Z'
            },
            'simple': {
                'format': '%(asctime)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %Z'
            },
        },
        'handlers': {
            'sysout': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'loggers': {
            app_name: {
                'handlers': ['sysout'],
                'propagate': True,
                'level': 'DEBUG',
            }
        },
    }


class LsllLogger:
    """A logger without a StreamHandler on sysout and optionally a SysLogHandler or a TimedRotatingFileHandler"""

    def __init__(self, app_name, verbose, debug):
        self.logging_dict = _get_logging_dict(app_name)
        self.verbose = verbose
        self.debug = debug
        self._log_file = None
        self._syslog_host = None
        self._syslog_port = None
        self.level = logging.INFO if self.verbose else logging.WARNING

        if self.debug:
            self.level = logging.DEBUG
        logging.config.dictConfig(self.logging_dict)
        self.logger = logging.getLogger(app_name)
        self._sysout_handler = self.logger.handlers[0]
        self._logfile_handler = None
        self._syslog_handler = None

        self._update_sysout_formatter()
        self._update_sysout_level()

        level_name = logging.getLevelName(self.logger.getEffectiveLevel())
        self.logger.info(f"Logging activated with level {level_name}")

        level_name = logging.getLevelName(self._sysout_handler.level)
        self.logger.info(f"Sysout logging activated with level {level_name}")

    @property
    def log_file(self) -> Path:
        """
        Log file where to write. Logs are rotated every day, 15 backups are kept
        """
        return self._log_file

    @log_file.setter
    def log_file(self, value: Path):
        self._log_file = Path(value)
        if not self._logfile_handler:
            self._add_logfile_handler()
        else:
            self._update_logfile_handler()

    @property
    def syslog_host(self) -> str:
        """
        Sets syslog hostname where to send logs to.
        """
        return self._syslog_host

    @syslog_host.setter
    def syslog_host(self, value: str):
        self._syslog_host = value
        if not self._syslog_handler:
            self._add_syslog_handler()
        else:
            self._update_syslog_handler()

    @property
    def syslog_port(self) -> int:
        """
        Sets syslog port where to send logs to.
        """
        return self._syslog_port

    @syslog_port.setter
    def syslog_port(self, value: int):
        self._syslog_port = value
        if self._syslog_handler:
            self._update_syslog_handler()

    def get_logger(self) -> logging.Logger:
        """
        get logger object
        """
        return self.logger

    def _get_formatter_from_dict(self, format_name):
        fmt_from_dict = self.logging_dict['formatters'][format_name]
        return logging.Formatter(fmt=fmt_from_dict['format'], datefmt=fmt_from_dict['datefmt'])

    def _update_sysout_formatter(self):
        sysout_fmt_name = 'logfile' if (self.verbose or self.debug) else 'simple'
        sysout_fmt = self._get_formatter_from_dict(sysout_fmt_name)
        self._sysout_handler.setFormatter(sysout_fmt)

    def _update_sysout_level(self):
        self._sysout_handler.level = self.level

    def _add_syslog_handler(self):
        """Adds a SysLogHandler, with minimum logging set to WARNING and a 'verbose' format"""
        self._syslog_handler = SysLogHandler(address=(self.syslog_host, self.syslog_port))
        self._syslog_handler.setLevel(logging.WARNING)
        self._syslog_handler.setFormatter(self._get_formatter_from_dict('syslog'))
        self.logger.addHandler(self._syslog_handler)
        level_name = logging.getLevelName(self._syslog_handler.level)
        self.logger.debug(f"Added logging to syslog on {self.syslog_host}:{self.syslog_port} with level {level_name}")

    def _update_syslog_handler(self):
        self._syslog_handler.address = (self.syslog_host, self.syslog_port)

    def _add_logfile_handler(self):
        """Adds a TimedRotatingFileHandler, with minimum logging set to DEBUG and a 'verbose' format"""
        self._logfile_handler = TimedRotatingFileHandler(filename=self.log_file, when='D', backupCount=15)
        self._logfile_handler.setLevel(logging.DEBUG)
        self._logfile_handler.setFormatter(self._get_formatter_from_dict('logfile'))
        self.logger.addHandler(self._logfile_handler)
        level_name = logging.getLevelName(self._logfile_handler.level)
        self.logger.debug(f"Added logging to {self.log_file} with level  {level_name}")

    def _update_logfile_handler(self):
        self._logfile_handler.baseFilename = self.log_file
