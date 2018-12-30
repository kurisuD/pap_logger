# coding=utf-8
"""
Licensed under WTFPL.
http://www.wtfpl.net/about/
"""
import logging
from logging import config
from logging.handlers import SysLogHandler, TimedRotatingFileHandler
from pathlib import Path
from socket import gethostname, error as socket_error
from datetime import datetime
from pytz import reference

__example_name__ = "pap_logger_example"


def _get_timezone():
    return reference.LocalTimezone().tzname(datetime.now())


def _get_logging_dict(app_name):
    tz = _get_timezone()
    base_fmt = "%(module)s : %(message)s"
    prefix_log_file_fmt = f'%(asctime)s.%(msecs)03d {tz} | [%(levelname)8s]'
    base_ts = '%Y-%m-%d %H:%M:%S'
    return {
        'version': 1,
        'formatters': {
            'logfile_with_host': {
                'format': f'{prefix_log_file_fmt} | {gethostname()} | {base_fmt}',
                'datefmt': base_ts
            },
            'logfile': {
                'format': f'{prefix_log_file_fmt} | {base_fmt}',
                'datefmt': base_ts
            },
            'syslog': {
                'format': f'[%(levelname)8s] | {base_fmt}',
                'datefmt': base_ts
            },
            'simple': {
                'format': "%(asctime)s : %(message)s",
                'datefmt': f'{base_ts} %Z'
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
                'level': 'WARNING',
            }
        },
    }


class PaPLogger:
    """A logger with a StreamHandler on sysout and optionally a SysLogHandler and/or a TimedRotatingFileHandler"""

    def __init__(self, app_name, level=None, verbose_fmt=False, logfile_with_hostname=False, when='D', backup_count=15):
        self.logging_dict = _get_logging_dict(app_name)
        logging.config.dictConfig(self.logging_dict)
        self.logger = logging.getLogger(app_name)
        if level:
            self.level = level
        self._verbose_fmt = verbose_fmt
        self._logfile_with_hostname = logfile_with_hostname
        self._when = when
        self._backup_count = backup_count
        self._log_file = None
        self._syslog_host = None
        self._syslog_port = 514
        self._level = logging.WARNING

        self._sysout_handler = self.logger.handlers[0]
        self._logfile_handler = None
        self._syslog_handler = None

        self._update_sysout_formatter()
        self._update_logger_level()
        self._update_sysout_level()

    def _update_logger_level(self):
        self.logger.setLevel(self.level)
        level_name = logging.getLevelName(self.logger.getEffectiveLevel())
        self.logger.info(f"Logging with global level {level_name}")

    @property
    def level(self) -> int:
        """
        Updates logging level at run time
        """
        return self._level

    @level.setter
    def level(self, value: int):
        self._level = value
        self._update_sysout_formatter()
        self._update_logger_level()
        self._update_sysout_level()
        if self._syslog_handler:
            self._update_syslog_handler()
        if self._logfile_handler:
            self._update_logfile_handler()

    @property
    def verbose_fmt(self) -> bool:
        """
        Updates verbosity at run time
        """
        return self._verbose_fmt

    @verbose_fmt.setter
    def verbose_fmt(self, value: bool):
        self._verbose_fmt = value
        self._update_sysout_formatter()

    @property
    def logfile_with_hostname(self) -> bool:
        """
        Adds the current hostname to logfile content and filename.
        """
        return self._logfile_with_hostname

    @logfile_with_hostname.setter
    def logfile_with_hostname(self, value: bool):
        if value != self.logfile_with_hostname:
            if not self.logfile_with_hostname and value:
                self.log_file = self.log_file.parent / f"{gethostname()}_{self.log_file.name}"
            elif self.logfile_with_hostname and not value:
                self.log_file = self.log_file.parent / self.log_file.name.replace(f"{gethostname()}_", "")
            self._logfile_with_hostname = value
            self._update_logfile_formatter()

    @property
    def log_file(self) -> Path:
        """
        Log file where to write. Logs are rotated every day, 15 backups are kept
        """
        return self._log_file

    @log_file.setter
    def log_file(self, value: [Path, str]):
        if value is None:
            self._remove_logfile_handler()
            self._log_file = value
            return

        if self.log_file:
            self.logger.debug(f"Changing log file from {self.log_file} to {value}")

        if isinstance(value, str):
            self._log_file = Path(value)
        else:
            self._log_file = value

        try:
            if not self._log_file.parent.exists():
                self._log_file.parent.mkdir(parents=True)

            if not self._logfile_handler:
                self._add_logfile_handler()
            else:
                self._update_logfile_handler()
        except PermissionError:
            self.logger.error(f"Could not create {self.log_file.name} in {self.log_file.parent}: Permission Denied")

    @property
    def syslog_host(self) -> str:
        """
        Sets syslog hostname where to send logs to.
        """
        return self._syslog_host

    @syslog_host.setter
    def syslog_host(self, value: str):
        if value is None:
            self._remove_syslog_handler()
            self._syslog_host = value
            return

        self._syslog_host = value
        try:
            if not self._syslog_handler:
                self._add_syslog_handler()
            else:
                self._update_syslog_handler()
        except socket_error:
            self.logger.error(f"Could not connect to syslog on {self.syslog_host}:{self.syslog_port}")

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
        sysout_fmt_name = 'logfile' if (self.verbose_fmt or self.level <= logging.WARNING) else 'simple'
        sysout_fmt = self._get_formatter_from_dict(sysout_fmt_name)
        self._sysout_handler.setFormatter(sysout_fmt)
        self._sysout_handler.close()

    def _update_sysout_level(self):
        self._sysout_handler.setLevel(self.level)
        level_name = logging.getLevelName(self._sysout_handler.level)
        self.logger.info(f"Sysout logging with level {level_name}")

    def _add_syslog_handler(self):
        """Adds a SysLogHandler, with minimum logging set to WARNING and a 'verbose' format"""
        self._syslog_handler = SysLogHandler(address=(self.syslog_host, self.syslog_port))
        self._syslog_handler.setLevel(logging.WARNING)
        self._syslog_handler.setFormatter(self._get_formatter_from_dict('syslog'))
        self.logger.addHandler(self._syslog_handler)
        level_name = logging.getLevelName(self._syslog_handler.level)
        self.logger.debug(f"Added SysLogHandler to {self.syslog_host}:{self.syslog_port} with level {level_name}.")

    def _update_syslog_handler(self):
        if self._syslog_handler:
            self._syslog_handler.address = (self.syslog_host, self.syslog_port)

    def _remove_syslog_handler(self):
        if self._syslog_handler:
            self.logger.debug("Removing SysLogHandler")
            self.logger.removeHandler(self._syslog_handler)

    def _add_logfile_handler(self):
        """Adds a TimedRotatingFileHandler, with minimum logging set to DEBUG and a 'verbose' format"""
        try:
            self._logfile_handler = TimedRotatingFileHandler(filename=self.log_file, when=self._when,
                                                             backupCount=self._backup_count)
        except ValueError as e:
            self.logger.error(f"TimedRotatingFileHandler : {e}")
            return

        self._logfile_handler.setLevel(logging.DEBUG)
        self._update_logfile_formatter()
        self.logger.addHandler(self._logfile_handler)
        level_name = logging.getLevelName(self._logfile_handler.level)
        self.logger.debug(f"Added TimedRotatingFileHandler to {self.log_file} with level {level_name}.")
        self.logger.debug(f"Log rotates every {self._when} and keeps {self._backup_count} logs.")

    def _update_logfile_formatter(self):
        logfile_fmt_name = 'logfile_with_host' if self.logfile_with_hostname else 'logfile'
        logfile_fmt = self._get_formatter_from_dict(logfile_fmt_name)
        self._logfile_handler.setFormatter(logfile_fmt)
        self._logfile_handler.close()

    def _update_logfile_handler(self):
        if self._logfile_handler:
            self._logfile_handler.close()
            self._logfile_handler.baseFilename = self.log_file

    def _remove_logfile_handler(self):
        if self._logfile_handler:
            self.logger.debug("Removing TimedRotatingFileHandler")
            self.logger.removeHandler(self._logfile_handler)


def _pap_logger_example(verbose_fmt: bool, log_path: Path, syslog_host: str):
    logging.raiseExceptions = False

    lssl = PaPLogger(app_name="lssl_logger_example", verbose_fmt=verbose_fmt)
    logger = lssl.get_logger()

    if log_path and log_path.exists() and not log_path.is_dir():
        logger.critical(f"{log_path} is not a directory")
        return

    syslog_host = "hostname_with_a_syslog_listening" if not syslog_host else syslog_host

    def _log_in_all_levels(msg):
        logger.debug(msg)
        logger.info(msg)
        logger.warning(msg)
        logger.error(msg)
        logger.critical(msg)

    for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        lssl.level = level
        lssl.log_file = log_path / f"{__example_name__}.log"
        lssl.syslog_host = syslog_host
        lssl.verbose_fmt = False
        _log_in_all_levels("")
        _log_in_all_levels(f"LEVEL SET TO {logging.getLevelName(level)} ({level})")
        _log_in_all_levels(f"Hello from {__example_name__}")
        lssl.logfile_with_hostname = True
        _log_in_all_levels("with hostname")
        lssl.logfile_with_hostname = False
        _log_in_all_levels("without hostname")
        lssl.syslog_host = "this_is_anunknown"
        _log_in_all_levels("unknown Syslog")
        lssl.syslog_host = None
        _log_in_all_levels("remove Syslog")
        lssl.log_file = None
        _log_in_all_levels("remove log file")
        if level >= logging.WARNING:
            lssl.verbose_fmt = True
            _log_in_all_levels("verbose")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__example_name__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose_fmt", help="Verbose formatting.", action="store_true")
    parser.add_argument("-p", "--log_path", help="Path to log directory.", type=Path,
                        default=Path("/tmp") / __example_name__)
    parser.add_argument("-sh", "--syslog_host", help="Syslog hostname.", type=str)

    args = parser.parse_args()
    _pap_logger_example(verbose_fmt=args.verbose_fmt, syslog_host=args.syslog_host, log_path=args.log_path)
