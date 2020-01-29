
import argparse
from . import log
from .app import app

def main():
    parser = argparse.ArgumentParser(
        usage="You dont"
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Config file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbosity increase"
    )

    args = parser.parse_args()

    log.info("Main start: " + __name__)

    log.info("Starting Flash main loop.")

    app.run()

if __name__ == '__main__':
    main()
