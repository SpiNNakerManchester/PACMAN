"""
PACMANAlgorithmExecutor
"""

# pacman imports
from pacman import exceptions
from pacman.utilities.file_format_coders.xml_file_formats.xml_file_decoder\
    import XMLFileDecoder

# general imports
import logging
import importlib

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

        # define mapping between types and expected file names
        self._external_type_mapping = dict()
        self._external_type_mapping["Tags"] = "tag_data"
        self._external_type_mapping['RoutingTables'] = "router_table_data"
        self._external_type_mapping['RoutingInfos'] = "routing_key_data"
        self._external_type_mapping['RoutingPaths'] = "routing_paths_data"
        self._external_type_mapping['AbstractPartitionedEdgeNKeysMap'] = \
            "edges_to_key_data"
        self._external_type_mapping['Placements'] = "placement_data"
        self._external_type_mapping['PartitionedGraph'] = \
            "partitioned_graph_data"
        self._external_type_mapping['GraphMapper'] = "graph_mapper_data"

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

        # decode the algorithms specs
        xml_decoder = XMLFileDecoder(None, xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()

        # filter for just algorithms we want to use
        self._algorithms = list()
        for algorithms_name in algorithms_names:
            self._algorithms.append(algorithm_data_objects[algorithms_name])

        # sort_out_order_of_algorithms for exeuction
        self._sort_out_order_of_algorithms(inputs, required_outputs)

    def _sort_out_order_of_algorithms(self, inputs, required_outputs):
        """
        takes the algorithms and deternmines which order they need to be
        executed to generate the correct data objects
        :param inputs: list of input types
        :type inputs: iterable of str
        :param required_outputs: the set of outputs that this workflow is meant
        to generate
        :return: None
        """

        allocated_algorithums = list()
        generated_outputs = list()
        generated_outputs.extend(inputs)
        allocated_a_algorithm = True
        while len(self._algorithms) != 0 and allocated_a_algorithm:
            allocated_a_algorithm = False
            suitable_algorithm = None
            # check each algorithm to see if its usable with current inputs
            position = 0
            while (suitable_algorithm is None and
                    position < len(self._algorithms)):
                algorithm = self._algorithms[position]
                all_inputs_avilable = True
                for input_parameter in algorithm.inputs:
                    if input_parameter['type'] not in inputs:
                        all_inputs_avilable = False
                if all_inputs_avilable and suitable_algorithm is None:
                    suitable_algorithm = algorithm
                position += 1
            # add the suitable algorithms to the list and take there outputs
            #  as new inputs
            if suitable_algorithm is not None:
                allocated_algorithums.append(algorithm)
                self._algorithms.remove(algorithm)
                allocated_a_algorithm = True
                for output in algorithm.outputs:
                    inputs.append(output['type'])
                    generated_outputs.append(output['type'])

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
            if not algorithm.external: # internal to pacman
                # create algorithm
                python_algorithm = self._create_python_object(algorithm)

                # create input dictonary
                inputs = dict()
                for input_parameter in algorithm.inputs:
                    inputs[input_parameter['name']] = \
                        self._internal_type_mapping[input_parameter['type']]

                # execute algorithm
                results = python_algorithm(**inputs)
                if results is not None:

                    # update python data objects
                    for result_name in results:
                        result_type = \
                            algorithm.get_type_from_output_name(result_name)
                        self._internal_type_mapping[result_type] = \
                            results[result_name]
            else:  # external to pacman
                if (algorithm.python_class is not None or
                        algorithm.python_function is not None):

                    # create a algorithm for python object
                    python_algorithm = self._create_python_object(algorithm)
                    self._create_input_files(algorithm)
                    python_algorithm(**inputs)
                    self._convert_output_files(algorithm)

                else:  # none python algorithm
                    self._create_input_files(algorithm)
                    #execute
                    self._convert_output_files(algorithm)

    def _create_input_files(self, algorithm):
        """
        creates the input files for the algorithm
        :param algorithm: the algorthum
        :return:
        """


    def _convert_output_files(self, algorithm):
        """
        decodes the output files from the algorithm
        :param algorithm:
        :return: the algorithm
        """

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
        else:
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
