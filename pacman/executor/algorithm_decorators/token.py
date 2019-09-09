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


class Token(object):
    """ A token in the algorithm flow that indicates a process or part of a\
        process.
    """

    __slots__ = [
        # The name of the token
        "_name",
        # The part of the token, or None if no part
        "_part"
    ]

    def __init__(self, name, part=None):
        self._name = name
        self._part = part

    @property
    def name(self):
        return self._name

    @property
    def part(self):
        return self._part

    def __repr__(self):
        return "Token(name={}, part={})".format(self._name, self._part)

    def __hash__(self):
        return ((self._name, self._part)).__hash__()

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self._name == other.name and self._part == other.part

    def __ne__(self, other):
        if not isinstance(other, Token):
            return True
        return not self.__eq__(other)
