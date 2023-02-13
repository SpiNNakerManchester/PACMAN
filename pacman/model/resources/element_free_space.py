# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class ElementFreeSpace(object):
    __slots__ = ["_size", "_start_address"]

    def __init__(self, start_address, size):
        """
        :param int start_address:
        :param int size:
        """
        self._start_address = start_address
        self._size = size

    @property
    def start_address(self):
        """
        :rtype: int
        """
        return self._start_address

    @property
    def size(self):
        """
        :rtype: int
        """
        return self._size

    def __repr__(self):
        return "ElementFreeSpace:start={}:size={}".format(
            hex(self._start_address), self._size)

    def __str__(self):
        return self.__repr__()
