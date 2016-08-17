# pacman imports
from pacman import exceptions
from pacman import operations
from pacman.executor import injection_decorator
from pacman.executor.algorithm_decorators import algorithm_decorator
from pacman.executor.algorithm_metadata_xml_reader \
    import AlgorithmMetadataXmlReader
from pacman.operations import algorithm_reports
from pacman.utilities import file_format_converters
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

    __slots__ = [

        # The timing of algorithms
        "_algorithm_timings",

        # The algorithms to run
        "_algorithms",

        # The inputs passed in from the user
        "_inputs",

        # The type mapping as things flow from input to output
        "_internal_type_mapping",

        # True if timing is to be done
        "_do_timing",

        # True if timing is to be printed
        "_print_timings",

        # True if injection is to be done during the run
        "_do_immediate_injection",

        # True if injection is to be done after the run
        "_do_post_run_injection",

        # True if the inputs are to be injected
        "_inject_inputs",

        # True if direct injection is to be done
        "_do_direct_injection"
    ]

    def __init__(
            self, algorithms, optional_algorithms, inputs, required_outputs,
            xml_paths=None, packages=None, do_timings=True,
            print_timings=False, do_immediate_injection=True,
            do_post_run_injection=False, inject_inputs=True,
            do_direct_injection=True):
        """

        :param algorithms: A list of algorithms that must all be run
        :param optional_algorithms:\
            A list of algorithms that must be run if their inputs are available
        :param inputs: A dict of input type to value
        :param required_outputs: A list of output types that must be generated
        :param xml_paths:\
            An optional list of paths to XML files containing algorithm\
            descriptions; if not specified, only detected algorithms will be\
            used (or else those found in packages)
        :param packages:\
            An optional list of packages to scan for decorated algorithms; if\
            not specified, only detected algorithms will be used (or else\
            those specified in packages
        :param do_timings:\
            True if timing information should be printed after each algorithm,\
            False otherwise
        :param do_immediate_injection:\
            Perform injection with objects as they are created; can result in\
            multiple calls to the same inject-annotated methods
        :param do_post_run_injection:\
            Perform injection at the end of the run. This will only set the\
            last object of any type created.
        :param inject_inputs:\
            True if inputs should be injected; only active if one of\
            do_immediate_injection or do_post_run_injection is True.  These\
            variables define when the injection of inputs is done; if\
            immediate injection is True, injection of inputs is done at the\
            start of the run, otherwise it is done at the end.
        :param do_direct_injection:\
            True if direct injection into methods should be supported.  This\
            will allow any of the inputs or generated outputs to be injected\
            into a method
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
        self._inject_inputs = inject_inputs
        self._do_direct_injection = do_direct_injection

        self._set_up_pacman_algorithm_listings(
            algorithms, optional_algorithms, xml_paths,
            packages, inputs, required_outputs)

    def _set_up_pacman_algorithm_listings(
            self, algorithms, optional_algorithms, xml_paths, packages, inputs,
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

        # protect the variable from reference movement during usage
        copy_of_xml_paths = []
        if xml_paths is not None:
            copy_of_xml_paths = list(xml_paths)
        copy_of_packages = []
        if packages is not None:
            copy_of_packages = list(packages)
        copy_of_optional_algorithms = []
        if optional_algorithms is not None:
            copy_of_optional_algorithms = list(optional_algorithms)

        # set up XML reader for standard PACMAN algorithms XML file reader
        # (used in decode_algorithm_data_objects function)
        copy_of_xml_paths.append(os.path.join(
            os.path.dirname(operations.__file__),
            "algorithms_metadata.xml"))
        copy_of_xml_paths.append(os.path.join(
            os.path.dirname(operations.__file__),
            "rigs_algorithm_metadata.xml"))
        copy_of_xml_paths.append(os.path.join(
            os.path.dirname(algorithm_reports.__file__),
            "reports_metadata.xml"))

        # decode the algorithms specs
        xml_decoder = AlgorithmMetadataXmlReader(copy_of_xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()
        converter_xml_path = \
            os.path.join(os.path.dirname(file_format_converters.__file__),
                         "converter_algorithms_metadata.xml")
        converter_decoder = AlgorithmMetadataXmlReader([converter_xml_path])
        converters = converter_decoder.decode_algorithm_data_objects()

        # Scan for annotated algorithms
        copy_of_packages.append(operations)
        copy_of_packages.append(algorithm_reports)
        converters.update(algorithm_decorator.scan_packages(
            [file_format_converters]))
        algorithm_data_objects.update(
            algorithm_decorator.scan_packages(copy_of_packages))

        # get list of all xml's as this is used to exclude xml files from
        # import
        all_xml_paths = list()
        all_xml_paths.extend(copy_of_xml_paths)
        all_xml_paths.append(converter_xml_path)

        converter_names = list()
        for converter in converters.iterkeys():
            converter_names.append(converter)

        # filter for just algorithms we want to use
        algorithm_data = self._get_algorithm_data(
            algorithms_names, algorithm_data_objects)
        optional_algorithms_datas = self._get_algorithm_data(
            copy_of_optional_algorithms, algorithm_data_objects)
        converter_algorithms_datas = self._get_algorithm_data(
            converter_names, converters)

        # sort_out_order_of_algorithms for execution
        self._sort_out_order_of_algorithms(
            inputs, required_outputs, algorithm_data,
            optional_algorithms_datas, converter_algorithms_datas)

    @staticmethod
    def _get_algorithm_data(
            algorithm_names, algorithm_data_objects):
        algorithms = list()
        for algorithm_name in algorithm_names:
            if algorithm_name in algorithm_data_objects:
                algorithms.append(algorithm_data_objects[algorithm_name])
            else:
                raise exceptions.PacmanConfigurationException(
                    "Cannot find algorithm {}".format(algorithm_name))
        return algorithms

    def _sort_out_order_of_algorithms(
            self, inputs, required_outputs, algorithm_data,
            optional_algorithm_data, converter_algorithms_datas):
        """ Takes the algorithms and determines which order they need to be\
            executed to generate the correct data objects

        :param inputs: list of input types
        :type inputs: iterable of str
        :param required_outputs: the set of outputs that this workflow is\
                meant to generate
        :param converter_algorithms_datas: the set of converter algorithms
        :param optional_algorithm_data: the set of optional algorithms
        :return: None
        """

        input_types = set(inputs.iterkeys())

        allocated_algorithms = list()
        generated_outputs = set()
        generated_outputs.union(input_types)
        allocated_a_algorithm = True
        algorithms_to_find = list(algorithm_data)
        optionals_to_use = list(optional_algorithm_data)
        outputs_to_find = self._remove_outputs_which_are_inputs(
            required_outputs, inputs)

        while ((len(algorithms_to_find) > 0 or len(outputs_to_find) > 0) and
                allocated_a_algorithm):
            allocated_a_algorithm = False

            # Find a usable algorithm
            suitable_algorithm = self._locate_suitable_algorithm(
                algorithms_to_find, input_types, generated_outputs)
            if suitable_algorithm is not None:
                self._remove_algorithm_and_update_outputs(
                    algorithms_to_find, suitable_algorithm, input_types,
                    generated_outputs, outputs_to_find)

            else:

                # If no algorithm, find a usable optional algorithm
                suitable_algorithm = self._locate_suitable_algorithm(
                    optionals_to_use, input_types, generated_outputs)
                if suitable_algorithm is not None:
                    self._remove_algorithm_and_update_outputs(
                        optionals_to_use, suitable_algorithm, input_types,
                        generated_outputs, outputs_to_find)
                else:
                    # if still no suitable algorithm, try converting some
                    # stuff from memory to file or visa versa
                    suitable_algorithm = self._locate_suitable_algorithm(
                        converter_algorithms_datas, input_types,
                        generated_outputs)
                    if suitable_algorithm is not None:
                        self._remove_algorithm_and_update_outputs(
                            converter_algorithms_datas, suitable_algorithm,
                            input_types, generated_outputs, outputs_to_find)

            if suitable_algorithm is not None:

                # add the suitable algorithms to the list and take the outputs
                # as new inputs
                allocated_algorithms.append(suitable_algorithm)
                allocated_a_algorithm = True
            else:

                # Failed to find an algorithm to run!
                algorithms_left_names = list()
                for algorithm in algorithms_to_find:
                    algorithms_left_names.append(algorithm.algorithm_id)
                for algorithm in optional_algorithm_data:
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
                for algorithm in optionals_to_use:
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
            inputs.add(output.output_type)
            generated_outputs.add(output.output_type)
            if output.output_type in outputs_to_find:
                outputs_to_find.remove(output.output_type)

    @staticmethod
    def _locate_suitable_algorithm(
            algorithm_list, inputs, generated_outputs):
        """ Locates a suitable algorithm

        :param algorithm_list: the list of algorithms to choose from
        :param inputs: the inputs available currently
        :param generated_outputs: the current outputs expected to be generated
        :return: a suitable algorithm which uses the inputs
        """

        # Find all algorithms which *can* run now and rank them using the
        # number of unavailable optional inputs
        algorithms_available = list()
        for algorithm in algorithm_list:

            # check all inputs
            all_inputs_match = True
            for input_parameter in algorithm.required_inputs:
                if not input_parameter.input_matches(inputs):
                    all_inputs_match = False
                    break

            if all_inputs_match:

                # check for optional inputs
                n_optional_inputs_unavailable = 0
                for optional_input in algorithm.optional_inputs:
                    if not optional_input.input_matches(inputs):
                        n_optional_inputs_unavailable += 1

                algorithms_available.append(
                    (algorithm, n_optional_inputs_unavailable))

        # If no algorithms are available, return None
        if len(algorithms_available) == 0:
            return None

        # Find the algorithm with the least unavailable optional inputs
        algorithms_available.sort(key=lambda (x, y): y)
        algorithm, n_optional_inputs_unavailable = algorithms_available[0]

        # Find any other algorithms with the same ranking; if None return this
        other_algorithms = filter(
            lambda (x, y): y == n_optional_inputs_unavailable,
            algorithms_available)
        if len(other_algorithms) == 1:
            return algorithm

        # If there are other algorithms, rank by the number of non-novel
        # outputs
        boring_algorithms = list()
        for algorithm, _ in other_algorithms:

            # Count the number of non-novel outputs
            n_boring_outputs = 0
            for output in algorithm.outputs:
                if output.output_type in generated_outputs:
                    n_boring_outputs += 1

            # If any, add to the list
            if n_boring_outputs > 0:
                boring_algorithms.append((algorithm, n_boring_outputs))

        # If all return something novel, return the first
        if len(boring_algorithms) == 0:
            return algorithm

        # Otherwise return the most non-novel
        boring_algorithms.sort(key=lambda (x, y): y, reverse=True)
        return boring_algorithms[0][0]

    def execute_mapping(self):
        """ Executes the algorithms
        :return: None
        """
        if self._inject_inputs and self._do_immediate_injection:
            injection_decorator.do_injection(self._inputs)
        self._internal_type_mapping.update(self._inputs)
        new_outputs = dict()

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
                if self._do_immediate_injection and not self._inject_inputs:
                    new_outputs.update(results)

            # Do injection with the outputs produced
            if self._do_immediate_injection and results is not None:
                injection_decorator.do_injection(results)

        # Do injection with all the outputs
        if self._do_post_run_injection:
            if self._inject_inputs:
                injection_decorator.do_injection(self._internal_type_mapping)
            else:
                injection_decorator.do_injection(new_outputs)

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
