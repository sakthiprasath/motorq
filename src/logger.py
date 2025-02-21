import os, sys
import uuid
import logging


class Logger:

    DEFAULT_LEVEL = 1
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    default_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    verbose_format = \
        logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(filename)s:%(lineno)d - %(message)s')

    def __init__(self, logger_name=None, min_level=None, to_stdout=True, to_file=None, format_verbose=False,
                 log_format=None):
        """
        Initializes a default logging or with options.
        :param logger_name: Name of the logging (optional). If you want to get a logging instance
        across modules, the same name can be used to get it using __init__()
        or get_logger_by_name().
        :param min_level: The minimum level of logging that is written to the logging's handlers. (default is 1)
        :param to_stdout: True outputs the logs to stdout. False does not. (default is True)
        :param to_file: The file to which log should be written. (default does not write to any file)
        :param format_verbose: True formats the message with details. False does not format the message. (default is False)
        :param log_format: str : set log format
        """

        if logger_name is None or not isinstance(logger_name, str):
            logger_name = 'default' + uuid.uuid1().__str__()

        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.set_min_level(min_level)

        handlers = self.set_handlers(to_file, to_stdout)

        Logger.set_log_formatter(handlers, log_format, format_verbose)

        for i in handlers:
            self.logger.addHandler(i)

        self.logger.propagate = False

    def set_min_level(self, min_level):
        if min_level is None:
            min_level = Logger.DEFAULT_LEVEL
        self.logger.setLevel(min_level)

    def set_handlers(self, to_file, to_stdout):
        handlers = []
        if to_stdout and not any(type(x) == logging.StreamHandler for x in self.logger.handlers):
            handlers.append(logging.StreamHandler(sys.stdout))
        if to_file is not None and isinstance(to_file, str):
            file_handlers = [x for x in self.logger.handlers if type(x) == logging.FileHandler]
            if not any(x.baseFilename.split(os.sep)[-1] == to_file for x in file_handlers):
                handlers.append(logging.FileHandler(to_file))
        return handlers

    @staticmethod
    def set_log_formatter(handlers, log_format, format_verbose:bool):
        formatter = Logger.default_format
        if log_format is not None:
            formatter = logging.Formatter(log_format)
        else:
            if format_verbose:
                formatter = Logger.verbose_format

        for h in handlers:
            h.setFormatter(formatter)

    def log(self, message, level=None):
        """
        Logs a message with an optional level. Default is the level of the logger that is defined.
        :param message: String with your log message.
        :param level: Integer > 0. Default is the level of the logger that is defined.
        You can also use Logger.INFO, Logger.WARN, Logger.ERROR, Logger.CRITICAL
        :return: None
        """
        if level is None:
            level = self.logger.level
        self.logger.log(msg=message, level=level)
