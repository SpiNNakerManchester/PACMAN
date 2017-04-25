import unittest
from pacman.operations.routing_info_allocator_algorithms\
    .malloc_based_routing_allocator.malloc_based_routing_info_allocator\
    import MallocBasedRoutingInfoAllocator
from pacman.model.routing_info import BaseKeyAndMask


class MyTestCase(unittest.TestCase):

    def test_allocate_fixed_key_and_mask(self):
        allocator = MallocBasedRoutingInfoAllocator()
        allocator._allocate_fixed_keys_and_masks(
            [BaseKeyAndMask(0x800, 0xFFFFF800)], None)
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print allocator._free_space_tracker
        self.assertEqual(len(allocator._free_space_tracker), 2, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 0,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size, 2048,
                         error)
        self.assertEqual(allocator._free_space_tracker[1].start_address,
                         0x1000, error)
        self.assertEqual(allocator._free_space_tracker[1].size, 0xFFFFF000,
                         error)

    def _print_keys_and_masks(self, keys_and_masks):
        for key_and_mask in keys_and_masks:
            print("key =", hex(key_and_mask.key),
                  "mask =", hex(key_and_mask.mask))

    def test_allocate_fixed_mask(self):
        allocator = MallocBasedRoutingInfoAllocator()
        self._print_keys_and_masks(allocator._allocate_keys_and_masks(
            0xFFFFFF00, None, 20))
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print allocator._free_space_tracker
        self.assertEqual(len(allocator._free_space_tracker), 1, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 0x100,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size, 0xFFFFFF00,
                         error)

    def test_allocate_n_keys(self):
        allocator = MallocBasedRoutingInfoAllocator()
        self._print_keys_and_masks(allocator._allocate_keys_and_masks(
            None, None, 20))
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print allocator._free_space_tracker
        self.assertEqual(len(allocator._free_space_tracker), 1, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 32,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size,
                         0x100000000 - 32, error)

    def test_allocate_mixed_keys(self):
        fixed_masks = [None, None, 0xFFFFFF00, 0xFFFFF800]
        n_keys = [200, 20, 20, 256]

        allocator = MallocBasedRoutingInfoAllocator()

        allocator._allocate_fixed_keys_and_masks(
            [BaseKeyAndMask(0x800, 0xFFFFF800)], None)

        print allocator._free_space_tracker

        for mask, keys in zip(fixed_masks, n_keys):
            self._print_keys_and_masks(
                allocator._allocate_keys_and_masks(mask, None, keys))
            print allocator._free_space_tracker

        print allocator._free_space_tracker

        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        self.assertEqual(len(allocator._free_space_tracker), 3, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address,
                         0x120, error)
        self.assertEqual(allocator._free_space_tracker[0].size,
                         224, error)
        self.assertEqual(allocator._free_space_tracker[1].start_address,
                         0x300, error)
        self.assertEqual(allocator._free_space_tracker[1].size,
                         1280, error)
        self.assertEqual(allocator._free_space_tracker[2].start_address,
                         0x1800, error)
        self.assertEqual(allocator._free_space_tracker[2].size,
                         0x100000000L - 0x1800, error)


if __name__ == '__main__':
    unittest.main()
