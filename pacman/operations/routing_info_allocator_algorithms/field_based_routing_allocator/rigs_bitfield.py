"""A system for defining and representing bit fields.

A common use-case for this module is defining SpiNNaker routing keys based on
hierarchical bit-fields.

See the :py:class:`.BitField` class.
"""

from six import iteritems

from collections import OrderedDict

from math import log


class RigsBitField(object):
    """Defines a hierarchical bit field and the values of those fields.

    Conceptually, a bit field is a sequence of bits which are logically broken
    up into individual fields which represent independent, unsigned integer
    values. For example, one could represent a pair of eight-bit values `x` and
    `y` as a sixteen-bit bit field where the upper eight bits are `x` and the
    lower eight bits are `y`. Bit fields are used when multiple pieces of
    information must be conveyed by a single binary value.

    For example, one method of allocating SpiNNaker routing keys (which are
    32-bit values) is to define each route a key as bit field with three
    fields. The fields `x`, `y`, and `p` can be used to represent the x- and
    y-chip-coordinate and processor id of a route's source.

    A hierarchical bit field is a bit field with fields which only exist
    dependent on the values of other fields. For a further routing-key related
    example, different key formats may be used by external devices and the rest
    of the SpiNNaker application. In these cases, a single bit could be used in
    the key to determine which key format is in use. Depending on the value of
    this bit, different fields would become available.

    This class supports the following key features:

    * Construction of guaranteed-safe hierarchical bit field formats.
    * Generation of bit-masks which select only defined fields
    * Automatic allocation of field sizes based on values actually used.
    * Partial-definition of a bit field (i.e. defining only a subset of
      available fields).
    """

    def __init__(self, length=32, _fields=None, _field_values=None):
        """Create a new BitField.

        An instance, `b`, of :py:class:`.BitField` represents a fixed-length
        hierarchical bit field with initially no fields. Fields can be added
        using :py:meth:`.BitField.add_field`. Derivatives of this instance
        with fields set to specific values can be created using the 'call'
        syntax: `b(field_name=value, other_field_name=other_value)` (see
        :py:meth:`.BitField.__call__`).

        .. Note::
            Only one :py:class:`.BitField` instance should be explicitly
            created for each bit field.

        Parameters
        ----------
        length : int
            The total number of bits in the bit field.
        _fields : :py:class:`._Tree`
            For internal use only. The shared, global field tree.
        _field_values : dict
            For internal use only. Mapping of field-identifier to value.
        """
        self.length = length

        # Fields are kept in a tree structure where child fields only exist
        # when their parents have a particular value.
        self.fields = _fields if _fields is not None else type(self)._Tree()

        if _field_values is not None:
            self.field_values = _field_values
        else:
            self.field_values = dict()

    def add_field(self, identifier, length=None, start_at=None, tags=None):
        """Add a new field to the BitField.

        If any existing fields' values are set, the newly created field will
        become a child of those fields. This means that this field will exist
        only when the parent fields' values are set as they are currently.

        Parameters
        ----------
        identifier : str
            A identifier for the field. Must be a valid python identifier.
            Field names must be unique within the scope in which they exist and
            are only valid within that scope. For example::

                >>> bf = BitField(32)
                >>> bf.add_field("a")

                >>> # Can add multiple fields with the same name if they exist
                >>> # in different scopes
                >>> bf0 = bf(a=0)
                >>> bf0.add_field("b", length=4)
                >>> bf1 = bf(a=1)
                >>> bf1.add_field("b", length=8)

                >>> # Can't add multiple fields with the same name which exist
                >>> # within the same or nested scopes.
                >>> bf.add_field("a")
                Traceback (most recent call last):
                ValueError: Field with identifier 'a' already exists
                >>> bf.add_field("b")
                Traceback (most recent call last):
                ValueError: Field with identifier 'b' already exists

            Here *three* fields are defined, one called "a" and the other two
            called "b". The two fields called "b" are completely unrelated
            (they may differ in size, position and associated set of tags) and
            are distinguished by the fact that one exists when a=0 and the
            other when a=1.
        length : int or None
            The number of bits in the field. If None the field will be
            automatically assigned a length long enough for the largest value
            assigned.
        start_at : int or None
            0-based index of least significant bit of the field within the
            bit field. If None the field will be automatically located in free
            space in the bit field.
        tags : string or collection of strings or None
            A (possibly empty) set of tags used to classify the field.  Tags
            should be valid Python identifiers. If a string, the string must be
            a single tag or a space-separated list of tags. If *None*, an empty
            set of tags is assumed. These tags are applied recursively to all
            fields of which this field is a child.

        Raises
        ------
        ValueError
            If any the field overlaps with another one or does not fit within
            the bit field. Note that fields with unspecified lengths and
            positions do not undergo such checks until their length and
            position become known when :py:meth:`.assign_fields` is called.
        """
        # Check for zero-length fields
        if length is not None and length <= 0:
            raise ValueError("Fields must be at least one bit in length.")

        # Check for fields which don't fit in the bit field
        if (start_at is not None and
            (0 <= start_at >= self.length or
             start_at + (length or 1) > self.length)):
            raise ValueError(
                "Field doesn't fit within {}-bit bit field.".format(
                    self.length))

        # Check for fields which occupy the same bits
        if start_at is not None:
            end_at = start_at + (length or 1)
            for other_identifier, other_field in \
                    self.fields.potential_fields(self.field_values):
                if other_field.start_at is not None:
                    other_start_at = other_field.start_at
                    other_end_at = other_start_at + (other_field.length or 1)

                    if end_at > other_start_at and other_end_at > start_at:
                        raise ValueError(
                            "Field '{}' (range {}-{}) "
                            "overlaps field '{}' (range {}-{})".format(
                                identifier,
                                start_at, end_at,
                                other_identifier,
                                other_start_at, other_end_at))

        # Normalise tags type
        if type(tags) is str:
            tags = set(tags.split())
        elif tags is None:
            tags = set()
        else:
            tags = set(tags)

        # Add the field (checking that the identifier is unique in the process)
        field = type(self)._Field(length, start_at, tags)
        self.fields.add_field(field, identifier, self.field_values)

        # Add tags to all parents of this field
        for parent_identifier in self.fields.get_field_requirements(
                identifier, self.field_values):
            parent = self.fields.get_field(parent_identifier,
                                           self.field_values)
            parent.tags.update(tags)

    def __call__(self, **field_values):
        """Return a new BitField instance with fields assigned values as
        specified in the keyword arguments.

        Returns
        -------
        :py:class:`.BitField`
            A `BitField` derived from this one but with the specified fields
            assigned a value.

        Raises
        ------
        ValueError
            If any field has already been assigned a value or the value is too
            large for the field.
        UnavailableFieldError
            If a field is specified which does not exist or is not available.
        """
        # Make sure no values are changed
        for identifier, value in self.field_values.items():
            if identifier in field_values:
                raise ValueError(
                    "Field '{}' already has value.".format(identifier))

        # Work out what the new set of defined values looks like
        field_values.update(self.field_values)

        for identifier, value in field_values.items():
            # All fields specified must exist (and be enabled)
            field = self.fields.get_field(identifier, field_values)

            # All field values must be within range
            if value < 0:
                raise ValueError("Fields must be positive.")
            elif field.length is not None and value >= (1 << field.length):
                raise ValueError(
                    "Value {} too large for {}-bit field '{}'.".format(
                        value, field.length, identifier))

        # Everything looks good!

        # Update maximum observed values
        for identifier, value in field_values.items():
            field = self.fields.get_field(identifier, field_values)
            field.max_value = max(field.max_value, value)

        # Finally, create a new BitField with the specified values
        return type(self)(self.length, self.fields, field_values)

    def __getattr__(self, identifier):
        """Get the value of a field.

        Returns
        -------
        int or None
            The value of the field (or None if the field has not been given a
            value).

        Raises
        ------
        UnavailableFieldError
            If the field requested does not exist or is not available given
            current field values.
        """
        # Ensure that the field exists/is available
        self.fields.get_field(identifier, self.field_values)

        return self.field_values.get(identifier, None)

    def get_value(self, tag=None, field=None):
        """Generate an integer whose bits are set according to the values of
        fields in this bit field. All other bits are set to zero.

        Parameters
        ----------
        tag : str
            Optionally specifies that the value should only include fields with
            the specified tag.
        field : str
            Optionally specifies that the value should only include the
            specified field.

        Raises
        ------
        ValueError
            If a field's value, length or position has not been defined. (e.g.
            :py:meth:`.assign_fields` has not been called).
        UnknownTagError
            If the tag specified using the `tag` argument does not exist.
        UnavailableFieldError
            If the field specified using the `field` argument does not exist or
            is not available.
        """
        assert not (tag is not None and field is not None), \
            "Cannot filter by tag and field simultaneously."

        selected_fields = self._select_by_field_or_tag(tag, field)

        # Check all selected fields have values defined
        missing_fields_idents = set(selected_fields) - set(self.field_values)
        if missing_fields_idents:
            raise ValueError(
                "Cannot generate value with undefined fields {}.".format(
                    ", ".join("'{}'".format(f)
                              for f in missing_fields_idents)))

        # Build the value
        value = 0
        for identifier, field in iteritems(selected_fields):
            if field.length is None or field.start_at is None:
                raise ValueError(
                    "Field '{}' does not have a fixed size/position.".format(
                        identifier))
            value |= (self.field_values[identifier] <<
                      field.start_at)

        return value

    def get_mask(self, tag=None, field=None):
        """Get the mask for all fields which exist in the current bit field.

        Parameters
        ----------
        tag : str
            Optionally specifies that the mask should only include fields with
            the specified tag.
        field : str
            Optionally specifies that the mask should only include the
            specified field.

        Raises
        ------
        ValueError
            If a field's length or position has not been defined. (e.g.
            :py:meth:`.assign_fields` has not been called).
        UnknownTagError
            If the tag specified using the `tag` argument does not exist.
        UnavailableFieldError
            If the field specified using the `field` argument does not exist or
            is not available.
        """
        if tag is not None and field is not None:
            raise TypeError("get_mask() takes exactly one keyword argument, "
                            "either 'field' or 'tag' (both given)")

        selected_fields = self._select_by_field_or_tag(tag, field)

        # Build the mask (and throw an exception if we encounter a field
        # without a fixed size/length.
        mask = 0
        for identifier, field in iteritems(selected_fields):
            if field.length is None or field.start_at is None:
                raise ValueError(
                    "Field '{}' does not have a fixed size/position.".format(
                        identifier))
            mask |= ((1 << field.length) - 1) << field.start_at

        return mask

    def _select_by_field_or_tag(self, tag=None, field=None):
        """For internal use only. Returns an OrderedDict of {identifier: field}
        representing fields which match the supplied field/tag.

        Parameters
        ----------
        tag : str
            Optionally specifies that the mask should only include fields with
            the specified tag.
        field : str
            Optionally specifies that the mask should only include the
            specified field.

        Raises
        ------
        UnknownTagError
            If the tag specified using the `tag` argument does not exist.
        UnavailableFieldError
            If the field specified using the `field` argument does not exist or
            is not available.
        """
        # Get the set of fields whose values will be included in the value
        if field is not None:
            # Select just the specified field (checking the field exists)
            field_obj = self.fields.get_field(field, self.field_values)
            selected_fields = OrderedDict([(field, field_obj)])
        elif tag is not None:
            # Select just fields with the specified tag
            selected_fields = OrderedDict(
                (i, f)
                for (i, f) in self.fields.enabled_fields(self.field_values)
                if tag in f.tags)
            # Fail if no fields match the supplied tag. Because tags are
            # applied to parent fields in the hierarchy, it is guaranteed that
            # if a tag exists, at least one top-level (i.e. always present)
            # field will have the tag.
            if not selected_fields:
                raise UnknownTagError(tag)
        else:
            # No specific field/tag supplied, select all enabled fields.
            selected_fields = OrderedDict(
                (i, f)
                for (i, f) in self.fields.enabled_fields(self.field_values))

        return selected_fields

    def get_tags(self, field):
        """Get the set of tags for a given field.

        .. note::
            The named field must be accessible given the current set of values
            defined.

        Parameters
        ----------
        field : str
            The field whose tag should be read.

        Returns
        -------
        set([tag, ...])

        Raises
        ------
        UnavailableFieldError
            If the field does not exist or is not available.
        """
        return self.fields.get_field(field, self.field_values).tags.copy()

    def assign_fields(self):
        """Assign a position & length to any fields which do not have one.

        Users should typically call this method after all field values have
        been assigned, otherwise fields may be fixed at an inadequate size.
        """
        # We must fix fields at every level of the hierarchy separately
        # (otherwise fields of children won't be allowed to overlap). Here we
        # do a breadth-first iteration over the hierarchy to fix fields with
        # given starting positions; then we do depth-first to fix other fields.

        # Assign all fields with a fixed starting position in breadth first,
        # top-down order. The breadth-first ensures that children's fixed
        # position fields must fit around the fixed position fields of their
        # parents.
        queue = [(self.fields, {})]
        while queue:
            node, field_values = queue.pop(0)

            # Assign all fields at this level whose position is fixed
            self._assign_fields(node.fields, field_values,
                                assign_positions=False)

            # Breadth-first search through children
            for requirements, child in iteritems(node.children):
                requirements = dict(requirements)
                requirements.update(field_values)
                queue.append((child, requirements))

        # Assign all fields with movable starting positions in leaf-first,
        # depth-first order.  The depth first ordering for variable position
        # fields ensures that parents don't allocate fields in positions which
        # would collide with fixed and variable position fields their children
        # have already allocated.

        def recurse_assign_fields(node=self.fields, field_values={}):
            # Assign fields of child nodes first (allowing them to allocate
            # bits independently)
            for requirements, child in iteritems(node.children):
                child_field_values = dict(requirements)
                child_field_values.update(field_values)
                recurse_assign_fields(child, child_field_values)

            # Finally, assign all remaining fields at this level in the tree
            self._assign_fields(node.fields, field_values,
                                assign_positions=True)
        recurse_assign_fields()

    def __eq__(self, other):
        """Test that this :py:class:`.BitField` is equivalent to another.

        In order to be equal, the other :py:class:`.BitField` must be a
        descendent of the same original :py:class:`.BitField` (and thus will
        *always* have exactly the same set of fields). It must also have the
        same field values defined.
        """
        return (self.length == other.length and
                self.fields is other.fields and
                self.field_values == other.field_values)

    def __repr__(self):
        """Produce a human-readable representation of this bit field and its
        current value.
        """
        enabled_field_idents = [
            i for (i, f) in self.fields.enabled_fields(self.field_values)]

        return "<{}-bit {}{}{}>".format(
            self.length,
            type(self).__name__,
            " " if enabled_field_idents else "",
            ", ".join("'{}':{}".format(identifier,
                                       self.field_values.get(identifier, "?"))
                      for identifier in enabled_field_idents))

    class _Field(object):
        """Internally used class which defines a field.
        """

        def __init__(self, length=None, start_at=None, tags=None,
                     conditions=None, max_value=1):
            """Field definition used internally by :py:class:`.BitField`.

            Parameters/Attributes
            ---------------------
            length : int
                The number of bits in the field. *None* if this should be
                determined based on the values assigned to it.
            start_at : int
                0-based index of least significant bit of the field within the
                bit field.  *None* if this field is to be automatically placed
                into an unused area of the bit field.
            tags : set
                A (possibly empty) set of tags used to classify the field.
            max_value : int
                The largest value ever assigned to this field (used for
                automatically determining field sizes.
            """
            self.length = length
            self.start_at = start_at
            self.tags = tags or set()
            self.max_value = max_value

    class _Tree(object):
        """A tree representing a hierarchy of fields."""

        def __init__(self, fields=None, children=None):
            """Create a node in the tree of fields.

            Parameters
            ----------
            fields : OrderedDict or None
                A mapping from field identifier to :py:class:`._Field` for
                fields which exist at this point in the hierarchy.
            children : OrderedDict or None
                A mapping from a non-empty tuples ((identifier, value), ...) to
                [_Tree, ...] defining set of field values which must be defined
                for the specified children to become available.
            """
            self.fields = fields or OrderedDict()
            self.children = children or OrderedDict()

        def add_field(self, field, identifier, field_values):
            """Add a new _Field to the tree.

            Parameters
            ----------
            field : :py:class:`._Field`
                The field to be added
            identifier : str
                A identifier for the field. Must be unique within the scope in
                which it exists.
            field_values : {identifier: int, ...}
                The field values which must be set for this field to exist. All
                identifiers must correspond to actual field values.

            Raises
            ------
            ValueError
                If the identifier is not unique within the scope supplied.
            """
            # Check the identifier is not already in use
            if identifier in (i for (i, f) in
                              self.potential_fields(field_values)):
                raise ValueError("Field with identifier '{}' already "
                                 "exists".format(identifier))

            if not field_values:
                # If no field_values need be specified, add the field at this
                # point in the hierarchy
                self.fields[identifier] = field
            else:
                # The field depends on some fields being defined with a
                # particular value; descend the hierarchy.

                # Get the child node which has the specified set of values and
                # add the field to that. (Note that requirement order mimics
                # the order of field definition.)
                meetable_requirements = tuple(
                    (i, field_values[i]) for (i, f) in iteritems(self.fields)
                    if i in field_values
                )
                child = self.children.setdefault(meetable_requirements,
                                                 type(self)())
                child.add_field(field, identifier,
                                {i: v for (i, v) in iteritems(field_values)
                                 if i not in dict(meetable_requirements)})

        def get_field(self, identifier, field_values):
            """Get the _Field object associated with a given identifier when the
            given set of field values are present.

            Parameters
            ----------
            identifier : str
            field_values : {identifier: int, ...}

            Returns
            -------
            :py:class:`._Field`

            Raises
            ------
            UnavailableFieldError
                If a field with the specified identifier is not present or is
                not accessible with the supplied set of values.
            """
            if identifier in self.fields:
                return self.fields[identifier]
            else:
                for requirements, child in self._enabled_children(
                        field_values):
                    try:
                        return child.get_field(identifier, field_values)
                    except UnavailableFieldError:
                        # Try the next child...
                        pass

            raise UnavailableFieldError(self, identifier, field_values)

        def get_field_requirements(self, identifier, field_values):
            """Get minimum subset of field_values which must be set for the
            given (already enabled) identifier to be enabled.

            Parameters
            ----------
            identifier : str
            field_values : {identifier: int, ...}

            Returns
            -------
            {identifier: int, ...}

            Raises
            ------
            UnavailableFieldError
                If a field with the specified identifier is not present or is
                not accessible with the supplied set of values.
            """
            if identifier in self.fields:
                # The field is part of this node and so no values need be set
                return OrderedDict()
            else:
                for child_requirements, child in self._enabled_children(
                        field_values):
                    try:
                        sub_requirements = child.get_field_requirements(
                            identifier, field_values)
                        requirements = OrderedDict(child_requirements)
                        requirements.update(sub_requirements)
                        return requirements
                    except UnavailableFieldError:
                        # Try the next child...
                        pass

            raise UnavailableFieldError(self, identifier, field_values)

        def get_field_candidates(self, identifier, field_values):
            """Get the possible sets of additional field values which could be
            set to enable an identifier with the specified name.

            Useful for generating helpful error messages.

            Parameters
            ----------
            identifier : str
            field_values : {identifier: int, ...}

            Returns
            -------
            [{identifier: value, ...}, ...]
                With a minimal set of additional field values which must be set
                to access a field with the supplied identifier. Empty list if
                a field with the identifier is not reachable given the current
                values (or if it doesn't exist at all).
            """
            candidates = []

            if identifier in self.fields:
                # No additional requirements!
                candidates.append({})
            else:
                # Look in any children for matching fields, adding any
                # additional requirements introduced as we go.
                for requirements, child in self._potential_children(
                        field_values):
                    for candidate in child.get_field_candidates(identifier,
                                                                field_values):
                        # Gather any additional requirements
                        for i, v in requirements:
                            if field_values.get(i, None) != v:
                                candidate[i] = v
                        candidates.append(candidate)

            return candidates

        def get_field_human_readable(self, identifier, field_values):
            """Get a human-readable representation of a field's fully-specified
            name.

            This representation includes any qualifying field values which must
            be set. The format looks like this::

                >>> t = BitField._Tree()
                >>> t.add_field(object(), "a", {})
                >>> t.add_field(object(), "b", {})
                >>> t.add_field(object(), "c", {"a": 0})

                >>> # Just reports the name of fields which don't have any
                >>> # field value requirements.
                >>> t.get_field_human_readable("a", {})
                "'a'"
                >>> t.get_field_human_readable("a", {"a": 0, "b": 1})
                "'a'"

                >>> # Prints field value requirements when present
                >>> t.get_field_human_readable("c", {"a": 0})
                "'c' ('a':0)"
                >>> t.get_field_human_readable("c", {"a": 0, "b": 1})
                "'c' ('a':0)"
            """
            requirements = self.get_field_requirements(identifier,
                                                       field_values)
            if requirements:
                return "'{}' ({})".format(
                    identifier,
                    ", ".join("'{}':{}".format(i, v)
                              for (i, v) in iteritems(requirements))
                )
            else:
                return "'{}'".format(identifier)

        def _enabled_children(self, field_values):
            """Iterate over (frozenset((identifier, int), ...), child) tuples
            which are accessible with the specified field values set.

            Iteration proceeds in a depth-first fashion with the ordering of
            each level of the hierarchy matching insertion order.

            Parameters
            ----------
            field_values : {identifier: int, ...}

            Generates
            ---------
            (((identifier, int), ...), :py:class:`_Tree`)
            """
            for requirements, child in iteritems(self.children):
                # Skip children with unfulfilled requirements
                conflict = False
                for ident, value in requirements:
                    if ident not in field_values or \
                            value != field_values[ident]:
                        conflict = True
                        break
                if not conflict:
                    yield (requirements, child)

        def enabled_fields(self, field_values):
            """Iterate over all accessible (identifier, field) pairs.

            This iterator excludes fields which need additional or different
            field values setting. Iteration proceeds in a depth-first fashion
            with the ordering of each level of the hierarchy matching insertion
            order.
            """
            for identifier, field in iteritems(self.fields):
                yield (identifier, field)

            for requirements, child in self._enabled_children(field_values):
                for identifier, field in child.enabled_fields(field_values):
                    yield (identifier, field)

        def _potential_children(self, field_values):
            """Iterate over (frozenset((identifier, int), ...), child) tuples
            which don't have field value requirements which conflict with those
            given.

            This iterator includes children which require additional field
            values to be set but excludes children which require field values
            which don't match those supplied. Iteration proceeds in a
            depth-first fashion with the ordering of each level of the
            hierarchy matching insertion order.

            Parameters
            ----------
            field_values : {identifier: int, ...}

            Generates
            ---------
            (((identifier, int), ...), :py:class:`_Tree`)
            """
            for requirements, child in iteritems(self.children):
                # Skip children with conflicting requirements
                conflict = False
                for ident, value in requirements:
                    if ident in field_values and value != field_values[ident]:
                        conflict = True
                        break
                if not conflict:
                    yield (requirements, child)

        def potential_fields(self, field_values):
            """Iterate over all potentially accessible (identifier, field)
            pairs.

            This iterator includes fields which may not yet be accessible (but
            which could be with additional field values set) but not fields
            which require a different set of field_values set. Iteration
            proceeds in a depth-first fashion with the ordering of each level
            of the hierarchy matching insertion order.
            """
            for identifier, field in iteritems(self.fields):
                yield (identifier, field)

            for requirements, child in self._potential_children(field_values):
                for identifier, field in child.potential_fields(field_values):
                    yield (identifier, field)

    def _assign_fields(self, identifiers, field_values,
                       assign_positions, assigned_bits=0):
        """For internal use only.  Assign lengths & positions to a subset of all
        potential fields with the supplied field_values.

        This method will check for any assigned bits of all potential fields
        but will only assign those fields whose identifiers are provided.

        Parameters
        ----------
        identifiers : iterable of identifiers
            The identifiers of the fields to assign
        field_values : {identifier: value, ...}
            The values held by various fields (used to access the correct
            identifiers)
        assign_positions : bool
            If False, will only assign lengths to fields whose positions are
            already known. Otherwise lengths and positions will be assigned to
            all fields as necessary.
        assigned_bits : int
            A bit mask of bits which are already allocated. (Note that this
            will automatically be extended with any already-assigned potential
            fields' bits.)

        Returns
        -------
        int
            Mask of which bits which are assigned to fields after fields have
            been assigned.
        """
        # Calculate a mask of already allocated fields' bits
        for i, f in self.fields.potential_fields(field_values):
            if f.length is not None and f.start_at is not None:
                assigned_bits |= ((1 << f.length) - 1) << f.start_at

        # Allocate all specified fields
        for identifier in identifiers:
            field = self.fields.get_field(identifier, field_values)
            if field.length is not None and field.start_at is not None:
                # Already allocated, do nothing!
                pass
            elif assign_positions or field.start_at is not None:
                assigned_bits |= self._assign_field(assigned_bits,
                                                    identifier,
                                                    field_values)

        return assigned_bits

    def _assign_field(self, assigned_bits, identifier, field_values):
        """For internal use only.  Assign a length and position to a field
        which may have either one of these values missing.

        Parameters
        ----------
        assigned_bits : int
            A bit mask of bits already in use by other fields
        identifier : str
            The identifier of the field to assign
        field_values : {identifier: value, ...}
            The values held by various fields (used to access the correct
            identifier)

        Returns
        -------
        int
            Mask of which bits which are assigned to fields after this field
            has been assigned.
        """
        field = self.fields.get_field(identifier, field_values)

        length = field.length
        if length is None:
            # Assign lengths based on values
            length = int(log(field.max_value, 2)) + 1

        start_at = field.start_at
        if start_at is None:
            # Force a failure if no better space is found
            start_at = self.length

            # Try every position until a space is found
            for bit in range(0, self.length - length):
                field_bits = ((1 << length) - 1) << bit
                if not (assigned_bits & field_bits):
                    start_at = bit
                    assigned_bits |= field_bits
                    break
        else:
            # A start position has been forced, ensure that it can be fulfilled
            field_bits = ((1 << length) - 1) << start_at

            if assigned_bits & field_bits:
                raise ValueError(
                    "{}-bit field {} with fixed position does not fit in "
                    "{}.".format(
                        field.length,
                        self.fields.get_field_human_readable(identifier,
                                                             field_values),
                        type(self).__name__
                    )
                )

            # Mark these bits as assigned
            assigned_bits |= field_bits

        # Check that the calculated field is within the bit field
        if start_at + length <= self.length:
            field.length = length
            field.start_at = start_at
        else:
            raise ValueError(
                "{}-bit field {} does not fit in {}.".format(
                    field.length,
                    self.fields.get_field_human_readable(identifier,
                                                         field_values),
                    type(self).__name__
                )
            )

        return assigned_bits


class UnknownTagError(LookupError):
    """Exception thrown when a tag is specified which does not exist."""

    def __init__(self, tag):
        """Simply enclose the tag in quotes."""
        super(UnknownTagError, self).__init__("'{}'".format(tag))


class UnavailableFieldError(LookupError):
    """Exception thrown when a field is requested from a BitField which is not
    does not exist or is unavailable (i.e. not in scope)."""

    def __init__(self, tree, identifier, field_values):
        """Create a human-readable error explaining that a field with the
        supplied identifier was not found."""
        # Find all possible instances of the supplied identifier (even those
        # which are blocked)
        candidates = tree.get_field_candidates(identifier, {})

        # Sanity check: the identifier shouldn't be available
        assert {} not in candidates

        # Split candidates into two groups: those which can be reached
        # without changing a field value...
        possible = [candidate for candidate in candidates
                    if not set(candidate).intersection(set(field_values))]
        # ...and those where an existing field value must be changed
        impossible = [candidate for candidate in candidates
                      if set(candidate).intersection(set(field_values))]

        if not candidates:
            # The supplied field either never existed or requires
            # contradictory field values.
            super(UnavailableFieldError, self).__init__(
                "Field '{}' does not exist.".format(identifier))
        elif possible:
            super(UnavailableFieldError, self).__init__(
                "Field '{}' is not available unless {}.".format(
                    identifier,
                    " OR ".join(
                        ", ".join("'{}':{}".format(i, v)
                                  for (i, v) in iteritems(candidate))
                        for candidate in possible)))
        else:  # impossible != []
            super(UnavailableFieldError, self).__init__(
                "Field '{}' is not available when {}.".format(
                    identifier,
                    " OR ".join(
                        ", ".join("'{}':{}".format(i, v)
                                  for (i, v) in iteritems(candidate)
                                  if i in field_values)
                        for candidate in impossible)))
