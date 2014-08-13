from pacman.model.constraints.abstract_utility_constraint import \
    AbstractUtilityConstraint


class VertexRequiresMultiCastSourceConstraint(AbstractUtilityConstraint):
    """ A constraint which indicates that a vertex has a requirement for some
    multicast packets to be trnasmitted at given times
    itself to a multicast source
    """

    def __init__(self, commands):
        """

        :param commands: The commands that the vertex expects to be trnasmitted
    :type commands: iterable of pacman.utility.multicastcommand.MultiCastCommand
        :raise None: does not raise any known exceptions
        """
        AbstractUtilityConstraint.__init__(
            self, "AbstractConstrainedVertex Requires Multi Cast Source Constraint with commands"
                  "{}".format(commands))
        self._commands = commands

    def is_utility_constraint(self):
        return True

    @property
    def commands(self):
        """ The commands to transmit

        :return: the commands
        :rtype: :py:class:`pacman.utility.multicastcommand.MultiCastCommand`
        :raise None: does not raise any known exceptions
        """
        return self._commands
