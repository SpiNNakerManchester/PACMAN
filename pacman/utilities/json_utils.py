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
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
import json
import gzip
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint, FixedKeyFieldConstraint,
    FixedKeyAndMaskConstraint, FixedMaskConstraint,
    FlexiKeyFieldConstraint, ShareKeyConstraint)
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)
from pacman.model.graphs.machine import SimpleMachineVertex


def json_to_object(json_object):
    if isinstance(json_object, str):
        if json_object.endswith(".gz"):
            with gzip.open(json_object) as j_file:
                return json.load(j_file)
        else:
            with open(json_object) as j_file:
                return json.load(j_file)
    return json_object


def constraint_to_json(constaint):
    json_object = OrderedDict()
    json_object["class"] = constaint.__class__.__name__
    if isinstance(constaint, BoardConstraint):
        json_object["board_address"] = constaint.board_address
    if isinstance(constaint, (
            ChipAndCoreConstraint, RadialPlacementFromChipConstraint)):
        json_object["x"] = constaint.x
        json_object["y"] = constaint.y
    if isinstance(constaint, ChipAndCoreConstraint):
        if constaint.p is not None:
            json_object["p"] = constaint.p
    if isinstance(constaint,
                  (SameChipAsConstraint, SameAtomsAsVertexConstraint)):
        json_object["vertex"] = constaint.vertex.label
    if isinstance(constaint,
                  (FixedVertexAtomsConstraint, MaxVertexAtomsConstraint)):
        json_object["size"] = constaint.size
    #if isinstance(constaint, FixedKeyAndMaskConstraint)
    if isinstance(constaint, FixedKeyFieldConstraint):
        raise NotImplementedError(
            "FixedKeyFieldConstraint not yet supported by json")
    return json_object


def contraint_from_json(json_object):
    json_object = json_to_object(json_object)
    if json_object["class"] == "BoardConstraint":
        return BoardConstraint(json_object["board_address"])
    if json_object["class"] == "ChipAndCoreConstraint":
        if "p" in json_object:
            p = json_object["p"]
        else:
            p = None
        return ChipAndCoreConstraint(json_object["x"], json_object["y"], p)
    if json_object["class"] == "ContiguousKeyRangeContraint":
        return ContiguousKeyRangeContraint()
    if json_object["class"] == "FixedVertexAtomsConstraint":
        return FixedVertexAtomsConstraint(json_object["size"])
    if json_object["class"] == "MaxVertexAtomsConstraint":
        return MaxVertexAtomsConstraint(json_object["size"])
    if json_object["class"] == "RadialPlacementFromChipConstraint":
        return RadialPlacementFromChipConstraint(
            json_object["x"], json_object["y"])
    if json_object["class"] == "SameChipAsConstraint":
        return SameChipAsConstraint(vertex_lookup(json_object["vertex"]))
    if json_object["class"] == "SameAtomsAsVertexConstraint":
        return SameAtomsAsVertexConstraint(
            vertex_lookup(json_object["vertex"]))


def vertex_to_json(vertex):
    json_object = OrderedDict()
    json_object["label"] = vertex.label
    return json_object


def vertex_lookup(label):
    return SimpleMachineVertex(None, label)