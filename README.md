# pap_logger

## A 'prêt-à-porter' logger with a sysout StreamHandler and optionally, a SysLogHandler and/or a TimedRotatingFileHandler

### Usage

```python
pap = PaPLogger(app_name="your_application_name")
```


Logging level, syslog server address and log file filename can easily be changed at runtime.
```python
pap.level = logging.INFO
# Setting a log file path will activate the TimedRotatingFileHandler
pap.log_file = Path("/var/log/new_log_file_name")
# A string works too
pap.log_file = "/var/log/new_log_file_name"
# Setting it to None will remove the TimedRotatingFileHandler
pap.log_file = None
# Setting a hostname will activate the SysLogHandler
pap.syslog_host = "your_syslog_server"
# Setting it to None will remove the SysLogHandler
pap.syslog_host = None
```
The log file can be prefixed by the hostname for cases where the machine where logs are created is necessary.

When activated, the hostname is also written in the logs.
```python
pap.logfile_with_hostname = True
```
The sysout StreamHandler format changes with the logging level; from simple to WARNING or lower, to verbose when higher.

This can be overriden with the verbose value.
```python
pap.verbose = True
```

The SysLogHandler will only log records with level WARNING or above and always in a verbose format.

The TimedRotatingFileHandler is rotating by default every day, and 15 days of logs are kept.

These values can be changed when instantiating LsslLogger:
```python
pap = PaPLogger(app_name="your_application_name", when='D', backup_count=15)
```

More detailed usage examples are given in the function _pap_logger_example.

Please refer to the source code.

### Compatibility information

This module will only run with Python 3.5 and ulterior due to its use of f-strings.

It has only been tested under GNU/Linux.