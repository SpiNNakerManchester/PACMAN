import numpy

from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.field import Field
from pacman.exceptions import PacmanRouteInfoAllocationException


class KeyFieldGenerator(object):

    def __init__(self, fixed_mask, fields, free_space_list):

        self._fixed_mask = fixed_mask
        self._is_next_key = True
        self._free_space_list = free_space_list
        self._free_space_pos = 0
        self._next_key_read = False

        expanded_mask = utility_calls.expand_to_bit_array(fixed_mask)
        zeros = numpy.where(expanded_mask == 0)[0]
        self._n_mask_keys = 2 ** len(zeros)

        # If there are no fields, add the mask as a field
        the_fields = fields
        if fields is None or len(fields) == 0:
            n_ones = 32 - len(zeros)
            field_max = (2 ** n_ones) - 1
            the_fields = [Field(0, field_max, fixed_mask)]

        # Check that the fields don't cross each other
        for field in the_fields:
            for other_field in the_fields:
                if field != other_field and field.mask & other_field.mask != 0:
                    raise PacmanRouteInfoAllocationException(
                        "Field masks {} and {} overlap".format(
                            field.mask, other_field.mask))

        # Sort the fields by highest bit range first
        self._fields = sorted(the_fields, key=lambda field: field.mask,
                              reverse=True)

        self._update_next_valid_fields()
        self._increment_space_until_valid_key()

    def _get_current_space_end_address(self):
        current_space = self._free_space_list[self._free_space_pos]
        return current_space.start_address + current_space.size

    def _increment_space_until_valid_key(self):
        while (self._is_next_key and self._get_next_key() >=
                self._get_current_space_end_address()):
            self._free_space_pos += 1
            self._update_next_valid_fields()

    def _update_next_valid_fields(self):

        # Find the next valid key for the general mask
        min_key = self._free_space_list[self._free_space_pos].start_address
        if min_key & self._fixed_mask != min_key:
            min_key = (min_key + self._n_mask_keys) & self._fixed_mask

        # Generate a set of indices of ones for each field, and then store
        # the current value of each field given the minimum key (even if the
        # value might be out of range for the key - see later for fix for this)
        self._field_ones = dict()
        self._field_value = dict()
        for field in self._fields:
            expanded_mask = utility_calls.expand_to_bit_array(field.mask)
            field_ones = numpy.where(expanded_mask == 1)[0]
            self._field_ones[field] = field_ones
            field_min_key = min_key & field.mask
            field_min_value = utility_calls.compress_bits_from_bit_array(
                utility_calls.expand_to_bit_array(field_min_key), field_ones)
            self._field_value[field] = field_min_value

        # Update the values (other than the top value) to be valid
        for field_no in reversed(range(1, len(self._fields))):
            field = self._fields[field_no]
            previous_field = self._fields[field_no - 1]

            # If this value is too small, set it to its minimum
            if self._field_value[field] < field.lo:
                self._field_value[field] = field.lo

            # If this value is too large, set it to its minimum
            # and up the value of the next field
            if self._field_value[field] > field.hi:
                self._field_value[field] = field.lo
                self._field_value[previous_field] += 1

        # If the top value is above its valid range, there are no valid keys
        top_field = self._fields[0]
        if self._field_value[top_field] > top_field.hi:
            self._is_next_key = False

        # If the top value is below its valid range, set it to the first valid
        # value
        if self._field_value[top_field] < top_field.lo:
            self._field_value[top_field] = top_field.lo

    def _increment_key(self):

        # Update the key
        fields_updated = False
        field_no = len(self._fields) - 1
        while not fields_updated and field_no >= 0:
            field = self._fields[field_no]
            self._field_value[field] = self._field_value[field] + 1
            if self._field_value[field] > field.hi:
                self._field_value[field] = field.lo
                field_no -= 1
            else:
                fields_updated = True

        # If the first field is now too big, there are no more keys
        first_field = self._fields[0]
        if self._field_value[first_field] > first_field.hi:
            self._is_next_key = False

        self._increment_space_until_valid_key()

    def _get_next_key(self):

        # Form the key from the value of the fields
        expanded_key = numpy.zeros(32, dtype="uint8")
        for field in self._fields:
            field_ones = self._field_ones[field]
            expanded_value = utility_calls.expand_to_bit_array(
                self._field_value[field])
            expanded_key[field_ones] = expanded_value[-len(field_ones):]
        key = utility_calls.compress_from_bit_array(expanded_key)

        # Return the generated key
        return key

    @property
    def is_next_key(self):
        if self._next_key_read:
            self._increment_key()
            self._next_key_read = False
        return self._is_next_key

    @property
    def next_key(self):

        # If there are no more keys, return None
        if not self._is_next_key:
            return None
        self._next_key_read = True
        return self._get_next_key()

    def __iter__(self):
        return self

    def next(self):
        if not self.is_next_key:
            raise StopIteration
        return self.next_key
