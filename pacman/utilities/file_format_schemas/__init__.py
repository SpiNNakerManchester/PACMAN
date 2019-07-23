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
    :param schema_filename: \
        The name of the file containing the schema (e.g., "routes.json")
    :type schema_filename: str
    :rtype: None
    :raises IOError: If the schema file doesn't exist.
    :raises ValidationError: If the JSON object isn't valid.
    """
    schema_file = os.path.join(os.path.dirname(__file__), schema_filename)
    with open(schema_file, "r") as f:
        jsonschema.validate(json_obj, json.load(f))
