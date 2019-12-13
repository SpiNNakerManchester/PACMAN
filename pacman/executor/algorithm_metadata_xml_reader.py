# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lxml import etree
from pacman.exceptions import PacmanConfigurationException
from pacman.executor.algorithm_decorators import (
    AllOfInput, OneOfInput, Output, SingleInput, Token)
from pacman.executor.algorithm_classes import (
    ExternalAlgorithm, PythonClassAlgorithm, PythonFunctionAlgorithm)
# pylint: disable=c-extension-no-member


class _XmlConfigurationException(PacmanConfigurationException):
    def __init__(self, element, path, problem, algorithm_name=None):
        """
        :param lxml.etree.ElementBase element:
        :param str path:
        :param str problem:
        :param algorithm_name:
        :type algorithm_name: str or None
        """
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
        "_xml_paths",
        # current path
        "_xml_path"
    ]

    def __init__(self, xml_paths):
        """
        :param list(str) xml_paths: paths to extra metadata files
        :rtype: None
        """
        self._xml_paths = xml_paths

    def _check_allowed_elements(self, element, allowed):
        """
        :param lxml.etree.ElementBase element:
        :param set(str) allowed:
        :raises PacmanConfigurationException:
        """
        if any(sub.tag.split("}")[-1] not in allowed
               for sub in element.iterchildren()):
            raise PacmanConfigurationException(
                "Error in XML starting at line {} of {}: Only"
                " one of {} is allowed in {}".format(
                    element.sourceline, self._xml_path, allowed, element.tag))

    def decode_algorithm_data_objects(self):
        """
        :return: the algorithm data objects which represent all the
            algorithm's inputs and outputs
        :rtype: dict(str, AbstractAlgorithm)
        :raises PacmanConfigurationException:
        """
        # parse xmls
        algorithms = dict()
        files_read_so_far = list()
        for self._xml_path in self._xml_paths:
            xml_root = etree.parse(self._xml_path)
            files_read_so_far.append(self._xml_path)
            for element in xml_root.findall("{*}algorithm"):
                name = element.get('name')
                if name in algorithms:
                    raise PacmanConfigurationException(
                        "There are two algorithms with the same name {}"
                        " in these XML files {}. Please rectify and try again."
                        .format(name, files_read_so_far))
                algorithms[name] = self._parse_algorithm(element)
        return algorithms

    def _parse_algorithm(self, element):
        """ Translates XML elements into tuples for the AbstractAlgorithm object

        :param lxml.etree.ElementBase element: the XML element to translate
        :rtype: AbstractAlgorithm
        :raises PacmanConfigurationException:
        """
        self._check_allowed_elements(element, {
            "input_definitions", "required_inputs", "optional_inputs",
            "outputs", "command_line_args", "python_module", "python_class",
            "python_method", "python_function", "required_input_tokens",
            "generated_output_tokens"})

        algorithm_id = element.get('name')
        if algorithm_id is None:
            raise PacmanConfigurationException(
                "Missing algorithm_id in algorithm definition starting on"
                " line {} of {}".format(element.sourceline, self._xml_path))

        # Determine the type of the algorithm and return the appropriate type
        is_external = False
        command_line_args = element.find("{*}command_line_args")
        if command_line_args is not None:
            command_line_args = self._translate_args(command_line_args)
            is_external = True
        py_module = self.__text(element, "{*}python_module")
        py_class = self.__text(element, "{*}python_class")
        py_function = self.__text(element, "{*}python_function")
        py_method = self.__text(element, "{*}python_method")

        # Get the input definitions
        input_defs = element.find("{*}input_definitions")
        if input_defs is None:
            raise PacmanConfigurationException(
                "Missing input_definitions in algorithm definition starting on"
                " line {} of {}".format(element.sourceline, self._xml_path))
        input_definitions = self._translate_input_definitions(input_defs)

        # get other params
        seen = set()  # Accumulate what inputs have been seen
        req_inputs, req_tokens = self._translate_inputs(
            algorithm_id, element.find("{*}required_inputs"),
            input_definitions, seen, allow_tokens=True)
        opt_inputs, opt_tokens = self._translate_inputs(
            algorithm_id, element.find("{*}optional_inputs"),
            input_definitions, seen, allow_tokens=True)
        outputs, output_tokens = self._translate_outputs(
            element.find("{*}outputs"), is_external)

        # Check that all input definitions have been used
        for input_name in input_definitions:
            if input_name not in seen:
                raise _XmlConfigurationException(
                    element, self._xml_path,
                    "input_definitions contains parameter {} but it is not"
                    " required or optional".format(input_name))

        if command_line_args is not None:
            if py_module or py_class or py_function or py_method:
                raise _XmlConfigurationException(
                    element, self._xml_path, algorithm_name=algorithm_id,
                    problem="command_line_args can not be specified with "
                    "python_module, python_class, python_function or "
                    "python_method")
            return ExternalAlgorithm(
                algorithm_id, req_inputs, opt_inputs, outputs,
                req_tokens, opt_tokens, output_tokens, command_line_args)

        if py_module and py_function:
            if py_class or py_method:
                raise _XmlConfigurationException(
                    element, self._xml_path, algorithm_name=algorithm_id,
                    problem="python_function can not be specified with "
                    "python_class or python_method")
            return PythonFunctionAlgorithm(
                algorithm_id, req_inputs, opt_inputs, outputs,
                req_tokens, opt_tokens, output_tokens,
                py_module, py_function)

        if py_module and py_class:
            return PythonClassAlgorithm(
                algorithm_id, req_inputs, opt_inputs, outputs,
                req_tokens, opt_tokens, output_tokens,
                py_module, py_class, py_method)

        raise _XmlConfigurationException(
            element, self._xml_path, algorithm_name=algorithm_id,
            problem="One of command_line_args, "
            "[python_module, python_function] or "
            "[python_module, python_class, [python_method]] must be "
            "specified")

    def _translate_args(self, args_element):
        """ Convert an XML arg element into a list of args

        :param lxml.etree.ElementBase args_element:
        :rtype: list(str)
        :raises PacmanConfigurationException:
        """
        if args_element is None:
            return None

        self._check_allowed_elements(args_element, {"arg"})
        translated_args = self.__all_text(args_element, "{*}arg")

        # return none if empty
        if translated_args:
            return translated_args
        return None

    def _translate_input_definitions(self, defs_element):
        """ Convert the XML input definitions section into a dict of
            name to AbstractInput

        :param lxml.etree.ElementBase defs_element:
        :rtype: dict(str, SingleInput)
        :raises PacmanConfigurationException:
        """
        definitions = dict()
        if defs_element is not None:
            self._check_allowed_elements(defs_element, {"parameter"})
            for parameter in defs_element.findall("{*}parameter"):
                self._check_allowed_elements(parameter, {
                    "param_name", "param_type"})
                param_name = self.__text(parameter, "{*}param_name")
                param_types = self.__all_text(parameter, "{*}param_type")
                definitions[param_name] = SingleInput(param_name, param_types)
        return definitions

    def _translate_inputs(
            self, algorithm_id, inputs_element, definitions, seen_names,
            allow_tokens=False):
        """ Convert an XML inputs section (required or optional) into a list
            of AbstractInput

        :param str algorithm_id:
        :param lxml.etree.ElementBase inputs_element:
        :param dict(str,SingleInput) definitions:
        :param set(str) seen_names:
        :param bool allow_tokens:
        :return: inputs, tokens
        :rtype: tuple(list(AbstractInput), set(Token))
        :raises PacmanConfigurationException:
        """
        if inputs_element is None:
            return [], set()

        inputs = list()
        tokens = set()
        allowed_elements = {"param_name", "one_of", "all_of"}
        if allow_tokens:
            allowed_elements.add("token")
        self._check_allowed_elements(inputs_element, allowed_elements)
        for alg_input in inputs_element.iterchildren():
            tag = alg_input.tag.split("}")[-1]
            if tag == "param_name":
                name = alg_input.text.strip()
                definition = definitions.get(name, None)
                if definition is None:
                    raise _XmlConfigurationException(
                        alg_input, self._xml_path,
                        "{} section references the parameter {} but this "
                        "was not defined in input_definitions".format(
                            inputs_element.tag, name))
                inputs.append(definition)
                seen_names.add(name)
            elif tag == "one_of":
                children, _ = self._translate_inputs(
                    algorithm_id, alg_input, definitions, seen_names)
                inputs.append(OneOfInput(children))
            elif tag == "all_of":
                children, _ = self._translate_inputs(
                    algorithm_id, alg_input, definitions, seen_names)
                inputs.append(AllOfInput(children))
            elif tag == "token":
                tokens.add(self._translate_token(alg_input))
        return inputs, tokens

    def _translate_outputs(self, outputs_element, is_external):
        """ Convert an XML outputs section into a list of str

        :param lxml.etree.ElementBase outputs_element:
        :param bool is_external:
        :return: outputs, tokens
        :rtype: tuple(list(Output), set(Token))
        :raises PacmanConfigurationException:
        """
        outputs = list()
        tokens = set()
        if outputs_element is not None:
            self._check_allowed_elements(
                outputs_element, {"param_type", "token"})
            for alg_output in outputs_element.iterchildren():
                tag = alg_output.tag.split("}")[-1]
                if tag == "param_type":
                    file_name_type = alg_output.get(
                        "file_name_type", default=None)
                    if is_external and file_name_type is None:
                        raise _XmlConfigurationException(
                            alg_output, self._xml_path,
                            "outputs of external algorithms must specify the "
                            "input type from which the file name will be "
                            "obtained using the file_name_type attribute")
                    outputs.append(
                        Output(alg_output.text.strip(), file_name_type))
                elif tag == "token":
                    tokens.add(self._translate_token(alg_output))
        return outputs, tokens

    @staticmethod
    def _translate_token(token_element):
        """
        :param lxml.etree.ElementBase token_element: The token element
        :rtype: Token
        """
        part = token_element.get("part", default=None)
        name = token_element.text.strip()
        return Token(name, part)

    @staticmethod
    def __text(element, xpath):
        """
        :param lxml.etree.ElementBase element: the XML element to search from
        :param str xpath:
        :rtype: str or None
        """
        e = element.find(xpath)
        return None if e is None else e.text.strip()

    @staticmethod
    def __all_text(element, xpath):
        """
        :param lxml.etree.ElementBase element: the XML element to search from
        :param str xpath:
        :rtype: list(str)
        """
        return [e.text.strip() for e in element.findall(xpath)]
