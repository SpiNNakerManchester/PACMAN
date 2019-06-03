class MinimisationFailedError(Exception):
    """Raised when a routing table could not be minimised to reach a specified
    target.

    Attributes
    ----------
    target_length : int
        The target number of routing entries.
    final_length : int
        The number of routing entries reached when the algorithm completed.
        (final_length > target_length)
    chip : (x, y) or None
        The coordinates of the chip on which routing table minimisation first
        failed. Only set when minimisation is performed across many chips
        simultaneously.
    """

    def __init__(self, target_length, final_length=None, chip=None):
        self.chip = chip
        self.target_length = target_length
        self.final_length = final_length

    def __str__(self):
        if self.chip is not None:
            x, y = self.chip
            text = ("Could not minimise routing table for "
                    "({}, {}) ".format(x, y))
        else:
            text = "Could not minimise routing table "

        text += "to fit in {} entries.".format(self.target_length)

        if self.final_length is not None:
            text += " Best managed was {} entries.".format(self.final_length)

        return text
