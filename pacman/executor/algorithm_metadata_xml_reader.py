from pacman import exceptions
from pacman.executor.single_input import SingleInput
from pacman.executor.one_of_input import OneOfInput
from pacman.executor.all_of_input import AllOfInput
from pacman.executor.external_algorithm import ExternalAlgorithm
from pacman.executor.python_function_algorithm import PythonFunctionAlgorithm
from pacman.executor.python_class_algorithm import PythonClassAlgorithm

from lxml import etree


class AlgorithmMetadataXmlReader(object):
    """ Converts an XML file into algorithm data
    """

    def __init__(self, xml_paths):
        """
        :param xml_paths: paths to extra metadata files
        :return:
        """
        self._xml_paths = xml_paths

    def decode_algorithm_data_objects(self):
        """

        :return: the algorithm data objects which represent all the\
                    algorithm's inputs and outputs
        """
        # parse xmls
        algorithm_data_objects = dict()
        files_read_so_far = list()
        for xml_path in self._xml_paths:
            xml_root = etree.parse(xml_path)
            files_read_so_far.append(xml_path)
            elements = xml_root.findall(".//algorithm")
            for element in elements:
                if element.get('name') in algorithm_data_objects:
                    raise exceptions.PacmanConfigurationException(
                        "There are two algorithms with the same name {}"
                        " in these xml files {}. Please rectify and try again."
                        .format(element.get("name"), files_read_so_far))
                else:
                    algorithm_data_objects[element.get('name')] = \
                        self._generate_algorithm_data(element)
        return algorithm_data_objects

    def _generate_algorithm_data(self, element):
        """ Translates XML elements into tuples for the AbstractAlgorithm object

        :param element: the xml element to translate
        :return: a AbstractAlgorithm
        """
        algorithm_id = element.get('name')

        # Get the input definitions
        input_definitions = self._translate_input_definitions(
            element.find("input_definitions"))

        # get other params
        required_inputs = self._translate_inputs(
            algorithm_id, element.find("required_inputs"), input_definitions)
        optional_inputs = self._translate_inputs(
            algorithm_id, element.find("optional_inputs"), input_definitions)
        outputs = self._translate_outputs(element.find("outputs"))

        # Determine the type of the algorithm and return the appropriate type
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
        python_method = element.find("python_method")
        if python_method is not None:
            python_method = python_method.text

        if command_line_args is not None:
            if (python_module is not None or python_class is not None or
                    python_function is not None or python_method is not None):
                raise exceptions.PacmanConfigurationException(
                    "Error in algorithm {} specification: command_line_args"
                    " can not be specified with python_module, python_class,"
                    " python_function or python_method".format(
                        algorithm_id))
            return ExternalAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                command_line_args)

        if python_module is not None and python_function is not None:
            if (python_class is not None or python_method is not None):
                raise exceptions.PacmanConfigurationException(
                    "Error in algorithm {} specification: python_function can"
                    " not be specified with python_class or python_method"
                    .format(algorithm_id))
            return PythonFunctionAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                python_module, python_function)

        if python_module is not None and python_class is not None:
            return PythonClassAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                python_module, python_class, python_method)

        raise exceptions.PacmanConfigurationException(
            "Error in algorithm {} specification: One of command_line_args,"
            " [python_module, python_function] or"
            " [python_module, python_class, [python_method]]"
            " must be specified".format(algorithm_id))

    @staticmethod
    def _translate_args(args_element):
        """ Convert an XML arg element into a list of args

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
    def _translate_input_definitions(defs_element):
        """ Convert the XML input definitions section into a dict of\
            name to AbstractInput
        """
        definitions = dict()
        if defs_element is not None:
            parameters = defs_element.findall("parameter")
            for parameter in parameters:
                param_name = parameter.find("param_name").text
                param_types = [
                    param_type.text
                    for param_type in parameter.findall("param_type")
                ]
                is_file = bool(parameter.get("is_file", default="False"))
                definitions[param_name] = SingleInput(
                    param_name, param_types, is_file)
        return definitions

    @staticmethod
    def _translate_inputs(algorithm_id, inputs_element, definitions):
        """ Convert an XML inputs section (required or optional) into a list\
            of AbstractInput
        """
        inputs = list()
        if inputs_element is not None:
            for alg_input in inputs_element.iterchildren():
                if alg_input.tag == "param_name":
                    definition = definitions.get(alg_input.text, None)
                    if definition is None:
                        raise exceptions.PacmanConfigurationException(
                            "Error in XML for algorithm {}: {} section"
                            " references the parameter {} but this was not"
                            " defined in input_definitions".format(
                                algorithm_id, inputs_element.tag,
                                alg_input.text))
                    inputs.append(definition)
                elif alg_input.tag == "one_of":
                    children = AlgorithmMetadataXmlReader._translate_inputs(
                        algorithm_id, alg_input, definitions)
                    inputs.append(OneOfInput(children))
                elif alg_input.tag == "all_of":
                    children = AlgorithmMetadataXmlReader._translate_inputs(
                        algorithm_id, alg_input, definitions)
                    inputs.append(AllOfInput(children))
        return inputs

    @staticmethod
    def _translate_outputs(outputs_element):
        """ Convert an XML outputs section into a list of str
        """
        return [elem.text for elem in outputs_element.findall("param_type")]
