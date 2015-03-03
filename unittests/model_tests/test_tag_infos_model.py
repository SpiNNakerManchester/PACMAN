import unittest
from pacman.model.tags.tags import Tags


class TestSubgraphModel(unittest.TestCase):

    def test_new_tag_info(self):
        tag_info = Tags()

    def test_adding_a_iptag_to_tag_info(self):
        tag_info = Tags()
        tag_info.add_iptag(1, "122.2.2.2", "11.22.34.5", 1, False,
                           "Test subvert")

    def test_adding_a_reverse_iptag(self):
        tag_info = Tags()
        tag_info.add_reverse_ip_tag(1, "122.2.2.2", 23, 0, 0, 1, 1)

    def test_add_iptag_then_locate_tag(self):
        tag_info = Tags()
        tag_info.add_iptag(1, "122.2.2.2", "11.22.34.5", 1, False,
                           "Test subvert")
        if tag_info.contains_iptag_for(1, "11.22.34.5"):
            pass
        else:
            raise AssertionError("should contain a iptag of this port "
                                 "and ipaddress")

    def test_add_iptag_then_fail_to_locate(self):
        tag_info = Tags()
        tag_info.add_iptag(1, "122.2.2.2", "11.22.34.5", 1, False,
                           "Test subvert")
        if tag_info.contains_iptag_for(1, "11.22.34.4"):
            raise AssertionError("should not contain a iptag of this port "
                                 "and ipaddress")
        else:
            pass

    def test_add_reverse_iptag_then_locate_tag(self):
        tag_info = Tags()
        tag_info.add_reverse_ip_tag(1, "122.2.2.2", 23, 0, 0, 1, 1)
        if tag_info.contains_reverse_iptag_for(0, 0, 1, 23):
            pass
        else:
            raise AssertionError("should contain a iptag of this port "
                                 "and ipaddress")

    def test_add_reverse_iptag_then_not_locate_tag(self):
        tag_info = Tags()
        tag_info.add_reverse_ip_tag(1, "122.2.2.2", 23, 0, 0, 1, 1)
        if tag_info.contains_reverse_iptag_for(0, 0, 2, 23):
            raise AssertionError("should not contain a iptag of this port "
                                 "and ipaddress")

        else:
            pass

if __name__ == '__main__':
    unittest.main()
