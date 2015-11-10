"""
test for subedge routing infos
"""
# pacman imports
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# general imports
import unittest


class TestSubedgeRoutingInfos(unittest.TestCase):
    def test_create_new_subedge_routing_info(self):
        """
        check that creating a routing info works by putting data in the
         right places
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks = list()
        keys_and_masks.append(BaseKeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks, sube)
        self.assertEqual(sri.subedge, sube)
        key_and_mask = sri.keys_and_masks
        self.assertEqual(key_and_mask[0].key, 0x0012)
        self.assertEqual(key_and_mask[0].mask, 0x00ff)

    def test_create_new_routing_info(self):
        """
        checks that creating a routing works on its own
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks = list()
        keys_and_masks.append(BaseKeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks, sube)
        RoutingInfo([sri])

if __name__ == '__main__':
    unittest.main()
