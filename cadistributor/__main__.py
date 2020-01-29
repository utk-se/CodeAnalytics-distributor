
import argparse
from . import log
from .app import app

def main():
    parser = argparse.ArgumentParser(
        usage="You dont"
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        help="Port to listen on"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbosity increase"
    )

    args = parser.parse_args()

    log.info("Main start.")

    log.info("Starting Flash main loop.")

    app.run()

if __name__ == '__main__':
    main()
