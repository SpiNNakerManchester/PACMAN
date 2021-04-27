# Copyright (c) 2017-2019 The University of Manchester
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import spinn_utilities.conf_loader as conf_loader
from spinn_utilities.configs import CamelCaseConfigParser
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__file__))

BASE_CONFIG_FILE = "spinnaker.cfg"

__config = None

__default_config_files = [
    os.path.join(os.path.dirname(__file__), BASE_CONFIG_FILE)]
__config_file = None
__validation_cfg = None


def add_default_cfg(default):
    """
    Adds an extra default config to be read after easrlier ones

    :param str default: Absolute path to the cfg file
    """
    __default_config_files.append(default)


def set_cfg_files(configfile, default, validation_cfg=None):
    """
    Adds the cfg files to be loaded

    :param str configfile:
        The base name of the configuration file(s).
        Should not include any path components.
    :param default: Full path to the extra file to get default configurations
        from.
    :param validation_cfg:
        The list of files to read a validation configuration from.
        If None, no such validation is performed.
    :type validation_cfg: list(str) or None

    :param str default: Absolute path to the cfg file
    """
    global __config_file, __validation_cfg
    __config_file = configfile
    __default_config_files.append(default)
    __validation_cfg = validation_cfg


def load_config_cfgs():
    """
    Resets the config to the defaults. Ignoring user configs and setup changes

    """
    global __config
    if __config_file:
        __config = conf_loader.load_config(
            filename=__config_file, defaults=__default_config_files,
            validation_cfg=__validation_cfg)
    else:
        # Only expected to happen in unittests but just in case
        logger.warning(
            "Accessing config before setup is not recommended as setup could"
            " change some config values. ")
        __config = CamelCaseConfigParser()
        for default in __default_config_files:
            __config.read(default)
    print("Here")


def get_config_str(section, option):
    """ Get the string value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value
    :rtype: str or None
    """
    try:
        return __config.get_str(section, option)
    except AttributeError:
        load_config_cfgs()
        return __config.get_str(section, option)


def get_config_str_list(section, option, token=","):
    """ Get the string value of a config option split into a list

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :param token: The token to split the string into a list
    :return: The list (possibly empty) of the option values
    :rtype: list(str)
    """
    try:
        return __config.get_str_list(section, option, token)
    except AttributeError:
        load_config_cfgs()
        return __config.get_str_list(section, option, token)


def get_config_int(section, option):
    """ Get the integer value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value
    :rtype: int
    """
    try:
        return __config.get_int(section, option)
    except AttributeError:
        load_config_cfgs()
        return __config.get_int(section, option)


def get_config_float(section, option):
    """ Get the float value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value.
    :rtype: float
    """
    try:
        return __config.get_float(section, option)
    except AttributeError:
        load_config_cfgs()
        return __config.get_float(section, option)


def get_config_bool(section, option):
    """ Get the boolean value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value.
    :rtype: bool
    """
    try:
        return __config.get_bool(section, option)
    except AttributeError:
        load_config_cfgs()
        return __config.get_bool(section, option)


def set_config(section, option, value):
    """ Sets the value of a config option.

    :param str section: What section to set the option in.
    :param str option: What option to set.
    :param object value: Value to set option to
    """
    __config.set(section, option, value)
    # Intentionally no try here to force tests that set to
    # load_default_configs before AND after


def has_config_option(section, option):
    """ Check if the section has this config option.

    :param str section: What section to check
    :param str option: What option to check.
    :rtype: bool
    :return: True if and only if the option is defined. It may be None
    """
    try:
        return __config.has_option(section, option)
    except AttributeError:
        load_config_cfgs()
        return __config.has_option(section, option)


def config_options(section):
    """Return a list of option names for the given section name.

    :param str section: What section to list options for.
    """
    return __config.options(section)


def _check_lines(py_path, line, lines, index, method):
    """
    Support for check_python_file. Gets section and option name

    :param str line: Line with get_config call
    :param list(str) lines: All lines in the file
    :param int index: index of line with get_config call
    :raise Exception: If an unexpected or uncovered get_config found
    """
    while ")" not in line:
        index += 1
        line += lines[index]
    parts = line[line.find("(", line.find("get_config")) + 1:
                 line.find(")")].split(",")
    section = parts[0].strip().replace("'", "").replace('"', '')
    option = parts[1].strip()
    if option[0] == "'":
        option = option.replace("'", "")
    elif option[0] == '"':
        option = option.replace('"', '')
    else:
        print(line)
        return
    try:
        method(section, option)
    except Exception:
        raise Exception(f"failed in line:{index} of file: {py_path}")


def check_python_file(py_path):
    """
    A testing function to check that all the get_config calls work

    :param str py_path: path to file to be checked
    :raise Exception: If an unexpected or uncovered get_config found
    """
    with open(py_path, 'r') as py_file:
        lines = py_file.readlines()
        for index, line in enumerate(lines):
            if "get_config_bool(" in line:
                _check_lines(py_path, line, lines, index, get_config_bool)
            if "get_config_float(" in line:
                _check_lines(py_path, line, lines, index, get_config_float)
            if "get_config_int(" in line:
                _check_lines(py_path, line, lines, index, get_config_int)
            if "get_config_str(" in line:
                _check_lines(py_path, line, lines, index, get_config_str)
            if "get_config_str_list(" in line:
                _check_lines(py_path, line, lines, index, get_config_str_list)
