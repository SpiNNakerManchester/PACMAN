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
    ContiguousKeyRangeContraint,
    FixedKeyAndMaskConstraint, FixedMaskConstraint,
    ShareKeyConstraint)
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)
from pacman.model.routing_info import BaseKeyAndMask
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


def constraint_to_json(constraint):
    json_object = OrderedDict()
    try:
        json_object["class"] = constraint.__class__.__name__
        if isinstance(constraint, BoardConstraint):
            json_object["board_address"] = constraint.board_address
        elif isinstance(constraint, (
                ChipAndCoreConstraint, RadialPlacementFromChipConstraint)):
            json_object["x"] = constraint.x
            json_object["y"] = constraint.y
            if isinstance(constraint, ChipAndCoreConstraint):
                if constraint.p is not None:
                    json_object["p"] = constraint.p
        elif isinstance(constraint,
                        (SameChipAsConstraint, SameAtomsAsVertexConstraint)):
            json_object["vertex"] = constraint.vertex.label
        elif isinstance(constraint,
                        (FixedVertexAtomsConstraint, MaxVertexAtomsConstraint)):
            json_object["size"] = constraint.size
        elif isinstance(constraint, FixedKeyAndMaskConstraint):
            json_object["keys_and_masks"] = key_mask_collection_to_json(
                constraint.keys_and_masks)
            if constraint.key_list_function:
                json_object["key_list_function"] = str(
                    constraint.key_list_function)
        elif isinstance(constraint, FixedMaskConstraint):
            json_object["mask"] = constraint.mask
        elif isinstance(constraint, "ContiguousKeyRangeContraint"):
             # No extra parameters
            pass
        else:
            # Oops an unexpected class
            # Classes Not covered include
            # FixedKeyFieldConstraint
            # FlexiKeyFieldConstraint
            json_object["str"] = str(constraint)
            json_object["repr"] = repr(constraint)
    except Exception as ex:
        json_object["exception"] = str(ex)
    return json_object


def contraint_from_json(json_object):
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
    if json_object["class"] == "FixedKeyAndMaskConstraint":
        if "key_list_function" in json_object:
            raise NotImplementedError(
                "key_list_function {}".format(json_object["key_list_function"]))
        return FixedKeyAndMaskConstraint(
            key_mask_list_from_json(json_object["keys_and_masks"]))
    if json_object["class"] == "FixedMaskConstraint":
        return FixedMaskConstraint(json_object["mask"])
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
    raise NotImplementedError("contraint {}".format(json_object["class"]))

def key_mask_to_json(key_mask):
    try:
        json_object = OrderedDict()
        json_object["key"] = key_mask.key
        json_object["mask"] = key_mask.mask
    except Exception as ex:
        json_object["exception"] = str(ex)
    return json_object

def key_mask_from_json(json_object):
    return BaseKeyAndMask(json_object["key"], json_object["mask"])

def key_mask_collection_to_json(key_masks):
    json_object = []
    for key_mask in key_masks:
        json_object.append(key_mask_to_json(key_mask))
    return json_object

def key_mask_list_from_json(json_object):
    key_masks = []
    for sub in json_object:
        key_masks.append(key_mask_from_json(sub))
    return key_masks

def vertex_to_json(vertex):
    json_object = OrderedDict()
    try:
        json_object["label"] = vertex.label
    except Exception as ex:
        json_object["exception"] = str(ex)
    return json_object


def vertex_lookup(label):
    return SimpleMachineVertex(None, label)