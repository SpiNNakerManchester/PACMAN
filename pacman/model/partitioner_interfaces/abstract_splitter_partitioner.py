# Copyright (c) 2020-2023 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase


class AbstractSplitterPartitioner(object, metaclass=AbstractBase):
    """ Splitter API to allow other Partitioner's to add more stuff to the\
        edge creation process.

    This makes sure that the methods the superclass expects to be there are
    not removed.
    """
