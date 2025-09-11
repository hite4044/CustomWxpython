from typing import TypeVar, Type

import wx

T = TypeVar("T")

def DelayInitWrapper(class_type: Type[T]) -> T:
    return DelayInitWrapperClass(class_type)


class DelayInitWrapperClass:
    def __init__(self, class_type):
        self._class_type = class_type
        self._instance = None
        self.__setattr__ = self.r_setattr

    def _checkInstance(self):
        try:
            if super().__getattribute__("_instance") is None:
                if wx.GetApp():
                    super().__setattr__("_instance", self._class_type())
        except AssertionError:
            pass

    def __getattr__(self, name):
        self._checkInstance()
        return getattr(self._instance, name)

    def r_setattr(self, key, value):
        self._checkInstance()
        return setattr(self._instance, key, value)

    def __repr__(self):
        self._checkInstance()
        return repr(self._instance)
