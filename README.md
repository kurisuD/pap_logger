# pap_logger

## A 'prêt-à-porter' logger with a sysout StreamHandler and optionally, a SysLogHandler ∥ a TimedRotatingFileHandler

### Usage
```python
from pap_logger import PaPLogger
pap = PaPLogger()
```

Calling PaPLogger initialize the logging module root logger.

You can access the root logger via the logger property, and can as well log directly using the logging functions.

The logging level can be changed at runtime by setting the PaPLogger level property.

```python
from pap_logger import *
pap = PaPLogger()
pap.logger.info("Hello from pap logger")
pap.logger.warning("Default level is WARNING")
pap.level = INFO
pap.logger.info("This in an informational Hello from pap logger")
# 2019-01-03 18:28:14.767 JST : Default level is WARNING
# 2019-01-03 18:28:14.767 JST [    INFO] <stdin> : This in an informational Hello from pap logger

# or

import logging
from pap_logger import PaPLogger
pap = PaPLogger()
logging.info("Hello from pap logger")
logging.warning("Default level is WARNING")
pap.level = logging.INFO
logging.info("This in an informational Hello from pap logger")
# 2019-01-03 18:28:14.767 JST : Default level is WARNING
# 2019-01-03 18:28:14.767 JST [    INFO] <stdin> : This in an informational Hello from pap logger
```

As shown in above examples, the formatting used by the sysout StreamHandler changes with the logging level.

Setting the level to WARNING, INFO or DEBUG will provide additional contextual informations on the sysout StreamHandler.

This change of formatting is only made on the sysout StreamHandler.

The idea behind this choice is that end-users of your application don't normally run above WARNING.

This behavior can however be overriden by setting the verbose_fmt property to True or False:
```python
from pap_logger import *
pap = PaPLogger()
pap.verbose_fmt = True
pap.logger.info("Hello from pap logger")
pap.logger.warning("Default level is WARNING")
pap.level = INFO
pap.logger.info("This in an informational Hello from pap logger")
# 2019-01-03 19:48:43.364 JST [ WARNING] <stdin> : Default level is WARNING
# 2019-01-03 19:48:43.364 JST [    INFO] <stdin> : This in an informational Hello from pap logger
```

Both level and verbose_fmt can be set when calling PaPLogger:
```python
from pap_logger import *
pap = PaPLogger(level=INFO, verbose_fmt=True)
pap.logger.info("Hello from pap logger")
pap.logger.warning("Default level is WARNING")
pap.logger.info("This in an informational Hello from pap logger")
# 2019-01-03 19:53:04.272 JST [    INFO] <stdin> : Hello from pap logger
# 2019-01-03 19:53:04.273 JST [ WARNING] <stdin> : Default level is WARNING
# 2019-01-03 19:53:04.273 JST [    INFO] <stdin> : This in an informational Hello from pap logger
```

Logging simultaneously to a SysLogHandler and/or a TimedRotatingFileHandler is possible.
Both logging are activated at run time (only) by setting the corresponding properties:

```python
from pathlib import Path
from pap_logger import *
pap = PaPLogger(level=INFO, verbose_fmt=True)
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
# The log file can be prefixed by the hostname for cases where the machine where logs are created is necessary.
# When activated, the hostname is also written in the logs.∨
pap.logfile_with_hostname = True
```

The SysLogHandler will only log records with level WARNING or above and always in a verbose format.

The TimedRotatingFileHandler is rotating by default every day, and 15 days of logs are kept.

These values can only be changed when instantiating LsslLogger:
```python
from pathlib import Path
from pap_logger import *
pap = PaPLogger(level=INFO, verbose_fmt=True, when='W', backup_count=4)
pap.log_file = Path("/var/log/new_log_file_name")
```

Please refer to [TimedRotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler)

A demonstration of usage examples is given in the function _pap_logger_example.

Please run and refer to the source code.

### Exception raised and error handling

AssertionError occurs if you modify this module and change the level too early in the PaPLogger's `__init__`.

#### TimedRotatingFileHandler:
PermissionError is _NOT_ raised when logging to a directory where the user doesn't have permissions to create inodes.

In such cases, the exception is catched, an error is logged, and the TimedRotatingFileHandler isn't added to the logger.

#### SysLogHandler
Network errors are _NOT_ raised  when logging to an unreachable syslog server.

In such cases, the exception is catched, an error is logged, and the SysLogHandler isn't added to the logger.


### Compatibility information

This module will only run with Python 3.5 and ulterior due to its use of f-strings.

It has only been tested under GNU/Linux.