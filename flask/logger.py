import logging

class ANSIFormatter(logging.Formatter):
    COLORS = {
        "INFO": "\033[92m",    # Verde
        "WARNING": "\033[93m", # Giallo
        "LOOT CAPTURED": "\033[91m",    # Rosso per LOOT
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


LOOT_LEVEL = 25  # Valore numerico per il livello LOOT
logging.addLevelName(LOOT_LEVEL, "LOOT CAPTURED")

def loot(self, message, *args, **kwargs):
    if self.isEnabledFor(LOOT_LEVEL):
        self._log(LOOT_LEVEL, message, args, **kwargs)


logging.Logger.loot = loot

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = ANSIFormatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
