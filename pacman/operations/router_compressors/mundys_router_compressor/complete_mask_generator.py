class CompleteMaskGenerator(object):
    """Iterator to generate variations of masks.

    .. todo:

        Track the time that the iterator has been used and stop yielding new
        masks once that maximum time has been passed.

        Try to avoid yielding masks that we've already yielded.
    """
    def __init__(self, masks, generators):
        self._masks = masks
        self._generators = generators

    def __iter__(self):
        # Try each generator in turn with each mask.
        for generator in self._generators:
            for mask in self._masks:
                for m in generator(*mask):
                    yield m