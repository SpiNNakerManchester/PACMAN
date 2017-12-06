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
        """
        return part in self._incomplete_parts or part in self._complete_parts

    def track_token_part(self, part):
        """ Indicates that this state should start tracking the completion\
            of a part of a token.  Part can be None to indicate the tracking\
            of a whole token.
        """
        self._incomplete_parts.add(part)

    def complete_token_part(self, part):
        """ Indicates that a part of this token has completed.  If part is\
            None, indicates that the whole token has completed.
        """
        if part is None:
            self._complete_parts.update(self._incomplete_parts)
            self._incomplete_parts = set()
        self._complete_parts.add(part)
        self._incomplete_parts.discard(part)

    def is_complete(self, part=None):
        """ If part is None, true if all parts have completed, otherwise\
            checks for completion of a specific part of the token
        """
        if part is None:
            return len(self._incomplete_parts) == 0
        return part in self._complete_parts


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
        return [
            name for name, token in self._tokens.iteritems()
            if token.is_complete()
        ]
