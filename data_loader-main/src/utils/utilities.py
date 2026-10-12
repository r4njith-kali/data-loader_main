
import yaml
from definitions import CONFIG_DIR, LOG_DIR
import logging


DEFAULT_CONFIG = f'{CONFIG_DIR}/api_config.yaml'


def config_param(config_file=DEFAULT_CONFIG, field=None):
    """Configures the script using a config file

    Args:
        field:
        config_file: the path of the config file, relative or absolute

    """
    with open(config_file) as config:
        try:
            configs = yaml.safe_load(config)
            param = configs.get(field)
            return param

        except yaml.YAMLError as e:
            print(e)


def percent_round(stat_cnt, total_cnt, decimal) -> float:
    """
    Calculates the percent of the actual vs total

    Args:
        stat_cnt: actual count
        total_cnt: total count
        decimal: number of decimal place to use
    Returns:
        float: rounded percentage
    """
    percent_rd = round((stat_cnt / total_cnt) * 100, decimal)

    return percent_rd


def keyword_filter(input_list: list, keyword: str) -> list:
    """
    Filter string list: check if input list contains given keyword
    Args:
        input_list: a list of string (exp: thing name)
        keyword: keyword for filtering
    Returns:
        list: filtered list
    """
    return [word for word in input_list if keyword in word]

def get_logger(name):

    """
    Create logfile and define logging level.
    Args:
        name: logger name
    Returns:
        obj: logger object
    """

    file_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    console_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

    file_handler = logging.FileHandler(filename=f'{LOG_DIR}/loader.log', encoding='utf_8_sig')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

    return logger
