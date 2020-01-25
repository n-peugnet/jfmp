# Copyright (C) 2020  Nicolas Peugnet
#
# This file is part of jfmp.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

from appdirs import *

from .constants import COMMAND_NAME


def conf_file(file_name, create=False):
    """Returns the path to the requested conf file."""
    conf_dir = user_config_dir(COMMAND_NAME)
    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir)
    file_name = os.path.join(conf_dir, file_name)
    if create and not os.path.isfile(file_name):
        open(file_name, 'w').close()
    return file_name


def cache_file(file_name, create=False):
    """Returns the path to the requested cache file."""
    cache_dir = user_cache_dir(COMMAND_NAME)
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    file_name = os.path.join(cache_dir, file_name)
    if create and not os.path.isfile(file_name):
        open(file_name, 'w').close()
    return file_name
