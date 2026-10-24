
import io
import logging

from zerocode.logging.config import configure_logging


class ExampleService:
    def run(self):
        logger = logging.getLogger("zerocode.test_module")
        logger.info("测试日志")


def test_log_contains_module_class_function_and_line():
    logger = configure_logging(
        level=logging.INFO,
        log_to_file=False,
    )

    # 用独立的内存流捕获日志
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logger.handlers[0].formatter)
    logger.addHandler(handler)

    try:
        ExampleService().run()
        output = stream.getvalue()

        assert "zerocode.test_module" in output
        assert "ExampleService" in output
        assert "run:" in output
        assert "测试日志" in output
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_repeated_configuration_does_not_duplicate_logs():
    import io

    logger = configure_logging(
        level=logging.INFO,
        log_to_file=False,
    )

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logger.handlers[0].formatter)
    logger.addHandler(handler)

    try:
        configure_logging(
            level=logging.INFO,
            log_to_file=False,
        )

        # configure_logging 会重建自己的 Handler，
        # 但这里手动添加的 handler 不属于它管理的范围。
        logger.info("重复初始化测试")

        output = stream.getvalue()
        assert output.count("重复初始化测试") == 1
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_log_is_written_to_file(tmp_path):
    log_dir = tmp_path / "logs"

    logger = configure_logging(
        level=logging.INFO,
        log_to_file=True,
        log_dir=log_dir,
    )

    try:
        logger.info("文件日志测试")

        # 刷新 Handler 缓冲区，确保内容写入文件
        for handler in logger.handlers:
            handler.flush()

        log_file = log_dir / "zerocode.log"

        assert log_file.exists()
        assert "文件日志测试" in log_file.read_text(encoding="utf-8")
    finally:
        # 避免测试结束后遗留指向临时目录的文件 Handler
        for handler in logger.handlers[:]:
            if getattr(handler, "_zerocode_handler", False):
                logger.removeHandler(handler)
                handler.close()
