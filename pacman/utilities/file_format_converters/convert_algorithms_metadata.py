"""
ConvertAlgorithmsMetadata
"""

from pacman import operations
from pacman.utilities.algorithm_utilities.algorithm_data import AlgorithmData
from pacman import utilities
from pacman import exceptions

from lxml import etree
import os


class ConvertAlgorithmsMetadata(object):
    """
    ConvertAlgorithmsMetadata that converts a xml file into algorithm data
    """

    def __init__(self, xml_paths):
        """
        constructor
        :param xml_paths: paths to extra metadata files
        :return:
        """
        self._xml_paths = xml_paths

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
        command_line_args = element.find("command_line_args")
        if command_line_args is not None:
            command_line_args = self._translate_args(command_line_args)
        python_module = element.find("python_module")
        if python_module is not None:
            python_module = python_module.text
        python_class = element.find("python_class")
        if python_class is not None:
            python_class = python_class.text
        python_function = element.find("python_function")
        if python_function is not None:
            python_function = python_function.text

        if python_module is None and command_line_args is not None:
            external = True
        elif python_module is not None and command_line_args is None:
            external = False
        elif ((python_module is None and command_line_args is None) or
                (python_module is not None and command_line_args is not None)):
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
            algorithm_id=element.get('name'),
            command_line_args=command_line_args, inputs=required_inputs,
            optional_inputs=optional_inputs, outputs=outputs, external=external,
            python_import=python_module, python_class=python_class,
            python_function=python_function)

    @staticmethod
    def _translate_args(args_element):
        """
        converts a xml arg element into a list of args
        :param args_element:
        :return:
        """
        translated_args = list()
        if args_element is not None:
            args = args_element.findall("arg")
            for arg in args:
                translated_args.append(arg.text)
        # return none if empty
        if len(translated_args) == 0:
            return None
        else:
            return translated_args

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
