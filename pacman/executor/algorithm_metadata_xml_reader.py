from lxml import etree
from six import iterkeys

from pacman.exceptions import PacmanConfigurationException
from pacman.executor.algorithm_decorators import OneOfInput
from pacman.executor.algorithm_decorators import Output
from pacman.executor.algorithm_classes import PythonFunctionAlgorithm
from pacman.executor.algorithm_decorators import SingleInput
from pacman.executor.algorithm_classes import ExternalAlgorithm
from pacman.executor.algorithm_classes import PythonClassAlgorithm
from pacman.executor.algorithm_decorators import AllOfInput
from pacman.executor.algorithm_decorators.token import Token


def _check_allowed_elements(path, element, allowed):
    if any(sub.tag.split("}")[-1] not in allowed
           for sub in element.iterchildren()):
        raise PacmanConfigurationException(
            "Error in XML starting at line {} of {}: Only"
            " one of {} is allowed in {}".format(
                element.sourceline, path, allowed, element.tag))


class _XmlConfigurationException(PacmanConfigurationException):
    def __init__(self, element, path, problem, algorithm_name=None):
        if algorithm_name is None:
            msg = "Error in algorithm definition starting on " \
                "line {} of {}: {}".format(
                    element.sourceline, path, problem)
        else:
            msg = "Error in algorithm {} specification starting on " \
                "line {} of {}: {}".format(
                    algorithm_name, element.sourceline, path, problem)
        super(_XmlConfigurationException, self).__init__(msg)


class AlgorithmMetadataXmlReader(object):
    """ Converts an XML file into algorithm data.
    """

    __slots__ = [
        # paths to extra metadata files
        "_xml_paths"
    ]

    def __init__(self, xml_paths):
        """
        :param xml_paths: paths to extra metadata files
        :rtype: None
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
            for element in xml_root.findall("{*}algorithm"):
                name = element.get('name')
                if name in algorithm_data_objects:
                    raise PacmanConfigurationException(
                        "There are two algorithms with the same name {}"
                        " in these xml files {}. Please rectify and try again."
                        .format(name, files_read_so_far))
                algorithm_data_objects[name] = \
                    self._generate_algorithm_data(xml_path, element)
        return algorithm_data_objects

    def _generate_algorithm_data(self, path, element):
        """ Translates XML elements into tuples for the AbstractAlgorithm object

        :param element: the xml element to translate
        :return: a AbstractAlgorithm
        """
        _check_allowed_elements(path, element, {
            "input_definitions", "required_inputs", "optional_inputs",
            "outputs", "command_line_args", "python_module", "python_class",
            "python_method", "python_function", "required_input_tokens",
            "generated_output_tokens"})

        algorithm_id = element.get('name')
        if algorithm_id is None:
            raise PacmanConfigurationException(
                "Missing algorithm_id in algorithm definition starting on"
                " line {} of {}".format(element.sourceline, path))

        # Determine the type of the algorithm and return the appropriate type
        is_external = False
        command_line_args = element.find("{*}command_line_args")
        if command_line_args is not None:
            command_line_args = self._translate_args(path, command_line_args)
            is_external = True
        python_module = element.find("{*}python_module")
        if python_module is not None:
            python_module = python_module.text.strip()
        python_class = element.find("{*}python_class")
        if python_class is not None:
            python_class = python_class.text.strip()
        python_function = element.find("{*}python_function")
        if python_function is not None:
            python_function = python_function.text.strip()
        python_method = element.find("{*}python_method")
        if python_method is not None:
            python_method = python_method.text.strip()

        # Get the input definitions
        input_defs = element.find("{*}input_definitions")
        if input_defs is None:
            raise PacmanConfigurationException(
                "Missing input_definitions in algorithm definition starting on"
                " line {} of {}".format(element.sourceline, path))
        input_definitions = self._translate_input_definitions(path, input_defs)

        # get other params
        required_inputs_elem = element.find("{*}required_inputs")
        required_inputs, required_seen, required_tokens = \
            self._translate_inputs(
                path, algorithm_id, required_inputs_elem, input_definitions,
                allow_tokens=True)
        optional_inputs_elem = element.find("{*}optional_inputs")
        optional_inputs, optional_seen, optional_tokens = \
            self._translate_inputs(
                path, algorithm_id, optional_inputs_elem, input_definitions,
                allow_tokens=True)
        outputs, output_tokens = self._translate_outputs(
            path, element.find("{*}outputs"), is_external)

        # Check that all input definitions have been used
        for input_name in iterkeys(input_definitions):
            if (input_name not in required_seen and
                    input_name not in optional_seen):
                raise _XmlConfigurationException(
                    element, path,
                    "input_definitions contains parameter {} but it is not"
                    " required or optional".format(input_name))

        if command_line_args is not None:
            if (python_module is not None or python_class is not None or
                    python_function is not None or python_method is not None):
                raise _XmlConfigurationException(
                    element, path, algorithm_name=algorithm_id,
                    problem="command_line_args can not be specified with "
                    "python_module, python_class, python_function or "
                    "python_method")
            return ExternalAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                required_tokens, optional_tokens, output_tokens,
                command_line_args)

        if python_module is not None and python_function is not None:
            if (python_class is not None or python_method is not None):
                raise _XmlConfigurationException(
                    element, path, algorithm_name=algorithm_id,
                    problem="python_function can not be specified with "
                    "python_class or python_method")
            return PythonFunctionAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                required_tokens, optional_tokens, output_tokens,
                python_module, python_function)

        if python_module is not None and python_class is not None:
            return PythonClassAlgorithm(
                algorithm_id, required_inputs, optional_inputs, outputs,
                required_tokens, optional_tokens, output_tokens,
                python_module, python_class, python_method)

        raise _XmlConfigurationException(
            element, path, algorithm_name=algorithm_id,
            problem="One of command_line_args, "
            "[python_module, python_function] or "
            "[python_module, python_class, [python_method]] must be "
            "specified")

    @staticmethod
    def _translate_args(path, args_element):
        """ Convert an XML arg element into a list of args

        :param args_element:
        """
        translated_args = list()
        if args_element is not None:
            _check_allowed_elements(path, args_element, {"arg"})
            args = args_element.findall("{*}arg")
            for arg in args:
                translated_args.append(arg.text.strip())

        # return none if empty
        if translated_args:
            return translated_args
        return None

    @staticmethod
    def _translate_input_definitions(path, defs_element):
        """ Convert the XML input definitions section into a dict of\
            name to AbstractInput
        """
        definitions = dict()
        if defs_element is not None:
            _check_allowed_elements(path, defs_element, {"parameter"})
            parameters = defs_element.findall("{*}parameter")
            for parameter in parameters:
                _check_allowed_elements(path, parameter, {
                    "param_name", "param_type"})
                param_name = parameter.find("{*}param_name").text.strip()
                param_types = [
                    param_type.text.strip()
                    for param_type in parameter.findall("{*}param_type")]
                definitions[param_name] = SingleInput(param_name, param_types)
        return definitions

    def _translate_inputs(
            self, path, algorithm_id, inputs_element, definitions,
            allow_tokens=False):
        """ Convert an XML inputs section (required or optional) into a list\
            of AbstractInput
        """
        inputs = list()
        seen_inputs = set()
        tokens = set()
        if inputs_element is not None:
            allowed_elements = {"param_name", "one_of", "all_of"}
            if allow_tokens:
                allowed_elements.add("token")
            _check_allowed_elements(path, inputs_element, allowed_elements)
            for alg_input in inputs_element.iterchildren():
                tag = alg_input.tag.split("}")[-1]
                if tag == "param_name":
                    definition = definitions.get(alg_input.text.strip(), None)
                    if definition is None:
                        raise _XmlConfigurationException(
                            alg_input, path,
                            "{} section references the parameter {} but this "
                            "was not defined in input_definitions".format(
                                inputs_element.tag, alg_input.text.strip()))
                    inputs.append(definition)
                    seen_inputs.add(definition.name)
                elif tag == "one_of":
                    children, seen, _ = self._translate_inputs(
                        path, algorithm_id, alg_input, definitions)
                    seen_inputs.update(seen)
                    inputs.append(OneOfInput(children))
                elif tag == "all_of":
                    children, seen, _ = self._translate_inputs(
                        path, algorithm_id, alg_input, definitions)
                    seen_inputs.update(seen)
                    inputs.append(AllOfInput(children))
                elif tag == "token":
                    part = alg_input.get("part", default=None)
                    name = alg_input.text.strip()
                    tokens.add(Token(name, part))
        return inputs, seen_inputs, tokens

    @staticmethod
    def _translate_outputs(path, outputs_element, is_external):
        """ Convert an XML outputs section into a list of str
        """
        outputs = list()
        tokens = set()
        if outputs_element is not None:
            _check_allowed_elements(
                path, outputs_element, {"param_type", "token"})
            for alg_output in outputs_element.iterchildren():
                tag = alg_output.tag.split("}")[-1]
                if tag == "param_type":
                    file_name_type = alg_output.get(
                        "file_name_type", default=None)
                    if is_external and file_name_type is None:
                        raise _XmlConfigurationException(
                            alg_output, path,
                            "outputs of external algorithms must specify the "
                            "input type from which the file name will be "
                            "obtained using the file_name_type attribute")
                    outputs.append(
                        Output(alg_output.text.strip(), file_name_type))
                elif tag == "token":
                    part = alg_output.get("part", default=None)
                    name = alg_output.text.strip()
                    tokens.add(Token(name, part))
        return outputs, tokens
