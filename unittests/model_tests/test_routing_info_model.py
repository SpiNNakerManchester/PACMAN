import unittest
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex


class TestRoutingTables(unittest.TestCase):
    def test_create_new_subedge_routing_info(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        self.assertEqual(sri.subedge, sube)
        self.assertEqual(sri.key, 0x0012)
        self.assertEqual(sri.mask, 0x00ff)

    def test_create_new_routing_info(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        RoutingInfo([sri])

    def test_create_new_routing_info_with_duplicate_key_mask_different_vertices(
            self):
        with self.assertRaises(PacmanAlreadyExistsException):
            subv1 = PartitionedVertex(0, 1)
            subv2 = PartitionedVertex(2, 3)
            sube1 = PartitionedEdge(subv1, subv2)
            sube2 = PartitionedEdge(subv2, subv1)
            sri1 = SubedgeRoutingInfo(sube1, 0x0012, 0x00ff)
            sri2 = SubedgeRoutingInfo(sube2, 0x0012, 0x00ff)
            RoutingInfo([sri1, sri2])

    def test_create_new_routing_info_with_duplicate_key_mask_the_same_vertex(
            self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube1 = PartitionedEdge(subv1, subv2)
        sube2 = PartitionedEdge(subv1, subv1)
        sri1 = SubedgeRoutingInfo(sube1, 0x0012, 0x00ff)
        sri2 = SubedgeRoutingInfo(sube2, 0x0012, 0x00ff)
        RoutingInfo([sri1, sri2])

    def test_all_subedge_info(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        all_info = ri.all_subedge_info
        self.assertEqual(all_info[0], sri)

    def test_all_subedge_info_multiple_entries(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        subedges = list()
        subedges.append(PartitionedEdge(subv1, subv2))
        subedges.append(PartitionedEdge(subv1, subv1))
        subedges.append(PartitionedEdge(subv2, subv2))
        subedges.append(PartitionedEdge(subv2, subv1))
        sri = list()
        for i in range(4):
            sri.append(SubedgeRoutingInfo(subedges[i], 0x0012 + i, 0x00ff))
        ri = RoutingInfo(sri)
        all_info = ri.all_subedge_info
        for i in range(4):
            self.assertEqual(all_info[i], sri[i])

    def test_get_subedge_info_by_key_matching(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_info_by_key(0xff12, 0x00ff), sri)

    def test_get_subedge_info_by_key_not_matching(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_info_by_key(0xff12, 0x000f), None)

    def test_get_key_from_subedge_info(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_key_from_subedge(sri.subedge), 0x0012)

    def test_get_key_from_subedge_info_not_matching(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_key_from_subedge(PartitionedEdge(subv1, subv1)), None)

    def test_get_subedge_information_from_subedge(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(ri.get_subedge_information_from_subedge(sri.subedge),
                         sri)

    def test_get_subedge_information_from_subedge_not_matching(self):
        subv1 = PartitionedVertex(0, 1)
        subv2 = PartitionedVertex(2, 3)
        sube = PartitionedEdge(subv1, subv2)
        sri = SubedgeRoutingInfo(sube, 0x0012, 0x00ff)
        ri = RoutingInfo([sri])
        self.assertEqual(
            ri.get_subedge_information_from_subedge(PartitionedEdge(subv1, subv1)),
            None)


if __name__ == '__main__':
    unittest.main()