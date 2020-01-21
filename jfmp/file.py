import os

from appdirs import *

from .constants import CLIENT_VERSION, COMMAND_NAME

def conf_file(conf_file, create=False):
    conf_dir = user_config_dir(COMMAND_NAME)
    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir)
    conf_file = os.path.join(conf_dir, conf_file)
    if create and not os.path.isfile(conf_file):
        open(conf_file, 'w').close()
    return conf_file