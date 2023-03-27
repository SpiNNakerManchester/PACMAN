# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Support code for validation.
"""

import os
import json
import concurrent.futures

_jsonschema = None


def _init():
    import jsonschema
    global _jsonschema  # pylint: disable=global-statement
    _jsonschema = jsonschema


def _validate(json_obj, schema_doc: str):
    _jsonschema.validate(json_obj, schema_doc)


#: A single thread that we fire all validation work through.
_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, initializer=_init)


def validate(json_obj, schema_filename):
    """
    Check that the given JSON object (or array) is valid against the
    given schema. The schema is given by filename relative to this package.

    :param json_obj: The entity to validate
    :type json_obj: dict or list
    :param str schema_filename:
        The name of the file containing the schema (e.g., "routes.json")
    :raises IOError: If the schema file doesn't exist.
    :raises ~jsonschema.exceptions.ValidationError:
        If the JSON object isn't valid.
    """
    schema_file = os.path.join(os.path.dirname(__file__), schema_filename)
    # Validate in a single thread to stop leakage of thread-bound resources
    # https://github.com/python-jsonschema/jsonschema/issues/1059
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_doc = json.load(f)
        _executor.submit(_validate, json_obj, schema_doc).result()
