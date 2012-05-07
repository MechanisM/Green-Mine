# -*- coding: utf-8 -*-

from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from greenmine.utils import Singleton

def load_class(path):
    """
    Load class from path.
    """

    try:
        mod_name, klass_name = path.rsplit('.', 1)
        mod = import_module(mod_name)
    except AttributeError as e:
        raise ImproperlyConfigured(u'Error importing %s: "%s"' % (mod_name, e))

    try:
        klass = getattr(mod, klass_name)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" class' % (mod_name, klass_name))

    return klass


class Library(object):
    __metaclass__ = Singleton
    __tasks__ = {}

    @classmethod
    def task_list(cls):
        for _name, _task in cls.__tasks__.iteritems():
            yield _name, _task

    @classmethod
    def task_by_name(cls, name):
        if name not in cls.__tasks__:
            raise ValueError("task %s does not exist or not registred" % (name))
        return cls.__tasks__[name]

    @classmethod
    def add_to_class(cls, name, func):
        cls.__tasks__[name] = func
        return func

    def task(self, name=None, compile_function=None):
        if name is None and compile_function is None:
            # @register.tag()
            return self.task_function
        elif name is not None and compile_function is None:
            if callable(name):
                # @register.tag
                return self.task_function(name)
            else:
                # @register.tag('somename') or @register.tag(name='somename')
                def dec(func):
                    return self.task(name, func)
                return dec
        elif name is not None and compile_function is not None:
            # register.tag('somename', somefunc)
            self._tasks[name] = compile_function
            return compile_function
        else:
            raise ImproperlyConfigured("invalid task registration")

    def task_function(self, func):
        self._tasks[getattr(func, "_decorated_function", func).__name__] = func
        return func
