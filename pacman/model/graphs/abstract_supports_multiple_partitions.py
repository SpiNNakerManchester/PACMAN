# Copyright (c) 2020 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List

from spinn_utilities.abstract_base import abstractmethod, AbstractBase


class AbstractSupportsMultiplePartitions(object, metaclass=AbstractBase):
    """
    Marks a vertex that can have multiplePartitions.
    """

    __slots__ = ()

    @abstractmethod
    def partition_ids_supported(self) -> List[str]:
        """
        List of Partition ids this vertex supports
        """
        raise NotImplementedError
