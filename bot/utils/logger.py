import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("rename_bot")

# quiet noisy libraries
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
