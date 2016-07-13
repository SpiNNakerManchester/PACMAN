from pacman.executor.abstract_algorithm import AbstractAlgorithm
from pacman.model.decorators.overrides import overrides
from pacman import exceptions
import subprocess
from spinn_machine.utilities.progress_bar import ProgressBar


class ExternalAlgorithm(AbstractAlgorithm):

    __slots__ = [

        # The command line to call
        "_command_line_arguments"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            command_line_arguments):
        AbstractAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs)
        self._command_line_arguments = command_line_arguments

    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):

        # Get the inputs to pass as the arguments
        arg_inputs = self._get_inputs(inputs)

        # Convert the arguments using the inputs
        args = [
            arg.format(**arg_inputs) for arg in self._command_line_arguments
        ]

        algorithm_progress_bar = ProgressBar(
            1, "Running external algorithm {}".format(self._algorithm_id))

        # Run the external command
        child = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)
        child.wait()

        algorithm_progress_bar.update(1)
        algorithm_progress_bar.end()

        # Detect any errors
        if child.returncode != 0:
            stdout, stderr = child.communicate()
            raise exceptions.\
                PacmanExternalAlgorithmFailedToCompleteException(
                    "Algorithm {} returned a non-zero error code {}\n"
                    "    Inputs: {}\n"
                    "    Output: {}\n"
                    "    Error: {}\n".format(
                        self._algorithm_id, child.returncode,
                        inputs, stdout, stderr))

        # Return the results processed into a dict
        return {
            output_type: inputs[output_type] for output_type in self._outputs
        }
