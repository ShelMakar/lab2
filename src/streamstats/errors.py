class StreamStatsError(Exception):
    """базовая ошибка приложения"""

class UncorrectFormatError(StreamStatsError):
    """неподдерживаемый формат"""

class UncorrectEventError(StreamStatsError):
    """неверное событие"""

class UncorrectTimeMark(StreamStatsError):
    """неверная временная метка"""

class CLIConfigError(StreamStatsError):
    """ошибка конфигурации CLI"""
