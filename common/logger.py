import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_DEFAULT_LOG_DIR = Path(os.getenv("EDGE_AI_LOG_DIR", "data/logs"))

def get_logger(name: str, level: int = logging.INFO, log_dir: Path = _DEFAULT_LOG_DIR) -> logging.Logger:
    """Return a process-wide singleton logger with console + rotating file handlers.
    File path: {log_dir}/{name.replace('.', '_')}.log
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_edge_ai_configured", False):
        return logger

    logger.setLevel(level)
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    safe_name = name.replace(".", "_")
    fh = RotatingFileHandler(log_dir / f"{safe_name}.log", maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger._edge_ai_configured = True  # type: ignore[attr-defined]
    return logger
