"""
test for routing infos
"""
# pacman imports
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman.model.routing_info.key_and_mask import KeyAndMask
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# general imports
import unittest


class TestRoutingInfos(unittest.TestCase):

    def test_create_new_routing_info_with_duplicate_key_mask_different_vertices(
            self):
        """
        checks that adding routing infos with same key and masks fail.
        This is only valid when the edgfes share a same key constraint
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube1 = MultiCastPartitionedEdge(subv1, subv2)
        sube2 = MultiCastPartitionedEdge(subv2, subv1)
        keys_and_masks1 = list()
        keys_and_masks2 = list()
        keys_and_masks1.append(KeyAndMask(0x0012, 0x00ff))
        keys_and_masks2.append(KeyAndMask(0x0012, 0x00ff))
        sri1 = SubedgeRoutingInfo(keys_and_masks1, sube1)
        sri2 = SubedgeRoutingInfo(keys_and_masks2, sube2)
        self.assertRaises(PacmanAlreadyExistsException, RoutingInfo,
                          [sri1, sri2])

    def test_create_new_routing_info_with_duplicate_key_mask_the_same_vertex(
            self):
        """
        test that edges coming from the same vertex with same keys work
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube1 = MultiCastPartitionedEdge(subv1, subv2)
        sube2 = MultiCastPartitionedEdge(subv1, subv1)
        keys_and_masks1 = list()
        keys_and_masks2 = list()
        keys_and_masks1.append(KeyAndMask(0x0012, 0x00ff))
        keys_and_masks2.append(KeyAndMask(0x0012, 0x00ff))
        sri1 = SubedgeRoutingInfo(keys_and_masks1, sube1)
        sri2 = SubedgeRoutingInfo(keys_and_masks2, sube2)
        RoutingInfo([sri1, sri2])

    def test_all_subedge_info(self):
        """
        test that creating a routing info causes edge infos to be stored in the
        routing info
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks1 = list()
        keys_and_masks1.append(KeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks1, sube)
        ri = RoutingInfo([sri])
        for info in ri.all_subedge_info:
            self.assertEqual(info, sri)

    def test_all_subedge_info_multiple_entries(self):
        """
        test that the multiple entries appear inside a routing info
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        subedges = list()
        subedges.append(MultiCastPartitionedEdge(subv1, subv2))
        subedges.append(MultiCastPartitionedEdge(subv1, subv1))
        subedges.append(MultiCastPartitionedEdge(subv2, subv2))
        subedges.append(MultiCastPartitionedEdge(subv2, subv1))
        sri = list()
        for i in range(4):
            keys_and_masks = list()
            keys_and_masks.append(KeyAndMask(0x0012 + i, 0x00ff))
            sri.append(SubedgeRoutingInfo(keys_and_masks, subedges[i]))
        ri = RoutingInfo(sri)
        i = 0
        for info in ri.all_subedge_info:
            self.assertIn(info, sri)
            i += 1

    def test_get_subedge_info_by_key_matching(self):
        """
        check that you can get a subedge routing info from a routing info
        based off key
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks = list()
        keys_and_masks.append(KeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks, sube)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_infos_by_key(0xff12, 0x00ff), sri)

    def test_get_subedge_info_by_key_not_matching(self):
        """
        check that trying to locate a subedge info with an invalid key and mask
        results in no subedge info being returned
        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks = list()
        keys_and_masks.append(KeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks, sube)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_infos_by_key(0xff12, 0x000f), None)

    def test_get_key_from_subedge_info(self):
        """

        :return:
        """
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        keys_and_masks = list()
        keys_and_masks.append(KeyAndMask(0x0012, 0x00ff))
        sri = SubedgeRoutingInfo(keys_and_masks, sube)
        ri = RoutingInfo([sri])
        ri_keys_and_masks = ri.get_keys_and_masks_from_subedge(sri.subedge)
        for key_and_mask in ri_keys_and_masks:
            self.assertEqual(key_and_mask.key, 0x0012)

    def test_get_key_from_subedge_info_not_matching(self):
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_key_from_subedge(MultiCastPartitionedEdge(subv1, subv1)), None)

    def test_get_subedge_information_from_subedge(self):
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_information_from_subedge(sri.subedge),
                         sri)

    def test_get_subedge_information_from_subedge_not_matching(self):
        subv1 = PartitionedVertex(None, "")
        subv2 = PartitionedVertex(None, "")
        sube = MultiCastPartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(
            ri.get_subedge_information_from_subedge(MultiCastPartitionedEdge(subv1, subv1)),
            None)


if __name__ == '__main__':
    unittest.main()