"""Exceptions which placers can throw to indicate standard types of problem.
"""


class InsufficientResourceError(Exception):
    """Indication that a process failed because adequate resources were not
    available in the machine.
    """
    pass


class InvalidConstraintError(Exception):
    """Indication that a process failed because an impossible constraint was
    given.
    """
    pass


class MachineHasDisconnectedSubregion(Exception):
    """Some part of the machine has no paths connecting it to the rest of the
    machine.
    """
    pass
