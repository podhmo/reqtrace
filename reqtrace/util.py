import socket
import logging
logger = logging.getLogger(__name__)


def find_freeport():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))
    port = sock.getsockname()[1]
    logger.info("finding free port.. found port=%d", port)
    sock.close()
    return port
