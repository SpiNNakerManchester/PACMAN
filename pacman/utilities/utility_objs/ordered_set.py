import collections


class _Node(object):

    def __init__(self, key, prev_node, next_node):
        self._key = key
        self._prev_node = prev_node
        self._next_node = next_node

    @property
    def key(self):
        return self._key

    @property
    def prev_node(self):
        return self._prev_node

    @prev_node.setter
    def prev_node(self, prev_node):
        self._prev_node = prev_node

    @property
    def next_node(self):
        return self._next_node

    @next_node.setter
    def next_node(self, next_node):
        self._next_node = next_node


class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):

        # sentinel node for doubly linked list
        # prev_node of end points to end of list (for reverse iteration)
        # next_node of end points to start of list (for forward iteration)
        self._end = _Node(None, None, None)
        self._end.prev_node = self._end
        self._end.next_node = self._end

        # key --> _Node
        self._map = dict()

        # or is overridden in mutable set; calls add on each element
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self._map)

    def __contains__(self, key):
        return key in self._map

    def add(self, key):
        if key not in self._map:
            end_prev = self._end.prev_node
            new_node = _Node(key, end_prev, self._end)
            self._map[key] = new_node
            end_prev.next_node = new_node
            self._end.prev_node = new_node

    def discard(self, key):
        if key in self._map:
            node = self._map.pop(key)
            prev_node = node.prev_node
            next_node = node.next_node
            node.prev_node.next_node = next_node
            node.next_node.prev_node = prev_node

    def __iter__(self):
        curr = self._end.next_node
        while curr is not self._end:
            yield curr.key
            curr = curr.next_node

    def __reversed__(self):
        curr = self._end.prev_node
        while curr is not self._end:
            yield curr.key
            curr = curr.prev_node

    def pop(self, last=True):
        if len(self._map) == 0:
            raise KeyError('set is empty')
        if last:
            key = self._end.prev_node.key
        else:
            key = self._end.next_node.key
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def __ne__(self, other):
        return not self.__eq__(other)
