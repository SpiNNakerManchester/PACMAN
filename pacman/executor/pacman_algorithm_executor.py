# pacman imports
from pacman import exceptions
from pacman.operations import algorithm_reports
from pacman.executor import injection_decorator
from pacman.executor.algorithm_metadata_xml_reader \
    import AlgorithmMetadataXmlReader
from pacman.utilities import file_format_converters
from pacman import operations
from pacman.utilities.utility_objs.timer import Timer

# general imports
import logging
import os
from collections import defaultdict

logger = logging.getLogger(__name__)


class PACMANAlgorithmExecutor(object):
    """ An executor of PACMAN algorithms where the order is deduced from the\
        input and outputs of the algorithm using an XML description of the\
        algorithm
    """

    def __init__(self, algorithms, optional_algorithms, inputs, xml_paths,
                 required_outputs, do_timings=True, print_timings=False,
                 do_immediate_injection=False, do_post_run_injection=False):
        """

        :param algorithms: A list of algorithms that must all be run
        :param optional_algorithms: A list of algorithms that must be run if\
                their inputs are available
        :param inputs: A dict of input type to value
        :param xml_paths: A list of paths to XML files containing algorithm\
                descriptions
        :param required_outputs: A list of output types that must be generated
        :param do_timings: True if timing information should be printed after\
                each algorithm, False otherwise
        :param do_immediate_injection: Perform injection with objects as they\
                are created; can result in multiple calls to the same inject-\
                annotated methods
        :param do_post_run_injection: Perform injection at the end of the run.\
                This will only set the last object of any type created.
        """

        # algorithm timing information
        self._algorithm_timings = list()

        # pacman mapping objects
        self._algorithms = list()
        self._inputs = inputs

        # define mapping between types and internal values
        self._internal_type_mapping = defaultdict()

        # store timing request
        self._do_timing = do_timings

        # print timings as you go
        self._print_timings = print_timings

        # injection
        self._do_immediate_injection = do_immediate_injection
        self._do_post_run_injection = do_post_run_injection

        # protect the variable from reference movement during usage
        copy_of_xml_paths = list(xml_paths)

        self._set_up_pacman_algorithm_listings(
            algorithms, optional_algorithms, copy_of_xml_paths, inputs,
            required_outputs)

    def _set_up_pacman_algorithm_listings(
            self, algorithms, optional_algorithms, xml_paths, inputs,
            required_outputs):
        """ Translates the algorithm string and uses the config XML to create\
            algorithm objects

        :param algorithms: the string representation of the set of algorithms
        :param inputs: list of input types
        :type inputs: iterable of str
        :param optional_algorithms: list of algorithms which are optional\
                and don't necessarily need to be ran to complete the logic flow
        :type optional_algorithms: list of strings
        :param xml_paths: the list of paths for XML configuration data
        :type xml_paths: iterable of strings
        :param required_outputs: the set of outputs that this workflow is\
                 meant to generate
        :type required_outputs: iterable of types as strings
        """

        # deduce if the algorithms are internal or external
        algorithms_names = list(algorithms)

        # set up XML reader for standard PACMAN algorithms XML file reader
        # (used in decode_algorithm_data_objects function)
        xml_paths.append(os.path.join(
            os.path.dirname(operations.__file__),
            "algorithms_metadata.xml"))
        xml_paths.append(os.path.join(
            os.path.dirname(algorithm_reports.__file__),
            "reports_metadata.xml"))

        converter_xml_path = list()
        converter_xml_path.append(os.path.join(
            os.path.dirname(file_format_converters.__file__),
            "converter_algorithms_metadata.xml"))

        # decode the algorithms specs
        xml_decoder = AlgorithmMetadataXmlReader(xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()
        xml_decoder = AlgorithmMetadataXmlReader(converter_xml_path)
        converter_algorithm_data_objects = \
            xml_decoder.decode_algorithm_data_objects()

        # filter for just algorithms we want to use
        algorithm_data = self._get_algorithm_data(
            algorithms_names, algorithm_data_objects,
            converter_algorithm_data_objects)
        optional_algorithms_datas = self._get_algorithm_data(
            optional_algorithms, algorithm_data_objects,
            converter_algorithm_data_objects)
        optional_algorithms_datas.extend(
            converter_algorithm_data_objects.values())

        # sort_out_order_of_algorithms for execution
        self._sort_out_order_of_algorithms(
            inputs, required_outputs, algorithm_data,
            optional_algorithms_datas)

    def _get_algorithm_data(
            self, algorithm_names, algorithm_data_objects,
            converter_algorithm_data_objects):
        algorithms = list()
        for algorithm_name in algorithm_names:
            if algorithm_name in algorithm_data_objects:
                algorithms.append(algorithm_data_objects[algorithm_name])

            elif algorithm_name in converter_algorithm_data_objects:
                algorithms.append(
                    converter_algorithm_data_objects[algorithm_name])
            else:
                raise exceptions.PacmanConfigurationException(
                    "Cannot find algorithm {}".format(algorithm_name))
        return algorithms

    def _sort_out_order_of_algorithms(
            self, inputs, required_outputs, algorithm_data,
            optional_algorithms):
        """ Takes the algorithms and determines which order they need to be\
            executed to generate the correct data objects

        :param inputs: list of input types
        :type inputs: iterable of str
        :param required_outputs: the set of outputs that this workflow is\
                meant to generate
        :param optional_algorithms: the set of optional algorithms which\
                include the converters for the file formats which can be\
                inserted automatically if required
        :return: None
        """

        input_types = set(inputs.iterkeys())

        allocated_algorithms = list()
        generated_outputs = set()
        generated_outputs.union(input_types)
        allocated_a_algorithm = True
        algorithms_to_find = list(algorithm_data)
        outputs_to_find = self._remove_outputs_which_are_inputs(
            required_outputs, inputs)

        while ((len(algorithms_to_find) > 0 or len(outputs_to_find) > 0) and
                allocated_a_algorithm):
            allocated_a_algorithm = False

            # check each algorithm to see if its usable with current inputs
            # and without its optional inputs
            suitable_algorithm = self._locate_suitable_algorithm(
                algorithms_to_find, input_types, generated_outputs,
                look_for_novel_output=False, look_for_optional_inputs=False)

            # If there isn't an algorithm, check for one with novel outputs
            # but not optional inputs
            if suitable_algorithm is None:
                suitable_algorithm = self._locate_suitable_algorithm(
                    algorithms_to_find, input_types, generated_outputs,
                    look_for_novel_output=True, look_for_optional_inputs=False)

            # If there isn't an algorithm, check for one with no novel
            # outputs but with optional inputs
            if suitable_algorithm is None:
                suitable_algorithm = self._locate_suitable_algorithm(
                    algorithms_to_find, input_types, generated_outputs,
                    look_for_novel_output=False, look_for_optional_inputs=True)

            # If still no algorithm, check for one with novel outputs and
            # optional inputs
            if suitable_algorithm is None:
                suitable_algorithm = self._locate_suitable_algorithm(
                    algorithms_to_find, input_types, generated_outputs,
                    look_for_novel_output=True, look_for_optional_inputs=True)

            if suitable_algorithm is not None:

                # add the suitable algorithms to the list and take the outputs
                # as new inputs
                allocated_algorithms.append(suitable_algorithm)
                allocated_a_algorithm = True
                self._remove_algorithm_and_update_outputs(
                    algorithms_to_find, suitable_algorithm, input_types,
                    generated_outputs, outputs_to_find)
            else:

                # Failed to find an algorithm to run!
                algorithms_left_names = list()
                for algorithm in algorithms_to_find:
                    algorithms_left_names.append(algorithm.algorithm_id)
                for algorithm in optional_algorithms:
                    algorithms_left_names.append(algorithm.algorithm_id)
                algorithms_used = list()
                for algorithm in allocated_algorithms:
                    algorithms_used.append(algorithm.algorithm_id)
                algorithm_input_requirement_breakdown = ""
                for algorithm in algorithms_to_find:
                    if algorithm.algorithm_id in algorithms_left_names:
                        algorithm_input_requirement_breakdown += \
                            self._deduce_inputs_required_to_run(
                                algorithm, input_types)
                for algorithm in optional_algorithms:
                    if algorithm.algorithm_id in algorithms_left_names:
                        algorithm_input_requirement_breakdown += \
                            self._deduce_inputs_required_to_run(
                                algorithm, input_types)

                raise exceptions.PacmanConfigurationException(
                    "Unable to deduce a future algorithm to use.\n"
                    "    Inputs: {}\n"
                    "    Outputs: {}\n"
                    "    Functions available: {}\n"
                    "    Functions used: {}\n"
                    "    Inputs required per function: \n{}\n".format(
                        input_types,
                        outputs_to_find,
                        algorithms_left_names, algorithms_used,
                        algorithm_input_requirement_breakdown))

        # Test that the outputs are generated
        all_required_outputs_generated = True
        failed_to_generate_output_string = ""
        for output in outputs_to_find:
            if output not in generated_outputs:
                all_required_outputs_generated = False
                failed_to_generate_output_string += ":{}".format(output)

        if not all_required_outputs_generated:
            raise exceptions.PacmanConfigurationException(
                "Unable to generate outputs {}".format(
                    failed_to_generate_output_string))

        self._algorithms = allocated_algorithms

    def _remove_outputs_which_are_inputs(self, required_outputs, inputs):
        """ Generates the output list which has pruned outputs which are\
            already in the input list

        :param required_outputs: the original output listings
        :param inputs: the inputs given to the executor
        :return: new list of outputs
        :rtype: iterable of str
        """
        copy_required_outputs = set(required_outputs)
        for input_type in inputs:
            if input_type in copy_required_outputs:
                copy_required_outputs.remove(input_type)
        return copy_required_outputs

    def _deduce_inputs_required_to_run(self, algorithm, inputs):
        left_over_inputs = "            {}: ".format(algorithm.algorithm_id)
        first = True
        for an_input in algorithm.required_inputs:
            unfound_types = [
                param_type for param_type in an_input.param_types
                if param_type not in inputs
            ]
            if len(unfound_types) > 0:
                if first:
                    left_over_inputs += "['{}'".format(unfound_types)
                    first = False
                else:
                    left_over_inputs += ", '{}'".format(unfound_types)
        left_over_inputs += "]\n"
        return left_over_inputs

    @staticmethod
    def _remove_algorithm_and_update_outputs(
            algorithm_list, algorithm, inputs, generated_outputs,
            outputs_to_find):
        """ Update data structures

        :param algorithm_list: the list of algorithms to remove algorithm from
        :param algorithm: the algorithm to remove
        :param inputs: the inputs list to update output from algorithm
        :param generated_outputs: the outputs list to update output from\
                    algorithm
        :return: none
        """
        algorithm_list.remove(algorithm)
        for output in algorithm.outputs:
            inputs.add(output)
            generated_outputs.add(output)
            if output in outputs_to_find:
                outputs_to_find.remove(output)

    @staticmethod
    def _locate_suitable_algorithm(
            algorithm_list, inputs, generated_outputs, look_for_novel_output,
            look_for_optional_inputs):
        """ Locates a suitable algorithm

        :param algorithm_list: the list of algorithms to choose from
        :param inputs: the inputs available currently
        :param generated_outputs: the current outputs expected to be generated
        :param look_for_novel_output: bool which says that algorithms need\
                to produce a novel output
        :param look_for_optional_inputs: bool which states it should\
                look at the optional inputs
        :return: a suitable algorithm which uses the inputs
        """
        for algorithm in algorithm_list:

            # check all inputs
            all_inputs_available = True
            for input_parameter in algorithm.required_inputs:
                if not input_parameter.input_matches(inputs):
                    all_inputs_available = False

            # check all outputs
            adds_to_output = False
            if look_for_novel_output:
                for output in algorithm.outputs:
                    if output not in generated_outputs:
                        adds_to_output = True

            # check for optional inputs
            optional_inputs_available = False
            if len(algorithm.optional_inputs) == 0:
                optional_inputs_available = True
            else:
                for optional_input in algorithm.optional_inputs:
                    if optional_input.input_matches(inputs):
                        optional_inputs_available = True

            # check if all checks passed
            if (all_inputs_available and
                    (not look_for_optional_inputs or
                        optional_inputs_available) and
                    (not look_for_novel_output or adds_to_output)):
                return algorithm
        return None

    def execute_mapping(self):
        """ Executes the algorithms
        :return: None
        """
        self._internal_type_mapping.update(self._inputs)

        for algorithm in self._algorithms:

            # set up timer
            timer = None
            if self._do_timing:
                timer = Timer()
                timer.start_timing()

            # Execute the algorithm
            results = algorithm.call(self._internal_type_mapping)

            # handle_prov_data
            if self._do_timing:
                self._update_timings(timer, algorithm)

            if results is not None:
                self._internal_type_mapping.update(results)

            # Do injection with the outputs produced
            if self._do_immediate_injection:
                for result_type, result in results.iteritems():
                    injection_decorator.do_injection({result_type: result})

        # Do injection with all the outputs
        if self._do_post_run_injection:
            injection_decorator.do_injection(self._internal_type_mapping)

    def get_item(self, item_type):
        """ Get an item from the outputs of the execution

        :param item_type: the item from the internal type mapping to be\
                    returned
        :return: the returned item
        """
        if item_type not in self._internal_type_mapping:
            return None
        else:
            return self._internal_type_mapping[item_type]

    def get_items(self):
        """ Get all the outputs from a execution

        :return: dictionary of types as keys and values.
        """
        return self._internal_type_mapping

    @property
    def algorithm_timings(self):
        return self._algorithm_timings

    def _update_timings(self, timer, algorithm):
        time_taken = timer.take_sample()
        if self._print_timings:
            logger.info("Time {} taken by {}".format(
                str(time_taken), algorithm.algorithm_id))
        self._algorithm_timings.append((algorithm.algorithm_id, time_taken))
