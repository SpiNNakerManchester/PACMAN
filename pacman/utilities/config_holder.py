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

import spinn_utilities.conf_loader as conf_loader

__config = None


def load_cfgs(configfile, default_config_paths, validation_cfg=None):
    """
    :param str configfile:
        The base name of the configuration file(s).
        Should not include any path components.
    :param list(str) default_config_paths:
        The list of files to get default configurations from.
    :type default_config_paths: list(str)
    :param validation_cfg:
        The list of files to read a validation configuration from.
        If None, no such validation is performed.
    :type validation_cfg: list(str) or None
    """
    global __config
    __config = conf_loader.load_config(
        filename=configfile, defaults=default_config_paths,
        validation_cfg=validation_cfg)


def get_config_str(section, option):
    """ Get the string value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value
    :rtype: str or None
    """
    return __config.get_str(section, option)


def get_config_str_list(section, option, token=","):
    """ Get the string value of a config option split into a list

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :param token: The token to split the string into a list
    :return: The list (possibly empty) of the option values
    :rtype: list(str)
    """
    return __config.get_str_list(section, option, token)


def get_config_int(section, option):
    """ Get the integer value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value
    :rtype: int
    """
    return __config.get_int(section, option)


def get_config_float(section, option):
    """ Get the float value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value.
    :rtype: float
    """
    return __config.get_float(section, option)


def get_config_bool(section, option):
    """ Get the boolean value of a config option.

    :param str section: What section to get the option from.
    :param str option: What option to read.
    :return: The option value.
    :rtype: bool
    """
    return __config.getboolean(section, option)


def set_config(section, option, value):
    """ Sets the value of a config option.

    :param str section: What section to set the option in.
    :param str option: What option to setd.
    :param object value: Value to set option to
    :return: The option value.
    """
    __config.set(section, option, value)


def config_options(section):
    """Return a list of option names for the given section name.

    :param str section: What section to list options for.
    """
    return __config.options(section)