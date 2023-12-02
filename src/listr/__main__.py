from argparse import ArgumentParser
from pathlib import Path

from listr.bot import Listr
from listr.utils.config import Config, read_from_env_var
from listr.utils.logging import get_logger

LOGGER = get_logger(__name__)


def main(config_file: Path):
    try:
        token = read_from_env_var("DISCORD_TOKEN_FILE")
    except Exception as error:
        LOGGER.error(error)
        return

    config = Config.from_yaml(config_file, create_if_not_found=True)
    bot = Listr(**config.model_dump())
    bot.run(token)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config-file", type=Path, default="config/config.yaml")
    main(**vars(parser.parse_args()))
