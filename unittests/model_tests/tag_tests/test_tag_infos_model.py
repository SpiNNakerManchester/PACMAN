"""
TestTagsModel
"""

# pacman imports
from pacman.model.graph.machine.simple_machine_vertex import SimpleMachineVertex
from pacman.model.tags.tags import Tags

# spinnmachine imports
from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag

# gfeneral imports
import unittest


class TestTagsModel(unittest.TestCase):
    """
    test that the tags object works as expected
    """

    def test_new_tag_info(self):
        """
        test that creating a empty tag object wroks
        :return:
        """
        tag_info = Tags()

    def test_adding_a_iptag_to_tag_info(self):
        """
        check that adding a tag after init works
        :return:
        """
        tag_info = Tags()
        iptag = IPTag("", 1, "122.2.2.2", 1, False)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, parttiioned_vertex)

    def test_adding_a_reverse_iptag(self):
        """
        check that adding a reverse iptag works correctly
        :return:
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, parttiioned_vertex)

    def test_add_iptag_then_locate_tag(self):
        """
        check that locating a iptag via get_ip_tags_for_vertex function
        :return:
        """
        tag_info = Tags()
        iptag = IPTag("", 1, "122.2.2.2", 1, False)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, parttiioned_vertex)

        gotton_tag = tag_info.get_ip_tags_for_vertex(parttiioned_vertex)
        self.assertEqual(gotton_tag[0], iptag)

    def test_add_iptag_then_fail_to_locate(self):
        """
        test that asking for a invalid iptag returns a None value
        :return:
        """
        tag_info = Tags()
        iptag = IPTag("", 1, "122.2.2.2", 1, False)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        parttiioned_vertex_2 = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, parttiioned_vertex)

        gotton_tag = tag_info.get_ip_tags_for_vertex(parttiioned_vertex_2)
        self.assertEqual(gotton_tag, None)

    def test_add_reverse_iptag_then_locate_tag(self):
        """
        check that asking for a reverse iptag for a speific machine vertex
        works
        :return:
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, parttiioned_vertex)
        gotton_tag = tag_info.get_reverse_ip_tags_for_vertex(parttiioned_vertex)
        self.assertEqual(gotton_tag[0], reverse_iptag)

    def test_add_reverse_iptag_then_not_locate_tag(self):
        """
        check that asking for a reverse iptag with a incorrect machine vertex
        will cause a none returned
        :return:
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        parttiioned_vertex = SimpleMachineVertex(None, "")
        parttiioned_vertex2 = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, parttiioned_vertex2)
        gotton_tag = tag_info.get_reverse_ip_tags_for_vertex(parttiioned_vertex)
        self.assertEqual(gotton_tag, None)

if __name__ == '__main__':
    unittest.main()
