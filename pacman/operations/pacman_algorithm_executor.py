"""
PACMANAlgorithmExecutor
"""

# pacman imports
from pacman import exceptions
from pacman.utilities.file_format_converters.convert_algorithms_metadata \
    import ConvertAlgorithmsMetadata

# general imports
import logging
import importlib
import subprocess
import os

from pacman.utilities import file_format_converters
from pacman import utilities
from pacman import operations

logger = logging.getLogger(__name__)


class PACMANAlgorithmExecutor(object):
    """
    an executor of pacman algorithums where the order is decuded from the input
    and outputs of the algorithm based off its xml data
    """

    def __init__(self, reports_states, in_debug_mode=True):
        """
        :param reports_states: the pacman report object
        :param in_debug_mode:
        :return:
        """
        # pacman mapping objects
        self._algorithms = list()

        # define mapping between types and internal values
        self._internal_type_mapping = dict()

        # define mapping between output types and reports
        if reports_states is not None and reports_states.tag_allocation_report:
            self._algorithms.append("TagReport")
        if reports_states is not None and reports_states.routing_info_report:
            self._algorithms.append("routingInfoReports")
        if reports_states is not None and reports_states.router_report:
            self._algorithms.append("RouterReports")
        if reports_states is not None and reports_states.partitioner_report:
            self._algorithms.append("PartitionerReport")
        if (reports_states is not None and
                reports_states.placer_report_with_partitionable_graph):
            self._algorithms.append("PlacerReportWithPartitionableGraph")
        if (reports_states is not None and
                reports_states.placer_report_without_partitionable_graph):
            self._algorithms.append("PlacerReportWithoutPartitionableGraph")
        # add debug algorithms if needed
        if in_debug_mode:
            self._algorithms.append("ValidRoutesChecker")

    def set_up_pacman_algorthms_listings(self, algorithms, xml_paths, inputs,
                                         required_outputs):
        """ trnaslates the algoreithum string and uses the config xml to create
        algorithm objects

        :param algorithms: the string represnetation of the set of algorithms
        :param inputs: list of input types
        :type inputs: iterable of str
        :param xml_paths: the list of paths for xml configuration data
        :type xml_paths: iterable of strings
        :param required_outputs: the set of outputs that this workflow is meant
        to generate
        :type required_outputs: iterable of types as strings
        """

        # dedeuce if the algoruthms are internal or external
        algorithms_names = self._algorithms
        algorithm_strings = algorithms.split(",")
        for algorithm_string in algorithm_strings:
            split_string = algorithm_string.split(":")
            if len(split_string) == 1:
                algorithms_names.append(split_string[0])
            else:
                raise exceptions.PacmanConfigurationException(
                    "The tool chain expects config params of list of 1 element"
                    "with ,. Where the elements are either: the "
                    "algorithum_name:algorithm_config_file_path, or "
                    "algorithum_name if its a interal to pacman algorithm. "
                    "Please rectify this and try again")

        # set up xml reader for standard pacman algorithums xml file reader
        # (used in decode_algorithm_data_objects func)
        xml_paths.append(os.path.join(os.path.dirname(operations.__file__),
                                      "algorithms_metadata.xml"))
        xml_paths.append(os.path.join(os.path.dirname(utilities.__file__),
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
        self._algorithms = list()
        for algorithms_name in algorithms_names:
            self._algorithms.append(algorithm_data_objects[algorithms_name])

        # sort_out_order_of_algorithms for exeuction
        self._sort_out_order_of_algorithms(
            inputs, required_outputs, converter_algorithm_data_objects.values())

    def _sort_out_order_of_algorithms(
            self, inputs, required_outputs, optional_converter_algorithms):
        """
        takes the algorithms and deternmines which order they need to be
        executed to generate the correct data objects
        :param inputs: list of input types
        :type inputs: iterable of str
        :param required_outputs: the set of outputs that this workflow is meant
        to generate
        :param optional_converter_algorithms: the set of optional converter
        algorithms from memory to file formats
        :return: None
        """

        allocated_algorithums = list()
        generated_outputs = set()
        generated_outputs.union(inputs)
        allocated_a_algorithm = True
        while len(self._algorithms) != 0 and allocated_a_algorithm:
            allocated_a_algorithm = False
            # check each algorithm to see if its usable with current inputs
            suitable_algorithm = self._locate_suitable_algorithm(
                self._algorithms, inputs)

            # add the suitable algorithms to the list and take there outputs
            #  as new inputs
            if suitable_algorithm is not None:
                allocated_algorithums.append(suitable_algorithm)
                allocated_a_algorithm = True
                self._remove_algorithm_and_update_outputs(
                    self._algorithms, suitable_algorithm, inputs,
                    generated_outputs)
            else:
                suitable_algorithm = self._locate_suitable_algorithm(
                    optional_converter_algorithms, inputs)
                if suitable_algorithm is not None:
                    allocated_algorithums.append(suitable_algorithm)
                    allocated_a_algorithm = True
                    self._remove_algorithm_and_update_outputs(
                        optional_converter_algorithms, suitable_algorithm,
                        inputs, generated_outputs)
                else:
                    raise exceptions.PacmanConfigurationException(
                        "I was not able to deduce a future algortihm to use as"
                        "I only have the inputs {} and am missing the outputs "
                        "{} from the requirements of the end user. The only"
                        " avilable functions are {}. Please add a algorithm(s) "
                        "which uses the defined inputs and generates the "
                        "required outputs and rerun me. Thanks"
                        .format(
                            inputs, list(set(required_outputs) - set(inputs)),
                            self._algorithms + optional_converter_algorithms))

        all_required_outputs_generated = True
        failed_to_generate_output_string = ""
        for output in required_outputs:
            if output not in generated_outputs:
                all_required_outputs_generated = False
                failed_to_generate_output_string += ":{}".format(output)

        if not all_required_outputs_generated:
            raise exceptions.PacmanConfigurationException(
                "I was not able to generate the outputs {}. Please rectify "
                "this and try again".format(failed_to_generate_output_string))

        self._algorithms = allocated_algorithums

    @staticmethod
    def _remove_algorithm_and_update_outputs(
            algorithm_list, algorithm, inputs, generated_outputs):
        """
        updates data structures
        :param algorithm_list: the list of algorithums to remove algoruthm from
        :param algorithm: the algorithm to remove
        :param inputs: the inputs list to update output from algorithm
        :param generated_outputs: the outputs list to update output from algorithm
        :return: none
        """
        algorithm_list.remove(algorithm)
        for output in algorithm.outputs:
            inputs.add(output['type'])
            generated_outputs.add(output['type'])


    def _locate_suitable_algorithm(self, algorithm_list, inputs):
        """
        locates a suitable algorithm
        :param algorithm_list: the list of algoirthms to choose from
        :param inputs: the inputs avilable currently
        :return: a suitable algorithm which uses the inputs
        """
        position = 0
        suitable_algorithm = None
        while (suitable_algorithm is None and
                position < len(algorithm_list)):
            algorithm = algorithm_list[position]
            all_inputs_avilable = True
            for input_parameter in algorithm.inputs:
                if input_parameter['type'] not in inputs:
                    all_inputs_avilable = False
            if all_inputs_avilable and suitable_algorithm is None:
                suitable_algorithm = algorithm
            position += 1
        return suitable_algorithm

    def execute_mapping(self, inputs):
        """
        executes the algorithms
        :param inputs: the imputs stated in setup function
        :return: None
        """

        for input_parameter in inputs:
            self._internal_type_mapping[input_parameter['type']] = \
                input_parameter['value']

        for algorithm in self._algorithms:
            # exeucte the algorithm and store outputs
            if not algorithm.external:  # internal to pacman
                self._handle_internal_algorithm(algorithm)
            else:  # external to pacman
                self._handle_external_algorithm(algorithm)

    def _handle_internal_algorithm(self, algorithm):
        """
        creates the input files for the algorithm
        :param algorithm: the algorthum
        :return: None
        """
        # create algorithm
        python_algorithm = self._create_python_object(algorithm)

        # create input dictonary
        inputs = dict()
        for input_parameter in algorithm.inputs:
            inputs[input_parameter['name']] = \
                self._internal_type_mapping[input_parameter['type']]

        # execute algorithm
        results = python_algorithm(**inputs)

        # move outputs into internal data objects
        if results is not None:
            # update python data objects
            for result_name in results:
                result_type = \
                    algorithm.get_type_from_output_name(result_name)
                self._internal_type_mapping[result_type] = \
                    results[result_name]

    def _handle_external_algorithm(self, algorithm):
        """
        creates the input files for the algorithm
        :param algorithm: the algorthum
        :return: None
        """
        if (algorithm.python_class is not None or
                algorithm.python_function is not None):
            # create a algorithm for python object
            python_algorithm = self._create_python_object(algorithm)
            input_params = self._create_input_files(algorithm)
            python_algorithm(**input_params)
            self._convert_output_files(algorithm)

        else:  # none python algorithm
            input_params = self._create_input_files(algorithm)
            input_string = ""
            for param in input_params:
                input_string += "{}={} ".format(param, input_params[param])
            # execute other command
            return_code = subprocess.call(
                [algorithm.command_line_string, input_string])
            if return_code != 0:
                raise exceptions.\
                    PacmanAlgorithmFailedToCompleteException(
                        "The algorithm {} failed to complete correctly, "
                        "Due to this algorithm being outside of the "
                        "software stacks defaultly supported algorthims,"
                        " we refer to the algorthm builder to rectify this.")
            self._convert_output_files(algorithm)

    @staticmethod
    def _create_python_object(algorithm):
        """
        creates the python algorithum from the spec
        :param algorithm: the algorithm spec
        :return: an instantated object for the algorithm
        """
        # import the python module to run
        if (algorithm.python_class is not None and
                algorithm.python_function is None):
            # if class, instansisate it
            python_algorithm = getattr(
                importlib.import_module(algorithm.python_module_import),
                algorithm.python_class)
            # create instanation of the algorithm to run
            python_algorithm = python_algorithm()
        elif (algorithm.python_function is not None and
                algorithm.python_class is None):
            # just a function, so no instantation required
            python_algorithm = getattr(
                importlib.import_module(algorithm.python_module_import),
                algorithm.python_function)
        else: # nither, but is a python object.... error
            raise exceptions.PacmanConfigurationException(
                "The algorithm {}, was deduced to be a internal "
                "algorithm and yet has resulted in no class or "
                "function definition. This makes the auto exeuction "
                "impossible. Please fix and try again."
                .format(algorithm.algorithm_id))
        return python_algorithm

    def get_item(self, item_type):
        """

        :param item_type:
        :return:
        """
        return self._internal_type_mapping[item_type]
