from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.abstract_classes.abstract_has_constraints\
    import AbstractHasConstraints
from pacman.model.decorators.overrides import overrides
from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


class ConstrainedObject(AbstractHasConstraints):
    """ An implementation of an object which holds constraints
    """

    __slots__ = [

        # The constraints of the object
        "_constraints"
    ]

    def __init__(self, constraints=None):
        """

        :param constraints: Any initial constraints
        """

        # safety point for diamond inheritance
        if not hasattr(self, 'constraints'):
            self._constraints = set()

        # add new constraints to the set
        self.add_constraints(constraints)

    @overrides(AbstractHasConstraints.add_constraint)
    def add_constraint(self, constraint):
        if (constraint is None or
                not isinstance(constraint, AbstractConstraint)):
            raise PacmanInvalidParameterException(
                "constraint", constraint, "Must be a pacman.model."
                                          "constraints.abstract_constraint."
                                          "AbstractConstraint")
        self._constraints.add(constraint)

    @overrides(AbstractHasConstraints.add_constraints)
    def add_constraints(self, constraints):
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    @property
    @overrides(AbstractHasConstraints.constraints)
    def constraints(self):
        return self._constraints
