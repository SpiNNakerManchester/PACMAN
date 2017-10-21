from spinn_utilities.timer import Timer
# pacman imports
from pacman.exceptions import PacmanConfigurationException
from pacman import operations
from .injection_decorator import injection_context, do_injection
from .algorithm_decorators import scan_packages, get_algorithms
from .algorithm_metadata_xml_reader import AlgorithmMetadataXmlReader
from pacman.operations import algorithm_reports
from pacman.utilities import file_format_converters

# general imports
import logging

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
        "_do_direct_injection",

        # the flag in the provenance area.
        "_provenance_name",

        # If required a file path to append provenace data to
        "_provenance_path"
    ]

    def __init__(
            self, algorithms, optional_algorithms, inputs, required_outputs,
            xml_paths=None, packages=None, do_timings=True,
            print_timings=False, do_immediate_injection=True,
            do_post_run_injection=False, inject_inputs=True,
            do_direct_injection=True, use_unscanned_annotated_algorithms=True,
            provenance_path=None, provenance_name=None):
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
        :param use_unscanned_annotated_algorithms:\
            True if algorithms that have been detected outside of the packages\
            argument specified above should be used
        :param provenance_path:
            Path to file to append full provenance data to
            If None no provenance is written
        """

        # algorithm timing information
        self._algorithm_timings = list()

        # pacman mapping objects
        self._algorithms = list()
        self._inputs = inputs

        # define mapping between types and internal values
        self._internal_type_mapping = dict()

        # store timing request
        self._do_timing = do_timings

        # print timings as you go
        self._print_timings = print_timings

        # injection
        self._do_immediate_injection = do_immediate_injection
        self._do_post_run_injection = do_post_run_injection
        self._inject_inputs = inject_inputs
        self._do_direct_injection = do_direct_injection

        if provenance_name is None:
            self._provenance_name = "mapping"
        else:
            self._provenance_name = provenance_name

        self._set_up_pacman_algorithm_listings(
            algorithms, optional_algorithms, xml_paths,
            packages, inputs, required_outputs,
            use_unscanned_annotated_algorithms)

        self._provenance_path = provenance_path

    def _set_up_pacman_algorithm_listings(
            self, algorithms, optional_algorithms, xml_paths, packages, inputs,
            required_outputs, use_unscanned_algorithms):
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
        copy_of_xml_paths.append(operations.algorithms_metdata_file)
        copy_of_xml_paths.append(operations.rigs_algorithm_metadata_file)
        copy_of_xml_paths.append(algorithm_reports.reports_metadata_file)

        # decode the algorithms specs
        xml_decoder = AlgorithmMetadataXmlReader(copy_of_xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()
        converter_xml_path = \
            file_format_converters.converter_algorithms_metadata_file
        converter_decoder = AlgorithmMetadataXmlReader([converter_xml_path])
        converters = converter_decoder.decode_algorithm_data_objects()

        # Scan for annotated algorithms
        copy_of_packages.append(operations)
        copy_of_packages.append(algorithm_reports)
        converters.update(scan_packages([file_format_converters]))
        algorithm_data_objects.update(scan_packages(copy_of_packages))
        if use_unscanned_algorithms:
            algorithm_data_objects.update(get_algorithms())

        # get list of all xml's as this is used to exclude xml files from
        # import
        all_xml_paths = list()
        all_xml_paths.extend(copy_of_xml_paths)
        all_xml_paths.append(converter_xml_path)

        # filter for just algorithms we want to use
        algorithm_data = self._get_algorithm_data(
            algorithms_names, algorithm_data_objects)
        optional_algorithms_datas = self._get_algorithm_data(
            copy_of_optional_algorithms, algorithm_data_objects)
        converter_algorithms_datas = self._get_algorithm_data(
            converters.keys(), converters)

        # sort_out_order_of_algorithms for execution
        self._determine_algorithm_order(
            inputs, required_outputs, algorithm_data,
            optional_algorithms_datas, converter_algorithms_datas)

    @staticmethod
    def _get_algorithm_data(
            algorithm_names, algorithm_data_objects):
        algorithms = list()
        for algorithm_name in algorithm_names:
            if algorithm_name not in algorithm_data_objects:
                raise PacmanConfigurationException(
                    "Cannot find algorithm {}".format(algorithm_name))
            algorithms.append(algorithm_data_objects[algorithm_name])
        return algorithms

    def _determine_algorithm_order(
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
        :rtype: None
        """

        input_types = set(inputs.iterkeys())

        allocated_algorithms = list()
        generated_outputs = set()
        generated_outputs.union(input_types)
        algorithms_to_find = list(algorithm_data)
        optionals_to_use = list(optional_algorithm_data)
        outputs_to_find = self._remove_outputs_which_are_inputs(
            required_outputs, inputs)

        while algorithms_to_find or outputs_to_find:
            # Find a usable algorithm
            suitable_algorithm, algorithm_list = \
                self._locate_suitable_algorithm(
                    algorithms_to_find, input_types, None)

            # If no algorithm, find a usable optional algorithm
            if suitable_algorithm is None:
                suitable_algorithm, algorithm_list = \
                    self._locate_suitable_algorithm(
                        optionals_to_use, input_types, generated_outputs)

            # if still no suitable algorithm, try using a converter algorithm
            if suitable_algorithm is None:
                suitable_algorithm, algorithm_list = \
                    self._locate_suitable_algorithm(
                        converter_algorithms_datas, input_types,
                        generated_outputs)

            if suitable_algorithm is not None:
                # Remove the value
                self._remove_algorithm_and_update_outputs(
                    algorithm_list, suitable_algorithm, input_types,
                    generated_outputs, outputs_to_find)

                # add the suitable algorithms to the list and take the outputs
                # as new inputs
                allocated_algorithms.append(suitable_algorithm)
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

                raise PacmanConfigurationException(
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
            raise PacmanConfigurationException(
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
        left_over_inputs = "            {}: [".format(algorithm.algorithm_id)
        separator = ""
        for an_input in algorithm.required_inputs:
            unfound_types = [
                param_type for param_type in an_input.param_types
                if param_type not in inputs]
            if unfound_types:
                left_over_inputs += "{}'{}'".format(separator, unfound_types)
                separator = ", "
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
        :rtype: None
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

        # TODO: This can be made "cleverer" by looking at which algorithms have
        # unsatisfied optional inputs.  The next algorithm to run can then
        # be the next that outputs the most unsatisfied optional inputs for
        # other algorithms from those with the least unsatisfied optional
        # inputs

        # Find the next algorithm which can run now
        for algorithm in algorithm_list:
            # check all inputs
            all_inputs_match = True
            for input_parameter in algorithm.required_inputs:
                if not input_parameter.input_matches(inputs):
                    all_inputs_match = False
                    break

            # verify that a new output is being generated.
            if all_inputs_match:
                # If the list of generated outputs is given, only use the
                # algorithm if it generates something new, assuming the
                # algorithm generates any outputs at all
                # (otherwise just use it)
                if algorithm.outputs and generated_outputs is not None:
                    for output in algorithm.outputs:
                        if (output.output_type not in generated_outputs and
                                output.output_type not in inputs):
                            return algorithm, algorithm_list
                else:
                    return algorithm, algorithm_list

        # If no algorithms are available, return None
        return None, algorithm_list

    def execute_mapping(self):
        """ Executes the algorithms

        :rtype: None
        """
        self._internal_type_mapping.update(self._inputs)
        if self._do_direct_injection:
            with injection_context(self._internal_type_mapping):
                self._execute_mapping()
        else:
            self._execute_mapping()

    def _execute_mapping(self):
        if self._inject_inputs and self._do_immediate_injection:
            do_injection(self._inputs)
        new_outputs = dict()
        for algorithm in self._algorithms:
            # set up timer
            timer = None
            if self._do_timing:
                timer = Timer()
                timer.start_timing()

            # Execute the algorithm
            results = algorithm.call(self._internal_type_mapping)

            if self._provenance_path:
                self._report_full_provenance(algorithm, results)

            # handle_prov_data
            if self._do_timing:
                self._update_timings(timer, algorithm)

            if results is not None:
                self._internal_type_mapping.update(results)
                if self._do_immediate_injection and not self._inject_inputs:
                    new_outputs.update(results)

            # Do injection with the outputs produced
            if self._do_immediate_injection:
                do_injection(results)

        # Do injection with all the outputs
        if self._do_post_run_injection:
            if self._inject_inputs:
                do_injection(self._internal_type_mapping)
            else:
                do_injection(new_outputs)

    def get_item(self, item_type):
        """ Get an item from the outputs of the execution

        :param item_type: the item from the internal type mapping to be\
                    returned
        :return: the returned item
        """
        if item_type not in self._internal_type_mapping:
            return None
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
        self._algorithm_timings.append(
            (algorithm.algorithm_id, time_taken, self._provenance_name))

    def _report_full_provenance(self, algorithm, results):
        try:
            with open(self._provenance_path, "a") as provenance_file:
                algorithm.write_provenance_header(provenance_file)
                if len(algorithm.required_inputs) > 0:
                    provenance_file.write("\trequired_inputs:\n")
                    self._report_inputs(provenance_file,
                                        algorithm.required_inputs)
                if len(algorithm.optional_inputs) > 0:
                    provenance_file.write("\toptional_inputs:\n")
                    self._report_inputs(provenance_file,
                                        algorithm.optional_inputs)
                if len(algorithm.outputs) > 0:
                    provenance_file.write("\toutputs:\n")
                    for output in algorithm.outputs:
                        variable = results[output.output_type]
                        the_type = self._get_type(variable)
                        provenance_file.write(
                            "\t\t{}:{}\n".format(output.output_type, the_type))
                provenance_file.write("\n")
        except Exception:
            logger.error("Exception when attempting to write provenance",
                         exc_info=True)

    def _report_inputs(self, provenance_file, inputs):
        for input in inputs:  # @ReservedAssignment
            name = input.name
            for param_type in input.param_types:
                if param_type in self._internal_type_mapping:
                    variable = self._internal_type_mapping[param_type]
                    the_type = self._get_type(variable)
                    provenance_file.write(
                        "\t\t{}   {}:{}\n".format(name, param_type, the_type))
                    break
            else:
                if len(input.param_types) == 1:
                    provenance_file.write(
                        "\t\t{}   None of {} provided\n"
                        "".format(name, input.param_types))
                else:
                    provenance_file.write(
                        "\t\t{}   {} not provided\n"
                        "".format(name, input.param_types[0]))

    def _get_type(self, variable):
        if variable is None:
            return "None"
        the_type = type(variable)
        if the_type in [bool, float, int, str]:
            return variable
        if the_type == set:
            if len(variable) == 0:
                return "Empty set"
            the_type = "set("
            for item in variable:
                the_type += "{},".format(self._get_type(item))
            the_type += ")"
            return the_type
        elif the_type == list:
            if len(variable) == 0:
                return "Empty list"
            first_type = type(variable[0])
            if all(isinstance(n, first_type) for n in variable):
                return "list({}) :len{}".format(first_type, len(variable))
        return the_type
