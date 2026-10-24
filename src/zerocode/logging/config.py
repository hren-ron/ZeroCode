import logging
from pathlib import Path


DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(className)s | %(funcName)s:%(lineno)d | %(message)s"
)


class ZeroCodeFormatter(logging.Formatter):
    """为日志记录补充类名。"""

    def format(self, record: logging.LogRecord) -> str:
        record.className = "-"

        # 从当前日志调用位置向外查找所属类
        import inspect

        frame = inspect.currentframe()
        try:
            frame = frame.f_back if frame else None

            while frame:
                # 找到产生这条日志的调用帧
                if (
                    frame.f_code.co_name == record.funcName
                    and frame.f_lineno == record.lineno
                ):
                    instance = frame.f_locals.get("self")
                    if instance is not None:
                        record.className = type(instance).__name__
                    else:
                        cls = frame.f_locals.get("cls")
                        if isinstance(cls, type):
                            record.className = cls.__name__
                    break

                frame = frame.f_back
        finally:
            del frame

        return super().format(record)


LOGGER_NAME = "zerocode"

def configure_logging(
        level: int | str = logging.INFO,
        log_to_file: bool = True,
        log_dir: str | Path | None = None
) -> logging.Logger:

    # 1. 解析并校验日志级别
    if isinstance(level, str):
        resolved_level = logging.getLevelName(level.upper())
        if not isinstance(resolved_level, int):
            raise ValueError(f"Invalid logging level: {level}")
        level = resolved_level

    # 2. 获取 ZeroCode 专属 logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # 不向 root logger 传播，避免重复输出
    logger.propagate = False

    # 子模块日志向 zerocode 传递
    logging.getLogger(LOGGER_NAME).setLevel(level)

    # 3. 移除本函数之前创建的 Handler，避免重复初始化

    for handler in logger.handlers[:]:
        if getattr(handler, "_zerocode_handler", False):
            logger.removeHandler(handler)
            handler.close()

    # 4. 统一日志格式
    formatter = ZeroCodeFormatter(DEFAULT_LOG_FORMAT)

    # 5. 输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler._zerocode_handler = True
    logger.addHandler(console_handler)

    # 6. 可选：输出到日志文件
    if log_to_file:
        if log_dir is None:
            project_root = Path(__file__).resolve().parents[3]
            log_dir = project_root / "logs"

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path / "zerocode.log", encoding="utf-8")

        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler._zerocode_handler = True
        logger.addHandler(file_handler)

    return logger


