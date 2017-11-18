import logging
import LoggerConfigurator
import ReceiptCollector

logger = logging.getLogger(__name__)

LoggerConfigurator.setup_logging()
ReceiptCollector.get_receipts()
