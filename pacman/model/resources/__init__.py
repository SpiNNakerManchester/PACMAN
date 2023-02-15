# Copyright (c) 2014 The University of Manchester
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

from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .element_free_space import ElementFreeSpace
from .iptag_resource import IPtagResource
from .multi_region_sdram import MultiRegionSDRAM
from .reverse_iptag_resource import ReverseIPtagResource
from .variable_sdram import VariableSDRAM

__all__ = ["AbstractSDRAM", "ConstantSDRAM",
           "ElementFreeSpace", "IPtagResource", "MultiRegionSDRAM",
           "ReverseIPtagResource", "VariableSDRAM"]
