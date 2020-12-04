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

from pacman.executor.algorithm_decorators import Token


class _TokenState(object):
    """ Determines whether a token has been fulfilled or not
    """

    __slots__ = [

        # The parts of the token that have not yet completed
        "_incomplete_parts",

        # The parts of the token that have completed
        "_complete_parts"
    ]

    def __init__(self):
        self._incomplete_parts = set()
        self._complete_parts = set()

    def is_tracking_token_part(self, part):
        """ Determine if the given part is being tracked

        :param part:
        :type part: str or None
        """
        return part in self._incomplete_parts or part in self._complete_parts

    def track_token_part(self, part):
        """ Indicates that this state should start tracking the completion\
            of a part of a token.  Part can be None to indicate the tracking\
            of a whole token.

        :param part:
        :type part: str or None
        """
        self._incomplete_parts.add(part)

    def complete_token_part(self, part):
        """ Indicates that a part of this token has completed.  If part is\
            None, indicates that the whole token has completed.

        :param part:
        :type part: str or None
        """
        if part is None:
            self._complete_parts.update(self._incomplete_parts)
            self._incomplete_parts = set()
        self._complete_parts.add(part)
        self._incomplete_parts.discard(part)

    def is_complete(self, part=None):
        """ If part is None, true if all parts have completed, otherwise\
            checks for completion of a specific part of the token

        :param part:
        :type part: str or None
        :rtype: bool
        """
        if part is None:
            return not self._incomplete_parts
        return part in self._complete_parts

    @property
    def complete_parts(self):
        """ returns the complete parts

        :return: the complete parts of this token
        """
        return self._complete_parts

    @property
    def incomplete_parts(self):
        return self._incomplete_parts

    def __or__(self, other):
        """
        Create a new object which is an or merge of the two

        If a part is completed in either it will be completed
        If a part is incomplete in either and not completed in the second is
        will be incomplete

        :param _Token_state other:
        :rtype:  _TokenState
        """
        result = _TokenState()
        result._complete_parts = self._complete_parts | other._complete_parts
        result._incomplete_parts = \
            (self._incomplete_parts | other._incomplete_parts)
        result._incomplete_parts.difference_update(result._complete_parts)
        return result


class TokenStates(object):
    """ Keeps track of multiple token state objects to determine if they\
        are complete
    """

    __slots__ = [

        # The tokens being tracked
        "_tokens"
    ]

    def __init__(self):
        self._tokens = dict()

    def is_tracking_token(self, token):
        """ Determine if the token is being tracked
        """
        if token.name not in self._tokens:
            return False
        if token.part is None:
            return True
        return self._tokens[token.name].is_tracking_token_part(token.part)

    def track_token(self, token):
        """ Start tracking a token
        """
        if token.name not in self._tokens:
            self._tokens[token.name] = _TokenState()
        self._tokens[token.name].track_token_part(token.part)

    def process_output_token(self, output_token):
        """ Process an output token marking a process or part as complete
        """
        if output_token.name in self._tokens:
            self._tokens[output_token.name].complete_token_part(
                output_token.part)

    def is_token_complete(self, token):
        """ True if the given token has completed
        """
        # If the token is not tracked, is assumed to be complete
        if token.name not in self._tokens:
            return False

        # The token is complete if the token part is complete or the token
        # as a whole is complete
        token_state = self._tokens[token.name]
        return token_state.is_complete(token.part) or token_state.is_complete()

    def get_completed_tokens(self):
        """ Get a list of tokens that have been completed
        """
        tokens_to_return = list()
        for token_name in self._tokens:
            for completed_part in self._tokens[token_name].complete_parts:
                tokens_to_return.append(
                    Token(name=token_name, part=completed_part))
        return tokens_to_return

    def get_token(self, name):
        return self._tokens[name]

    def is_tracking_token_part(self, token):
        """ checks if a token part is actually being tracked

        :param token: the token whom's part is to be checked.
        :return: bool
        """
        if token.name not in self._tokens:
            return False

        return self._tokens[token.name].is_tracking_token_part(token.part)

    def __or__(self, other):
        """
        Create a new object which is an or merge of the two

        If a token or part is completed in either it will be completed
        If a part is incomplete in either and not completed in the second is
        will be incomplete

        :param other:
        :return:
        """
        result = TokenStates()
        # Copy in all the tokens
        for name in self._tokens:
            if name in other._tokens:
                # Both so union
                result._tokens[name] = (
                        self._tokens[name] | other._tokens[name])
            else:
                # only self
                result._tokens[name] = self._tokens[name]
        for name in other._tokens:
            # Add the ones not already unioned from other
            if name not in self._tokens:
                result._tokens[name] = other._tokens[name]
        return result
