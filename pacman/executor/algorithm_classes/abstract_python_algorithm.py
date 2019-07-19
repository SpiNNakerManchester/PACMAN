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

from abc import abstractmethod
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanAlgorithmFailedToGenerateOutputsException
from .abstract_algorithm import AbstractAlgorithm


class AbstractPythonAlgorithm(AbstractAlgorithm):
    """ An algorithm written in Python.
    """

    __slots__ = [
        # The module containing the python code to execute
        "_python_module"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens, python_module):
        """
        :param python_module: The module containing the python code to execute
        """
        # pylint: disable=too-many-arguments
        super(AbstractPythonAlgorithm, self).__init__(
            algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens)
        self._python_module = python_module

    @abstractmethod
    def call_python(self, inputs):
        """ Call the algorithm

        :param inputs: A dict of parameter name -> value
        :return: The result of calling the python algorithm
        """

    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):

        # Get the inputs to pass to the function
        method_inputs = self._get_inputs(inputs)

        # Run the algorithm and get the results
        results = self.call_python(method_inputs)

        if results is not None and not isinstance(results, tuple):
            results = (results,)

        # If there are no results and there are not meant to be, return
        if results is None and not self._outputs:
            return None

        # Check the results are valid
        if ((results is None and self._outputs) or
                len(self._outputs) != len(results)):
            raise PacmanAlgorithmFailedToGenerateOutputsException(
                "Algorithm {} returned {} but specified {} output types"
                .format(self._algorithm_id, results, len(self._outputs)))

        # Return the results processed into a dict
        return self._get_outputs(inputs, results)
