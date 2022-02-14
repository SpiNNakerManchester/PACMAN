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

""" A simple bit of support code for validation.
"""

import os
import json
import jsonschema


def validate(json_obj, schema_filename):
    """ Check that the given JSON object (or array) is valid against the\
        given schema. The schema is given by filename relative to this package.

    :param json_obj: The entity to validate
    :type json_obj: dict or list
    :param str schema_filename:
        The name of the file containing the schema (e.g., "routes.json")
    :rtype: None
    :raises IOError: If the schema file doesn't exist.
    :raises ~jsonschema.exceptions.ValidationError:
        If the JSON object isn't valid.
    """
    schema_file = os.path.join(os.path.dirname(__file__), schema_filename)
    with open(schema_file, "r", encoding="utf-8") as f:
        jsonschema.validate(json_obj, json.load(f))
