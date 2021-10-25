# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from inspect import getfullargspec
from functools import wraps
_instances = list()
_methods = defaultdict(dict)
_injectables = None


class InjectionException(Exception):
    """ Raised when there is an error with injection.
    """


def inject_items(types):
    """ A :py:obj:`decorator` that ndicates values that need to be injected
        into the method

    :param types: A dict of method argument name to type name to be injected
    :type types: dict(str, str)
    """
    def wrap(wrapped_method):
        exn_arg = None
        method_args = getfullargspec(wrapped_method)
        for type_arg in types:
            if type_arg not in method_args.args:
                # Can't raise exception until run time
                exn_arg = type_arg
                break

        @wraps(wrapped_method)
        def wrapper(obj, *args, **kwargs):
            if exn_arg is not None:
                raise InjectionException(
                    "Argument {} does not exist for method {} of {}".format(
                        exn_arg, wrapped_method.__name__, obj.__class__))
            if _injectables is None:
                raise InjectionException(
                    "No injectable objects have been provided")
            new_args = dict(kwargs)
            for arg, arg_type in types.items():
                if arg_type not in _injectables:
                    raise InjectionException(
                        "Cannot find object of type {} to inject into"
                        " method {} of {}".format(
                            arg_type, wrapped_method.__name__, obj.__class__))
                if arg in new_args:
                    raise InjectionException(
                        "Argument {} was already provided to"
                        " method {} of {}".format(
                            arg, wrapped_method.__name__, obj.__class__))
                new_args[arg] = _injectables[arg_type]
            return wrapped_method(obj, *args, **new_args)
        return wrapper
    return wrap


def provide_injectables(injectables):
    """ Set the objects from which values should be injected into methods

    :param injectables: A dict of type to value
    :type injectables: dict(str, ...)
    """
    global _injectables
    if _injectables is not None:
        raise InjectionException("Injectables have already been defined")
    _injectables = injectables


def clear_injectables():
    """ Clear the current set of injectables
    """
    global _injectables
    _injectables = None


class _DictFacade(dict):
    """ Provides a dict of dict overlay so that container-ship is True if any\
        one of the dict objects contains the items and the item is returned\
        from the first dict.
    """
    def __init__(self, dicts):
        """
        :param dicts: An iterable of dict objects to be used
        """
        super().__init__()
        self._dicts = dicts

    def get(self, key, default=None):
        for d in self._dicts:
            if key in d:
                return d[key]
        return default

    def __getitem__(self, key):
        for d in self._dicts:
            try:
                return d.__getitem__(key)
            except KeyError:
                pass
        raise KeyError(key)

    def __contains__(self, item):
        return any(item in d for d in self._dicts)


class injection_context(object):
    """ Provides a context for injection to use with `with`.
    """

    def __init__(self, injection_dictionary):
        """
        :param injection_dictionary:
            The dictionary of items to inject whilst in the context
        :type injection_dictionary: dict(str, ...)
        """
        self._old = None
        self._mine = injection_dictionary

    def __enter__(self):
        global _injectables
        dicts = [self._mine]
        if _injectables is not None:
            dicts.append(_injectables)
        self._old = _injectables
        _injectables = _DictFacade(dicts)

    def __exit__(self, a, b, c):
        global _injectables
        _injectables = self._old
        return False
