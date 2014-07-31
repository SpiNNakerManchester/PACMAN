from pacman.model.constraints.abstract_constraint import AbstractConstraint


class VertexRequiresMultiCastSourceConstraint(AbstractConstraint):
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
        AbstractConstraint.__init__(
            self, "Vertex Requires Multi Cast Source Constraint with commands"
                  "{}".format(commands))
        self._commands = commands

    @property
    def commands(self):
        """ The commands to transmit

        :return: the commands
        :rtype: :py:class:`pacman.utility.multicastcommand.MultiCastCommand`
        :raise None: does not raise any known exceptions
        """
        return self._commands
