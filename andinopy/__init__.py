#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import configparser
import logging
import os

from setuptools.command.setopt import config_file

andinopy_logger = logging.getLogger('andinopy')
andinopy_logger.addHandler(logging.NullHandler())

base_config = configparser.ConfigParser()
config_file_s = ""
initialized = False


def initialize_cfg(config_file_i=None):
    global initialized
    global config_file_s

    if config_file_i is None:
        config_file_s = "default.cfg"
    else:
        if config_file_i[-4:] != ".cfg":
            raise RuntimeWarning("Config File does not End in '.cfg'")
        config_file_s = config_file_i
    if os.path.isfile(config_file_s[:-4]+"_saved.cfg"):
        base_config.read(config_file_s[:-4]+"_saved.cfg")
    else:
        if not os.path.isfile(config_file_s):
            raise Exception(f"config file: {config_file_s} does not exist")
        base_config.read(config_file_s)
    initialized = True


def save_base_config():
    global initialized
    global config_file_s
    if not initialized:
        raise RuntimeWarning("Config was not initialized - cannot save config")
    fp = open(config_file_s[:-4]+"_saved.cfg", 'w')
    base_config.write(fp, space_around_delimiters=False)
    andinopy_logger.debug("config saved")
    fp.close()
