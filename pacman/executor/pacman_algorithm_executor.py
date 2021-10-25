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

import logging
from collections import defaultdict
from itertools import chain
from spinn_utilities.log import FormatAdapter
from spinn_utilities.timer import Timer
from pacman.exceptions import PacmanConfigurationException
from pacman import operations
from .injection_decorator import injection_context
from .algorithm_decorators import (
    scan_packages, get_algorithms, Token)
from .algorithm_metadata_xml_reader import AlgorithmMetadataXmlReader
from pacman.executor.token_states import TokenStates

logger = FormatAdapter(logging.getLogger(__name__))


class PACMANAlgorithmExecutor(object):
    """ An executor of PACMAN algorithms where the order is deduced from the\
        input and outputs of the algorithm using an XML description of the\
        algorithm.
    """

    __slots__ = [

        # The timing of algorithms
        "_algorithm_timings",

        # The algorithms to run
        "_algorithms",

        # The inputs passed in from the user
        "_inputs",

        # The completed output tokens
        "_completed_tokens",

        # The type mapping as things flow from input to output
        "_internal_type_mapping",

        # True if timing is to be done
        "_do_timing",

        # True if timing is to be printed
        "_print_timings",

        # True if direct injection is to be done
        "_do_direct_injection",

        # the flag in the provenance area.
        "_provenance_name",

        # If required a file path to append provenance data to
        "_provenance_path",

        "__algorithm_data",
        "__optional_algorithm_data",
    ]

    def __init__(
            self, algorithms, optional_algorithms, inputs, required_outputs,
            tokens, required_output_tokens, xml_paths=None, packages=None,
            do_timings=True, print_timings=False,
            do_direct_injection=True, use_unscanned_annotated_algorithms=True,
            provenance_path=None, provenance_name=None):
        """
        :param list(str) algorithms: A list of algorithms that must all be run
        :param list(str) optional_algorithms:
            A list of algorithms that must be run if their inputs are available
        :param inputs: A dict of input type to value
        :type inputs: dict(str, ...)
        :param list(str) required_outputs:
            A list of output types that must be generated
        :param list(str) tokens:
            A list of tokens that should be considered to have been generated
        :param list(str) required_output_tokens:
            A list of tokens that should be generated by the end of the run
        :param list(str) xml_paths:
            An optional list of paths to XML files containing algorithm
            descriptions; if not specified, only detected algorithms will be
            used (or else those found in packages)
        :param list(module) packages:
            An optional list of packages to scan for decorated algorithms; if
            not specified, only detected algorithms will be used (or else
            those specified in packages
        :param bool do_timings:
            True if timing information should be captured for each algorithm,
            False otherwise
        :param bool print_timings:
            True if timing information should be printed after each algorithm,
            False otherwise
        :param bool do_direct_injection:
            True if direct injection into methods should be supported.  This
            will allow any of the inputs or generated outputs to be injected
            into a method
        :param bool use_unscanned_annotated_algorithms:
            True if algorithms that have been detected outside of the packages
            argument specified above should be used
        :param str provenance_path:
            Path to file to append full provenance data to
            If None no provenance is written
        :raises PacmanConfigurationException:
            if the configuration cannot be compiled into an execution plan
        """

        # algorithm timing information
        self._algorithm_timings = list()

        # Store the completed tokens, initially empty
        self._completed_tokens = None

        # pacman mapping objects
        self._algorithms = list()
        self._inputs = inputs

        # define mapping between types and internal values
        self._internal_type_mapping = dict()

        # store timing request
        self._do_timing = do_timings

        # print timings as you go
        self._print_timings = print_timings

        self._do_direct_injection = do_direct_injection

        if provenance_name is None:
            self._provenance_name = "mapping"
        else:
            self._provenance_name = provenance_name

        copy_of_xml_paths = []
        if xml_paths is not None:
            copy_of_xml_paths.extend(xml_paths)
        copy_of_packages = []
        if packages is not None:
            copy_of_packages.extend(packages)
        opt_algorithm_names = []
        if optional_algorithms is not None:
            opt_algorithm_names.extend(optional_algorithms)
        self.__load_algorithm_definitions(
            algorithms, opt_algorithm_names, copy_of_xml_paths,
            copy_of_packages, use_unscanned_annotated_algorithms)

        # sort_out_order_of_algorithms for execution
        self._determine_algorithm_order(
            required_outputs, tokens, required_output_tokens)

        self._provenance_path = provenance_path

    def __load_algorithm_definitions(
            self, algorithms, optional_algorithms, xml_paths, packages,
            use_unscanned_algorithms):
        """ Translates the algorithm string and uses the config XML to create
            algorithm objects

        :param list(str) algorithms:
            the algorithms that must be run by the logic flow
        :param list(str) optional_algorithms:
            algorithms which are optional and don't necessarily need to be ran
            to complete the logic flow
        :param list(str) xml_paths:
            the list of paths for XML configuration data
        :param list(module) packages:
        :param bool use_unscanned_algorithms:
        :raises PacmanConfigurationException:
        """
        # protect the variable from reference movement during usage
        xml_paths = list(xml_paths)
        packages = list(packages)

        # set up XML reader for standard PACMAN algorithms XML file reader
        # (used in decode_algorithm_data_objects function)
        xml_paths.append(operations.algorithms_metdata_file)

        # decode the algorithms specs
        xml_decoder = AlgorithmMetadataXmlReader(xml_paths)
        algorithm_data_objects = xml_decoder.decode_algorithm_data_objects()

        # Scan for annotated algorithms
        packages.append(operations)
        algorithm_data_objects.update(scan_packages(packages))
        if use_unscanned_algorithms:
            algorithm_data_objects.update(get_algorithms())

        # filter for just algorithms we want to use
        self.__algorithm_data = self._get_algorithm_data(
            algorithms, algorithm_data_objects)
        self.__optional_algorithm_data = self._get_algorithm_data(
            optional_algorithms, algorithm_data_objects)

    @staticmethod
    def _get_algorithm_data(algorithm_names, algorithm_data_objects):
        """
        :param iterable(str) algorithm_names:
        :param dict(str, AbstractAlgorithm) algorithm_data_objects:
        :rtype: list(AbstractAlgorithm)
        :raises PacmanConfigurationException:
        """
        algorithms = list()
        for algorithm_name in algorithm_names:
            if algorithm_name not in algorithm_data_objects:
                raise PacmanConfigurationException(
                    "Cannot find algorithm {}".format(algorithm_name))
            algorithms.append(algorithm_data_objects[algorithm_name])
        return algorithms

    def _determine_algorithm_order(
            self, required_outputs, tokens, required_output_tokens):
        """ Takes the algorithms and determines which order they need to be
            executed to generate the correct data objects

        :param iterable(str) required_outputs:
            the set of outputs that this workflow is meant to generate
        :param iterable(str) tokens:
        :param iterable(str) required_output_tokens:
        :rtype: None
        :raises PacmanConfigurationException:
        """

        # Go through the algorithms and get all possible outputs
        all_outputs = set(self._inputs)
        for algorithm in chain(
                self.__algorithm_data, self.__optional_algorithm_data):
            # Get the algorithm output types
            alg_outputs = {
                output.output_type for output in algorithm.outputs}

            # Remove from the outputs any optional input that is also an
            # output
            for alg_input in algorithm.optional_inputs:
                for matching in alg_input.get_matching_inputs(alg_outputs):
                    alg_outputs.discard(matching)
            all_outputs.update(alg_outputs)

        # Set up the token tracking and make all specified tokens complete
        token_states = TokenStates()
        for token in tokens:
            token = Token(token.name, token.part)
            token_states.track_token(token)
            token_states.process_output_token(token)

        # Go through the algorithms and add in the tokens that can be completed
        # by any of the algorithms
        for algorithm in chain(
                self.__algorithm_data, self.__optional_algorithm_data):
            for token in algorithm.generated_output_tokens:
                if (not token_states.is_token_complete(token) or
                        not token_states.is_tracking_token_part(token)):
                    token_states.track_token(token)

        # Go through the algorithms and add a fake token for any algorithm that
        # requires an optional token that can't be provided and a fake input
        # for any algorithm that requires an optional input that can't be
        # provided.  This allows us to require the other optional inputs and
        # tokens so that algorithms that provide those items are run before
        # those that can make use of them.
        fake_inputs = set()
        fake_tokens = TokenStates()
        for algorithm in chain(
                self.__algorithm_data, self.__optional_algorithm_data):
            for input_parameter in algorithm.optional_inputs:
                if not input_parameter.input_matches(all_outputs):
                    fake_inputs.update(
                        input_parameter.get_fake_inputs(all_outputs))
            for token in algorithm.optional_input_tokens:
                if (not token_states.is_tracking_token(token) and
                        not fake_tokens.is_token_complete(token)):
                    fake_tokens.track_token(token)
                    fake_tokens.process_output_token(token)

        input_types = set(self._inputs)

        generated_outputs = set()
        generated_outputs.union(input_types)
        algorithms_to_find = list(self.__algorithm_data)
        optionals_to_use = list(self.__optional_algorithm_data)
        outputs_to_find = self._remove_outputs_which_are_inputs(
            required_outputs)
        tokens_to_find = self._remove_complete_tokens(
            token_states, required_output_tokens)

        while algorithms_to_find or outputs_to_find or tokens_to_find:
            algorithm, algorithm_list = self.__find_suitable_algorithm(
                algorithms_to_find, optionals_to_use, input_types,
                outputs_to_find, tokens_to_find, generated_outputs,
                token_states, fake_inputs, fake_tokens)

            # Remove the value
            self._remove_algorithm_and_update_outputs(
                algorithm_list, algorithm, input_types,
                generated_outputs, outputs_to_find)

            # add the suitable algorithms to the list and take the outputs
            # as new inputs
            self._algorithms.append(algorithm)

            # Mark any tokens generated as complete
            for output_token in algorithm.generated_output_tokens:
                token_states.process_output_token(output_token)
                if token_states.is_token_complete(Token(output_token.name)):
                    tokens_to_find.discard(output_token.name)

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

        self._completed_tokens = token_states.get_completed_tokens()

    def __find_suitable_algorithm(
            self, algorithms_to_find, optionals_to_use, input_types,
            outputs_to_find, tokens_to_find, generated_outputs,
            token_states, fake_inputs, fake_tokens):
        """
        :param list(AbstractAlgorithm) algorithms_to_find:
        :param list(AbstractAlgorithm) optionals_to_use:
        :param set(str) input_types: the inputs available *currently*
        :param set(str) outputs_to_find:
        :param set(str) tokens_to_find:
        :param set(str) generated_outputs:
        :param TokenStates token_states:
        :param set(str) fake_inputs:
        :param TokenStates fake_tokens:
        :raises PacmanConfigurationException:
        """
        # Order of searching - each combination will be attempted in order;
        # the first matching algorithm will be used (and search will stop)
        # Elements are:
        #  1. Algorithm list to search,
        #  2. check generated outputs,
        #  3. require optional inputs)
        order = [
            # Check required algorithms forcing optional inputs
            (algorithms_to_find, False, True),

            # Check optional algorithms forcing optional inputs
            (optionals_to_use, True, True),

            # Check required algorithms without optional inputs
            # - shouldn't need to do this, but might if an optional input
            # is also a generated output of the same algorithm
            (algorithms_to_find, False, False),

            # Check optional algorithms without optional inputs
            # - as above, it shouldn't be necessary but might be if an
            # optional input is also an output of the same algorithm
            (optionals_to_use, True, False)
        ]

        for (algorithms, check_outputs, force_required) in order:
            suitable_algorithm = self.__find_algorithm_in_list(
                algorithms, input_types, generated_outputs,
                token_states, fake_inputs, fake_tokens,
                check_outputs, force_required)
            if suitable_algorithm:
                return suitable_algorithm, algorithms

        for (algorithms, check_outputs, force_required) in order:
            suitable_algorithm = self.__find_algorithm_in_list(
                algorithms, input_types, generated_outputs,
                token_states, fake_inputs, fake_tokens,
                check_outputs, force_required)

        # Failed to find an algorithm to run!
        algorithms_to_find_names = [
            alg.algorithm_id for alg in algorithms_to_find]
        optional_algorithms_names = [
            alg.algorithm_id for alg in self.__optional_algorithm_data]
        algorithms_used = [
            alg.algorithm_id for alg in self._algorithms]
        algorithm_input_requirement_breakdown = ""
        for algorithm in chain(algorithms_to_find, optionals_to_use):
            algorithm_input_requirement_breakdown += \
                self.__deduce_inputs_required_to_run(
                    algorithm, input_types, token_states, fake_inputs,
                    fake_tokens)
        algorithms_by_output = defaultdict(list)
        algorithms_by_token = defaultdict(list)
        for algorithm in chain(
                self.__algorithm_data, self.__optional_algorithm_data):
            for output in algorithm.outputs:
                algorithms_by_output[output.output_type].append(
                    algorithm.algorithm_id)
            for token in algorithm.generated_output_tokens:
                algorithms_by_token[token.name].append("{}: part={}".format(
                    algorithm.algorithm_id, token.part))

        # create complete token string
        completed_tokens_string = ""
        for token in token_states.get_completed_tokens():
            completed_tokens_string += "{}:{}, ".format(token.name, token.part)

        # create fake token string
        fake_token_string = ""
        for token in fake_tokens.get_completed_tokens():
            fake_token_string += (
                "{}:{}, ".format(token.name, token.part))

        # tokens to find string
        token_to_find_string = ""
        for token_name in tokens_to_find:
            token = token_states.get_token(token_name)
            for incomplete_part in token.incomplete_parts:
                token_to_find_string += (
                    "{}:{}, ".format(token_name, incomplete_part))

        raise PacmanConfigurationException(
            "Unable to deduce a future algorithm to use.\n"
            "    Inputs: {}\n"
            "    Fake Inputs: {}\n"
            "    Outputs to find: {}\n"
            "    Tokens complete: {}\n"
            "    Fake tokens complete: {}\n"
            "    Tokens to find: {}\n"
            "    Required algorithms remaining to be used: {}\n"
            "    Optional Algorithms unused: {}\n"
            "    Functions used: {}\n"
            "    Algorithm by outputs: {}\n"
            "    Algorithm by tokens: {}\n"
            "    Inputs required per function: \n{}\n".format(
                sorted(self._inputs),
                sorted(fake_inputs),
                outputs_to_find,
                completed_tokens_string,
                fake_token_string,
                token_to_find_string,
                algorithms_to_find_names,
                optional_algorithms_names,
                algorithms_used,
                algorithms_by_output,
                algorithms_by_token,
                algorithm_input_requirement_breakdown))

    def _remove_outputs_which_are_inputs(self, required_outputs):
        """ Generates the output list which has pruned outputs which are\
            already in the input list

        :param required_outputs: the original output listings
        :return: new list of outputs
        :rtype: iterable(str)
        """
        copy_required_outputs = set(required_outputs)
        for input_type in self._inputs:
            if input_type in copy_required_outputs:
                copy_required_outputs.remove(input_type)
        return copy_required_outputs

    @staticmethod
    def _remove_complete_tokens(tokens, output_tokens):
        """
        :param TokenStates tokens:
        :param output_tokens:
        :rtype: set
        """
        return {
            token for token in output_tokens
            if not tokens.is_token_complete(Token(token))
        }

    @staticmethod
    def __deduce_inputs_required_to_run(
            algorithm, inputs, tokens, fake_inputs, fake_tokens):
        """
        :param AbstractAlgorithm algorithm:
        :param inputs: the inputs available *currently*
        :param tokens: the tokens available *currently*
        :param fake_inputs:
        :param fake_tokens:
        :rtype: str
        """
        left_over_inputs = "            {}: [".format(algorithm.algorithm_id)
        separator = ""
        all_inputs = inputs | fake_inputs
        all_tokens = tokens | fake_tokens
        for algorithm_inputs, extra, the_inputs, the_tokens in (
                (algorithm.required_inputs, "", inputs, tokens),
                (algorithm.optional_inputs, " (optional)", all_inputs,
                 all_tokens)):
            for an_input in algorithm_inputs:
                unfound_types = [
                    param_type for param_type in an_input.param_types
                    if param_type not in the_inputs]
                found_types = [
                    param_type for param_type in an_input.param_types
                    if param_type in the_inputs]
                if unfound_types:
                    left_over_inputs += "{}'{}'{}".format(
                        separator, unfound_types, extra)
                    if found_types:
                        left_over_inputs += " (but found '{}')".format(
                            found_types)
                    separator = ", "
            for a_token in algorithm.required_input_tokens:
                if (not the_tokens.is_token_complete(a_token)):
                    left_over_inputs += "{}'{}'".format(
                        separator, a_token)
                    separator = ", "
        left_over_inputs += "]\n"
        return left_over_inputs

    @staticmethod
    def _remove_algorithm_and_update_outputs(
            algorithm_list, algorithm, input_types, generated_outputs,
            outputs_to_find):
        """ Update data structures

        :param list(AbstractAlgorithm) algorithm_list:
            the list of algorithms to remove algorithm from
        :param AbstractAlgorithm algorithm: the algorithm to remove
        :param set(str) input_types:
            the inputs list to update output from algorithm
        :param set(str) generated_outputs:
            the outputs list to update output from algorithm
        :param set(str) outputs_to_find:
        :rtype: None
        """
        algorithm_list.remove(algorithm)
        for output in algorithm.outputs:
            input_types.add(output.output_type)
            generated_outputs.add(output.output_type)
            if output.output_type in outputs_to_find:
                outputs_to_find.remove(output.output_type)

    @staticmethod
    def __find_algorithm_in_list(
            algorithm_list, inputs, generated_outputs, tokens,
            fake_inputs, fake_tokens, check_generated_outputs,
            force_optionals):
        """ Locates a suitable algorithm

        :param list(AbstractAlgorithm) algorithm_list:
            the list of algorithms to choose from
        :param iterable(str) inputs: the inputs available *currently*
        :param set(str) generated_outputs:
            the current outputs expected to be generated
        :param TokenStates tokens: the current token tracker
        :param iterable(str) fake_inputs:
            the optional inputs that will never be available
        :param TokenStates fake_tokens:
            the optional tokens that will never be available
        :param bool check_generated_outputs:
            True if an algorithm should only be selected if it generates\
            an output not in the list of generated outputs
        :param bool force_optionals:
            True if optional inputs/tokens should be considered required
        :return: a suitable algorithm which uses the inputs
        :rtype: AbstractAlgorithm or None
        """
        # TODO: This can be made "cleverer" by looking at which algorithms have
        # unsatisfied optional inputs.  The next algorithm to run can then
        # be the next that outputs the most unsatisfied optional inputs for
        # other algorithms from those with the least unsatisfied optional
        # inputs

        # Find the next algorithm which can run now
        for algorithm in algorithm_list:
            # check all inputs
            all_inputs_match = all(
                input_parameter.input_matches(inputs)
                for input_parameter in algorithm.required_inputs)

            # check all required tokens
            if all_inputs_match:
                all_inputs_match = all(
                    tokens.is_token_complete(token)
                    for token in algorithm.required_input_tokens)

            # check all optional inputs
            if all_inputs_match and force_optionals:
                all_inputs_match = all(
                    input_parameter.input_matches(inputs)
                    or input_parameter.input_matches(fake_inputs)
                    for input_parameter in algorithm.optional_inputs)

            # check all optional tokens
            if all_inputs_match and force_optionals:
                all_inputs_match = all(
                    tokens.is_token_complete(token)
                    or fake_tokens.is_token_complete(token)
                    for token in algorithm.optional_input_tokens)

            if all_inputs_match:
                # If the list of generated outputs is not given, we're done now
                if not check_generated_outputs:
                    return algorithm

                # The list of generated outputs is given, so only use the
                # algorithm if it generates something new, assuming the
                # algorithm generates any outputs at all
                if algorithm.outputs:
                    for output in algorithm.outputs:
                        if (output.output_type not in generated_outputs
                                and output.output_type not in inputs):
                            return algorithm

                # If the algorithm doesn't generate a unique output,
                # check if it generates a unique token
                if algorithm.generated_output_tokens:
                    for token in algorithm.generated_output_tokens:
                        if not tokens.is_token_complete(token):
                            return algorithm

        # If no algorithms are available, return None
        return None

    def execute_mapping(self):
        """ Executes the algorithms

        :rtype: None
        """
        self._internal_type_mapping.update(self._inputs)
        if self._do_direct_injection:
            with injection_context(self._internal_type_mapping):
                self.__execute_mapping()
        else:
            self.__execute_mapping()

    def __execute_mapping(self):
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

    def get_item(self, item_type):
        """ Get an item from the outputs of the execution

        :param str item_type:
            the item from the internal type mapping to be returned
        :return: the returned item
        """
        if item_type not in self._internal_type_mapping:
            return None
        return self._internal_type_mapping[item_type]

    def get_items(self):
        """ Get all the outputs from a execution

        :return: dictionary of types as keys and values.
        :rtype: dict(str, ...)
        """
        return self._internal_type_mapping

    def get_completed_tokens(self):
        """ Get all of the tokens that have completed as part of this execution

        :return: A list of tokens
        :rtype: list(str)
        """
        return self._completed_tokens

    @property
    def algorithm_timings(self):
        return self._algorithm_timings

    def _update_timings(self, timer, algorithm):
        """
        :param ~spinn_utilities.timer.Timer timer:
        :param AbstractAlgorithm algorithm:
        """
        time_taken = timer.take_sample()
        if self._print_timings:
            logger.info("Time {} taken by {}",
                        time_taken, algorithm.algorithm_id)
        self._algorithm_timings.append(
            (algorithm.algorithm_id, time_taken, self._provenance_name))

    def _report_full_provenance(self, algorithm, results):
        """
        :param AbstractAlgorithm algorithm:
        :param dict(str,...) results:
        """
        try:
            with open(self._provenance_path, "a") as provenance_file:
                algorithm.write_provenance_header(provenance_file)
                if algorithm.required_inputs:
                    provenance_file.write("\trequired_inputs:\n")
                    self._report_inputs(provenance_file,
                                        algorithm.required_inputs)
                if algorithm.optional_inputs:
                    provenance_file.write("\toptional_inputs:\n")
                    self._report_inputs(provenance_file,
                                        algorithm.optional_inputs)
                if algorithm.required_input_tokens:
                    provenance_file.write("\trequired_tokens:\n")
                    self._report_tokens(
                        provenance_file, algorithm.required_input_tokens)
                if algorithm.optional_input_tokens:
                    provenance_file.write("\toptional_tokens:\n")
                    self._report_tokens(
                        provenance_file, algorithm.optional_input_tokens)
                if algorithm.outputs:
                    provenance_file.write("\toutputs:\n")
                    for output in algorithm.outputs:
                        variable = results[output.output_type]
                        the_type = self._get_type(variable)
                        provenance_file.write(
                            "\t\t{}:{}\n".format(output.output_type, the_type))
                if algorithm.generated_output_tokens:
                    provenance_file.write("\tgenerated_tokens:\n")
                    self._report_tokens(
                        provenance_file, algorithm.generated_output_tokens)

                provenance_file.write("\n")
        except Exception:  # pylint: disable=broad-except
            logger.exception("Exception when attempting to write provenance")

    def _report_inputs(self, provenance_file, inputs):
        """
        :param ~io.FileIO provenance_file:
        :param iterable(AbstractInput) inputs:
        """
        for input_parameter in inputs:
            name = input_parameter.name
            for param_type in input_parameter.param_types:
                if param_type in self._internal_type_mapping:
                    variable = self._internal_type_mapping[param_type]
                    the_type = self._get_type(variable)
                    provenance_file.write(
                        "\t\t{}   {}:{}\n".format(name, param_type, the_type))
                    break
            else:
                if len(input_parameter.param_types) == 1:
                    provenance_file.write(
                        "\t\t{}   None of {} provided\n"
                        "".format(name, input_parameter.param_types))
                else:
                    provenance_file.write(
                        "\t\t{}   {} not provided\n"
                        "".format(name, input_parameter.param_types[0]))

    def _report_tokens(self, provenance_file, tokens):
        """
        :param ~io.FileIO provenance_file:
        :param list(Token) tokens:
        """
        for token in tokens:
            part = token.part if token.part is not None else ""
            if part == "":
                part = " ({})".format(part)
            provenance_file.write("\t\t{}{}".format(token.name, part))

    def _get_type(self, variable):
        if variable is None:
            return "None"
        the_type = type(variable)
        if the_type in [bool, float, int, str]:
            return variable
        if the_type == set:
            if not variable:
                return "Empty set"
            the_type = "set("
            for item in variable:
                the_type += "{},".format(self._get_type(item))
            the_type += ")"
            return the_type
        elif the_type == list:
            if not variable:
                return "Empty list"
            first_type = type(variable[0])
            if all(isinstance(n, first_type) for n in variable):
                return "list({}) :len{}".format(first_type, len(variable))
        return the_type
