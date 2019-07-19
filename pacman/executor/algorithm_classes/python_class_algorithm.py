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

import importlib
import logging
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from .abstract_python_algorithm import AbstractPythonAlgorithm

logger = FormatAdapter(logging.getLogger(__name__))


class PythonClassAlgorithm(AbstractPythonAlgorithm):
    """ An algorithm that is a class.
    """

    __slots__ = [
        # Python Class to create
        "_python_class",

        # Python Method to call on the class (optional if class is callable)
        "_python_method"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens, python_module, python_class,
            python_method=None):
        """
        :param python_class: The class of the algorithm
        :param python_method:\
            The method of the algorithm, or None if the class is callable
        """
        # pylint: disable=too-many-arguments
        super(PythonClassAlgorithm, self).__init__(
            algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens, python_module)
        self._python_class = python_class
        self._python_method = python_method

    @overrides(AbstractPythonAlgorithm.call_python)
    def call_python(self, inputs):

        # Get the class to use
        cls = getattr(
            importlib.import_module(self._python_module),
            self._python_class)

        # Create an instance
        instance = cls()

        # Get the method to call (or use the class as a callable if None)
        method = instance
        if self._python_method is not None:
            method = getattr(instance, self._python_method)
        try:
            return method(**inputs)
        except Exception:
            method = "__call__"
            if self._python_method is not None:
                method = self._python_method
            logger.error("Error when calling {}.{}.{} with inputs {}",
                         self._python_module, self._python_class, method,
                         inputs.keys())
            raise

    def __repr__(self):
        return (
            "PythonClassAlgorithm(algorithm_id={},"
            " required_inputs={}, optional_inputs={}, outputs={},"
            " python_module={}, python_class={}, python_method={})".format(
                self._algorithm_id, self._required_inputs,
                self._optional_inputs, self._outputs, self._python_module,
                self._python_class, self._python_method))

    @overrides(AbstractPythonAlgorithm.write_provenance_header)
    def write_provenance_header(self, provenance_file):
        provenance_file.write("{}\n".format(self._algorithm_id))
        if self._python_method:
            provenance_file.write("\t{}.{}.{}\n".format(
                self._python_module, self._python_class, self._python_method))
        else:
            provenance_file.write("\t{}.{}\n".format(
                self._python_module, self._python_class))
