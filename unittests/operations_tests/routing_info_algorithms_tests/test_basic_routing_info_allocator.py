import unittest
# from pacman.operations.routing_info_allocator_algorithms\
#     .basic_routing_info_allocator import BasicRoutingInfoAllocator


class MyTestCase(unittest.TestCase):

    @unittest.skip("testing skipping")
    def test_something(self):
        self.assertEquals(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()
