# pacman imports
from pacman import exceptions
from pacman.operations import algorithm_reports
from pacman.utilities.file_format_converters.convert_algorithms_metadata \
    import ConvertAlgorithmsMetadata
from pacman.utilities import file_format_converters
from pacman import operations
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman.utilities.utility_objs.timer import Timer

# general imports
import logging
import importlib
import subprocess
import os
import sys
from collections import defaultdict

logger = logging.getLogger(__name__)


class PACMANAlgorithmExecutor(object):
    """ An executor of PACMAN algorithms where the order is deduced from the\
        input and outputs of the algorithm using an XML description of the\
        algorithm
    """

    def __init__(self, algorithms, optional_algorithms, inputs, xml_paths,
                 required_outputs, do_timings=True, print_timings=False):
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
        xml_decoder = ConvertAlgorithmsMetadata(xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()
        xml_decoder = ConvertAlgorithmsMetadata(converter_xml_path)
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
            # and without its optional required inputs
            suitable_algorithm = self._locate_suitable_algorithm(
                algorithms_to_find, input_types, generated_outputs, False,
                True)

            # add the suitable algorithms to the list and take there outputs
            #  as new inputs
            if suitable_algorithm is not None:
                allocated_algorithms.append(suitable_algorithm)
                allocated_a_algorithm = True
                self._remove_algorithm_and_update_outputs(
                    algorithms_to_find, suitable_algorithm, input_types,
                    generated_outputs, outputs_to_find)
            else:
                suitable_algorithm = self._locate_suitable_algorithm(
                    optional_algorithms, input_types,
                    generated_outputs, True, True)
                if suitable_algorithm is not None:
                    allocated_algorithms.append(suitable_algorithm)
                    allocated_a_algorithm = True
                    self._remove_algorithm_and_update_outputs(
                        optional_algorithms, suitable_algorithm,
                        input_types, generated_outputs, outputs_to_find)
                else:
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

    def _deduce_inputs_required_to_run(self, algorithm, input_names):
        inputs = algorithm.inputs
        left_over_inputs = "            {}: ".format(algorithm.algorithm_id)
        first = True
        for an_input in inputs:
            if an_input['type'] not in input_names:
                if first:
                    left_over_inputs += "['{}'".format(an_input['type'])
                    first = False
                else:
                    left_over_inputs += ", '{}'".format(an_input['type'])
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
            inputs.add(output['type'])
            generated_outputs.add(output['type'])
            if output['type'] in outputs_to_find:
                outputs_to_find.remove(output['type'])

    @staticmethod
    def _locate_suitable_algorithm(
            algorithm_list, inputs, generated_outputs, look_for_novel_output,
            look_for_optional_required_inputs):
        """ Locates a suitable algorithm

        :param algorithm_list: the list of algorithms to choose from
        :param inputs: the inputs available currently
        :param generated_outputs: the current outputs expected to be generated
        :param look_for_novel_output: bool which says that algorithms need\
                to produce a novel output
        :param look_for_optional_required_inputs: bool which states it should\
                look at the optional required inputs to verify a usable\
                function
        :return: a suitable algorithm which uses the inputs
        """
        position = 0
        suitable_algorithm = None
        while (suitable_algorithm is None and
                position < len(algorithm_list)):
            algorithm = algorithm_list[position]

            # check all inputs
            all_inputs_available = True
            for input_parameter in algorithm.inputs:
                if input_parameter['type'] not in inputs:
                    all_inputs_available = False
            adds_to_output = False

            # check all outputs
            if look_for_novel_output:
                for output_parameter in algorithm.outputs:
                    if output_parameter['type'] not in generated_outputs:
                        adds_to_output = True

            # check for optional required inputs
            has_any_optional_required_inputs = False
            if len(algorithm.requred_optional_inputs) == 0:
                has_any_optional_required_inputs = True
            else:
                extra_inputs = algorithm.requred_optional_inputs
                for optional_required_input in extra_inputs:
                    if optional_required_input['type'] in inputs:
                        has_any_optional_required_inputs = True

            # check if all check's passed
            if (all_inputs_available and
                    (not look_for_optional_required_inputs or
                        has_any_optional_required_inputs) and
                    (not look_for_novel_output or adds_to_output) and
                    suitable_algorithm is None):
                suitable_algorithm = algorithm
            position += 1
        return suitable_algorithm

    def execute_mapping(self):
        """ Executes the algorithms
        :return: None
        """
        self._internal_type_mapping.update(self._inputs)

        for algorithm in self._algorithms:

            # execute the algorithm and store outputs
            if not algorithm.external:

                # internal to pacman
                self._handle_internal_algorithm(algorithm)
            else:

                # external to pacman
                self._handle_external_algorithm(algorithm)

    def _handle_internal_algorithm(self, algorithm):
        """ Creates the input files for the algorithm

        :param algorithm: the algorithm
        :return: None
        """
        # create algorithm
        python_algorithm = self._create_python_object(algorithm)

        # create input dictionary
        inputs = self._create_input_commands(algorithm)

        # set up timer
        timer = None
        if self._do_timing:
            timer = Timer()
            timer.start_timing()

        # execute algorithm
        try:
            results = python_algorithm(**inputs)
        except Exception as e:
            exc_info = sys.exc_info()
            if isinstance(
                    e, exceptions.PacmanAlgorithmFailedToCompleteException):
                raise exc_info[0], exc_info[1], exc_info[2]
            else:
                raise exceptions.PacmanAlgorithmFailedToCompleteException(
                    algorithm, e, exc_info[2])
        # handle_prov_data
        if self._do_timing:
            self._update_timings(timer, algorithm)

        # move outputs into internal data objects
        self._map_output_parameters(results, algorithm)

    def _handle_external_algorithm(self, algorithm):
        """ Creates the input files for the algorithm

        :param algorithm: the algorithm
        :return: None
        """
        input_params = self._create_input_commands(algorithm)

        inputs = \
            [a.format(**input_params) for a in algorithm.command_line_args]

        # output debug info in case things go wrong
        logger.debug(
            "The inputs to the external mapping function are {}"
            .format(inputs))

        # create progress bar for external algorithm
        algorithm_progress_bar = ProgressBar(
            1, "Running external algorithm {}".format(algorithm.algorithm_id))

        timer = None
        if self._do_timing:
            timer = Timer()
            timer.start_timing()

        # execute other command
        child = subprocess.Popen(
            inputs, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)
        child.wait()
        algorithm_progress_bar.end()

        if self._do_timing:
            self._update_timings(timer, algorithm)

        # check the return code for a successful execution
        if child.returncode != 0:
            stdout, stderr = child.communicate()
            raise exceptions.\
                PacmanExternalAlgorithmFailedToCompleteException(
                    "Algorithm {} returned a non-zero error code {}\n"
                    "    Inputs: {}\n"
                    "    Output: {}\n"
                    "    Error: {}\n".format(
                        algorithm.algorithm_id, child.returncode,
                        inputs, stdout, stderr))

        outputs = self._sort_out_external_algorithm_outputs(algorithm)
        self._map_output_parameters(outputs, algorithm)

    def _sort_out_external_algorithm_outputs(self, algorithm):
        """ Get a map of output name to type for an external algorithm

        :param algorithm: the external algorithm
        :return: the list of mapped outputs
        """
        outputs = dict()
        for output in algorithm.outputs:
            outputs[output['name']] = \
                self._internal_type_mapping[output['name']]
        return outputs

    def _create_input_commands(self, algorithm):
        """ Get a map of input name to type for an algorithm

        :param algorithm: the algorithm in question
        :return: a dictionary containing input names and the corresponding \
                internal type mapping's object
        """
        params = dict()

        # handle required inputs
        for input_param in algorithm.inputs:
            params[input_param['name']] = \
                self._internal_type_mapping[input_param['type']]

        # handle optional inputs
        for input_param in algorithm.optional_inputs:
            if input_param['type'] in self._internal_type_mapping:
                params[input_param['name']] = \
                    self._internal_type_mapping[input_param['type']]

        # handle optional required inputs, only adding the first found param
        #  and other params with that rank
        required_optional_inputs_list = list(algorithm.requred_optional_inputs)

        required_optional_inputs_list = \
            sorted(required_optional_inputs_list, key=lambda i: i['rank'],
                   reverse=False)

        # locate first param
        located = False
        located_rank = None
        for input_param in required_optional_inputs_list:
            if (input_param['type'] in self._internal_type_mapping and
                    (not located or located_rank == input_param['rank'])):
                params[input_param['name']] = self._internal_type_mapping[
                    input_param['type']]
                located = True
                located_rank = input_param['rank']

        return params

    def _map_output_parameters(self, results, algorithm):
        """ Get a map of outputs from an algorithm

        :param results: the results from the algorithm
        :param algorithm: the algorithm description
        :return: None
        """
        if results is not None:

            # update python data objects
            for result_name in results:
                result_type = algorithm.get_type_from_output_name(result_name)
                if result_type is None:
                    raise exceptions.PacmanTypeError(
                        "Unrecognised result name {} for algorithm {} with "
                        "outputs {}".format(
                            result_name, algorithm.algorithm_id,
                            algorithm.outputs))
                self._internal_type_mapping[result_type] = results[result_name]
        elif len(algorithm.outputs) != 0:
            raise exceptions.PacmanAlgorithmFailedToGenerateOutputsException(
                "Algorithm {} did not generate any outputs".format(
                    algorithm.algorithm_id))

    @staticmethod
    def _create_python_object(algorithm):
        """ Create a python object for an algorithm from a specification

        :param algorithm: the algorithm specification
        :return: an instantiated object for the algorithm
        """
        if (algorithm.python_class is not None and
                algorithm.python_function is None):

            # if class, instantiate it
            python_algorithm = getattr(
                importlib.import_module(algorithm.python_module_import),
                algorithm.python_class)
            try:
                python_algorithm = python_algorithm()
            except TypeError as type_error:
                raise exceptions.PacmanConfigurationException(
                    "Failed to create instance of algorithm {}: {}"
                    .format(algorithm.algorithm_id, type_error.message))

        elif (algorithm.python_function is not None and
                algorithm.python_class is None):

            # just a function, so no instantiation required
            python_algorithm = getattr(
                importlib.import_module(algorithm.python_module_import),
                algorithm.python_function)

        else:

            # neither, but is a python object.... error
            raise exceptions.PacmanConfigurationException(
                "Internal algorithm {} must be either a function or a class"
                "but not both".format(algorithm.algorithm_id))
        return python_algorithm

    def get_item(self, item_type):
        """ Get an item from the outputs of the execution

        :param item_type: the item from the internal type mapping to be\
                    returned
        :return: the returned item
        """
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
