# pacman imports
from pacman import exceptions
from pacman.interfaces.abstract_provides_provenance_data import \
    AbstractProvidesProvenanceData
from pacman.utilities.utility_objs.ordered_set import OrderedSet
from pacman.utilities.file_format_converters.convert_algorithms_metadata \
    import ConvertAlgorithmsMetadata
from pacman.utilities import file_format_converters
from pacman import operations
from pacman.utilities.utility_objs.progress_bar import ProgressBar

# general imports
import logging
import importlib
import subprocess
import os
import traceback
from collections import defaultdict
from pacman.utilities.utility_objs.provenance_data_item import \
    ProvenanceDataItem
from pacman.utilities.utility_objs.timer import Timer

logger = logging.getLogger(__name__)


class PACMANAlgorithmExecutor(AbstractProvidesProvenanceData):
    """ An executor of PACMAN algorithms where the order is deduced from the\
        input and outputs of the algorithm using an XML description of the\
        algorithm
    """

    def __init__(self, algorithms, inputs, xml_paths,
                 required_outputs, do_timings=True, print_timings=False):
        """
        :return:
        """
        AbstractProvidesProvenanceData.__init__(self)

        # provenance data store
        self._provenance_data = list()

        # pacman mapping objects
        self._algorithms = list()

        # define mapping between types and internal values
        self._internal_type_mapping = defaultdict()

        # store timing request
        self._do_timing = do_timings

        # print timings as you go
        self._print_timings = print_timings

        self._set_up_pacman_algorithms_listings(
            algorithms, xml_paths, inputs, required_outputs)

        self._inputs = inputs

    def _set_up_pacman_algorithms_listings(
            self, algorithms, xml_paths, inputs, required_outputs):
        """ Translates the algorithm string and uses the config XML to create\
            algorithm objects

        :param algorithms: the string representation of the set of algorithms
        :param inputs: list of input types
        :type inputs: iterable of str
        :param xml_paths: the list of paths for XML configuration data
        :type xml_paths: iterable of strings
        :param required_outputs: the set of outputs that this workflow is\
                 meant to generate
        :type required_outputs: iterable of types as strings
        """

        # deduce if the algorithms are internal or external
        algorithms_names = self._algorithms
        algorithms_names.extend(algorithms)

        # set up XML reader for standard PACMAN algorithms XML file reader
        # (used in decode_algorithm_data_objects function)
        xml_paths.append(os.path.join(os.path.dirname(operations.__file__),
                                      "algorithms_metadata.xml"))

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
        self._algorithms = list()
        for algorithms_name in algorithms_names:
            self._algorithms.append(algorithm_data_objects[algorithms_name])

        # sort_out_order_of_algorithms for execution
        self._sort_out_order_of_algorithms(
            inputs, required_outputs,
            converter_algorithm_data_objects.values())

    def _sort_out_order_of_algorithms(
            self, inputs, required_outputs, optional_converter_algorithms):
        """ Takes the algorithms and determines which order they need to be\
            executed to generate the correct data objects
        :param inputs: list of input types
        :type inputs: iterable of str
        :param required_outputs: the set of outputs that this workflow is\
                meant to generate
        :param optional_converter_algorithms: the set of optional converter\
                algorithms which can be inserted automatically if required
        :return: None
        """

        input_names = OrderedSet()
        for input_item in inputs:
            input_names.add(input_item['type'])

        allocated_algorithms = list()
        generated_outputs = set()
        generated_outputs.union(input_names)
        allocated_a_algorithm = True
        while len(self._algorithms) != 0 and allocated_a_algorithm:
            allocated_a_algorithm = False

            # check each algorithm to see if its usable with current inputs
            # and without its optional required inputs
            suitable_algorithm = self._locate_suitable_algorithm(
                self._algorithms, input_names, generated_outputs, False, True)

            if suitable_algorithm is None:
                suitable_algorithm = self._locate_suitable_algorithm(
                    self._algorithms, input_names, generated_outputs, False,
                    True)
            # check each algorithm to see if its usable with current inputs and
            # its optional required inputs

            # add the suitable algorithms to the list and take there outputs
            #  as new inputs
            if suitable_algorithm is not None:
                allocated_algorithms.append(suitable_algorithm)
                allocated_a_algorithm = True
                self._remove_algorithm_and_update_outputs(
                    self._algorithms, suitable_algorithm, input_names,
                    generated_outputs)
            else:
                suitable_algorithm = self._locate_suitable_algorithm(
                    optional_converter_algorithms, input_names,
                    generated_outputs, True, True)
                if suitable_algorithm is not None:
                    allocated_algorithms.append(suitable_algorithm)
                    allocated_a_algorithm = True
                    self._remove_algorithm_and_update_outputs(
                        optional_converter_algorithms, suitable_algorithm,
                        input_names, generated_outputs)
                else:
                    algorithms_left_names = list()
                    for algorithm in self._algorithms:
                        algorithms_left_names.append(algorithm.algorithm_id)
                    for algorithm in optional_converter_algorithms:
                        algorithms_left_names.append(algorithm.algorithm_id)
                    algorithms_used = list()
                    for algorithm in allocated_algorithms:
                        algorithms_used.append(algorithm.algorithm_id)

                    raise exceptions.PacmanConfigurationException(
                        "Unable to deduce a future algorithm to use.\n"
                        "    Inputs: {}\n"
                        "    Outputs: {}\n"
                        "    Functions available: {}\n"
                        "    Functions used: {}\n".format(
                            input_names,
                            list(set(required_outputs) - set(input_names)),
                            algorithms_left_names, algorithms_used))

        all_required_outputs_generated = True
        failed_to_generate_output_string = ""
        for output in required_outputs:
            if output not in generated_outputs:
                all_required_outputs_generated = False
                failed_to_generate_output_string += ":{}".format(output)

        if not all_required_outputs_generated:
            raise exceptions.PacmanConfigurationException(
                "Unable to generate outputs {}".format(
                    failed_to_generate_output_string))

        # iterate through the list removing algorithms which are obsolete
        self._prune_unnecessary_algorithms(allocated_algorithms)

        self._algorithms = allocated_algorithms

    @staticmethod
    def _prune_unnecessary_algorithms(allocated_algorithms):
        """

        :param allocated_algorithms:
        :return:
        """
        # TODO optimisations!
        pass

    @staticmethod
    def _remove_algorithm_and_update_outputs(
            algorithm_list, algorithm, inputs, generated_outputs):
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
        :param look_for_optional_required_inputs: bool which states it should
                look at the optional required inputs to verify a usable function
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
            if (all_inputs_available
                and ((look_for_optional_required_inputs
                      and has_any_optional_required_inputs)
                     or not look_for_optional_required_inputs)
                and ((look_for_novel_output and adds_to_output)
                     or (not look_for_novel_output))
                and suitable_algorithm is None):
                suitable_algorithm = algorithm
            position += 1
        return suitable_algorithm

    def execute_mapping(self):
        """ Executes the algorithms
        :return: None
        """

        for input_parameter in self._inputs:
            self._internal_type_mapping[input_parameter['type']] = \
                input_parameter['value']

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
        except Exception as type_error:
            raise exceptions.PacmanAlgorithmFailedToCompleteException(
                algorithm, type_error, traceback)
        # handle_prov_data
        if self._do_timing:
            self._handle_prov(timer, algorithm)

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
            self._handle_prov(timer, algorithm)

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
                    (not located or
                         (located and located_rank == input_param['rank']))):
                params[input_param['name']] = \
                    self._internal_type_mapping[input_param['type']]
                located = True
                located_rank = input_param['rank']

        return params

    def _map_output_parameters(self, results, algorithm):
        """ Get a map of outputs from an algorithm

        :param results: the results from the algorithm
        :param algorithm: the algorithm description
        :return: None
        :raises PacmanAlgorithmFailedToCompleteException: when the algorithm\
                returns no results
        """
        if results is not None:

            # update python data objects
            for result_name in results:
                result_type = algorithm.get_type_from_output_name(result_name)
                if result_type is None:
                    raise exceptions.PacmanTypeError(
                        "Unrecognised result name {} for algorithm {} with"
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
        """

        :param item_type: the item from the internal type mapping to be\
                    returned
        :return: the returned item
        """
        return self._internal_type_mapping[item_type]

    def get_provenance_data_items(self, transceiver, placement=None):
        """
        @implements pacman.interface.abstract_provides_provenance_data.AbstractProvidesProvenanceData.get_provenance_data_items
        :return:
        """
        return self._provenance_data

    def _handle_prov(self, timer, algorithm):
        """
        adds a piece of provenance data to the list
        :param timer: the tracker of how long a algorithm has taken
        :param algorithm: the algorithm in question
        :return: None
        """
        time_taken = timer.take_sample()

        # write timing element into provenance data item
        self._provenance_data.append(ProvenanceDataItem(
            name="algorithm_{}".format(algorithm.algorithm_id),
            item=str(time_taken),
            needs_reporting_to_end_user=False))
