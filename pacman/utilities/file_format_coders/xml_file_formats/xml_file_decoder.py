"""
XMLFileDecoder for decoder for XML files into python objects
"""
from pacman.utilities.file_format_coders.abstract_coders.\
    abstract_format_decoder import AbstractFormatDecoder
from pacman import exceptions

from pacman import operations
from pacman.utilities.algorithm_utilities.algorithm_data import AlgorithmData
from pacman import utilities

from lxml import etree
import os


class XMLFileDecoder(AbstractFormatDecoder):
    """
    XMLFileDecoder:  decoder for XML files into python objects
    """

    def __init__(self, folder_path, xml_paths):
        AbstractFormatDecoder.__init__(self)
        self._xml_paths = None
        self._folder_path = folder_path
        # set up xml reader for standard pacman algorithums xml file reader
        # (used in decode_algorithm_data_objects func)
        xml_paths.append(os.path.join(os.path.dirname(operations.__file__),
                                      "algorithms_metadata.xml"))
        xml_paths.append(os.path.join(os.path.dirname(utilities.__file__),
                                      "reports_metadata.xml"))
        self._xml_paths = xml_paths

    def decode_placements(self):
        """
        :return: placement object
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitionable_graph_constraints(self):
        """

        :return: partitionable graph constraints
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitioned_graph(self):
        """

        :return:return a partitioned graph object
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_tags(self):
        """
        return tags object
        :return:
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitioned_graph_constraints(self):
        """
        returns a partitioned graph's constraints
        :return:
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_tables(self):
        """

        :return: returns the routing tables
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_machine(self):
        """

        :return: returns the machine object
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitionable_graph(self):
        """

        :return: return the partitionable graph
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_paths(self):
        """

        :return: returns the routing paths
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_infos(self):
        """

        :return: returns the routing infos
        """
        raise exceptions.PacmanException("Not implimented yet")

    def decode_algorithm_data_objects(self):
        """

        :return: returns the algorithm data objects which represent all the
        algorithms for inputs and outputs
        """
        # parse xmls
        xml_roots = list()
        for xml_path in self._xml_paths:
            xml_roots.append(etree.parse(xml_path))

        algorithm_data_objects = dict()
        for xml_root in xml_roots:
            elements = xml_root.findall(".//algorithm")
            for element in elements:
                if element.get('name') in algorithm_data_objects:
                    raise exceptions.PacmanConfigurationException(
                        "There are two algorithms with the same name in these"
                        "xml files {}. Please rectify and try again."
                        .format(self._xml_paths))
                else:
                    algorithm_data_objects[element.get('name')] = \
                        self._generate_algorithm_data(element)
        return algorithm_data_objects

    def _generate_algorithm_data(self, element):
        """
        takes the xml elements and translaters them into tuples for the
        AlgorithmData object
        :param element: the lxml element to translate
        :return: a AlgorithmData
        """
        # convert lxml elemtnts into dicts or strings
        external = False
        # verify if its a internal or extenral via if it is import-able or
        # command line based
        command_line = element.find("command_line_command")
        if command_line is not None:
            command_line = command_line.text
        python_module = element.find("python_module")
        if python_module is not None:
            python_module = python_module.text
        python_class = element.find("python_class")
        if python_class is not None:
            python_class = python_class.text
        python_function = element.find("python_function")
        if python_function is not None:
            python_function = python_function.text

        if python_module is None and command_line is not None:
            external = True
        elif python_module is not None and command_line is None:
            external = False
        elif ((python_module is None and command_line is None) or
                (python_module is not None and command_line is not None)):
            raise exceptions.PacmanConfigurationException(
                "Cannot deduce what to do when either both command line and "
                "python mudle are none or are filled in. Please rectify and "
                "try again")

        # get other params
        required_inputs = \
            self._translate_parameters(element.find("required_inputs"))
        optional_inputs = \
            self._translate_parameters(element.find("optional_inputs"))
        outputs = \
            self._translate_parameters(element.find("produces_outputs"))
        return AlgorithmData(
            algorithm_id=element.get('name'), command_line_string=command_line,
            inputs=required_inputs, optional_inputs=optional_inputs,
            outputs=outputs, external=external, python_import=python_module,
            python_class=python_class, python_function=python_function)

    @staticmethod
    def _translate_parameters(parameters_element):
        """
        converts a xml parameter element into a dict
        :param parameters_element:
        :return:
        """
        translated_params = list()
        if parameters_element is not None:
            parameters = parameters_element.findall("parameter")
            for parameter in parameters:
                translated_params.append(
                    {'name': parameter.find("param_name").text,
                     'type': parameter.find("param_type").text})
        return translated_params

