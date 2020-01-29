
import argparse, toml
from . import log
from .app import app

def main():
    parser = argparse.ArgumentParser()

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
    if (args.verbose):
        log.setLevel(log.DEBUG)

    app.config["codeanalytics"] = toml.load(args.config)
    try:
        app.config['SECRET_KEY'] = app.config["codeanalytics"]["api"]["sessionkey"]
    except Exception as e:
        log.err("Failed to load session SECRET_KEY from config.")
        raise e
    log.debug("Config loaded.")

    log.info("Main start: " + __name__)

    app.config.update(TESTING=True)

    log.info("Starting Flash main loop.")
    app.run()

if __name__ == '__main__':
    main()
