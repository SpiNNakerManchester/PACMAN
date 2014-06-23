__author__ = 'daviess'

from pacman.constraints.abstract_constraint import AbstractConstraint


class AbstractPlacerConstraint(AbstractConstraint):
    """
    Object which is inherited by every constraint class\
    related to the placer algorithm
    """
    
    def __init__(self):
        """
        
        :return: the placer constraint object just created
        :rtype: pacman.constraints.abstract_placer_constraint.AbstractPlacerConstraint
        :raise None: Raises no known exceptions
        """
        pass
