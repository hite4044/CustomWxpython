from inspect import stack

import wx

from ..dpi import SCALE


class ScaledBoxSizer(wx.BoxSizer):
    def __init__(self, orient: int = wx.HORIZONTAL, out_spacer: int = 0):
        super().__init__(orient)
        self.out_spacer = out_spacer

    def __enter__(self):
        if self.out_spacer != 0:
            self.AddSpacer(self.out_spacer)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.out_spacer != 0:
            self.AddSpacer(self.out_spacer)

    def AddSpacer(self, size):
        super().AddSpacer(round(size * SCALE))


class PaddedBoxSizer(wx.BoxSizer):
    def __init__(self, orient: int = wx.HORIZONTAL, padx: int = 0, pady: int = 0):
        super().__init__(wx.VERTICAL if orient == wx.HORIZONTAL else wx.HORIZONTAL)
        self.orient = orient
        self.real_sizer = wx.BoxSizer(orient)
        self.padx = padx
        self.pady = pady

        if orient == wx.HORIZONTAL:
            self.add_pad(super(), self.padx)
        elif orient == wx.VERTICAL:
            self.add_pad(super(), self.pady)
        super().Add(self.real_sizer, 1, wx.EXPAND)
        if orient == wx.HORIZONTAL:
            self.add_pad(super(), self.padx)
        elif orient == wx.VERTICAL:
            self.add_pad(super(), self.pady)

    @staticmethod
    def add_pad(sizer: wx.BoxSizer, abs_size: int):
        if abs_size == 0:
            return
        if abs_size == -1:
            sizer.AddStretchSpacer(1)
        else:
            sizer.AddSpacer(round(abs_size * SCALE))

    def __enter__(self):
        if self.orient == wx.HORIZONTAL:
            self.add_pad(self.real_sizer, self.padx)
        elif self.orient == wx.VERTICAL:
            self.add_pad(self.real_sizer, self.pady)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.orient == wx.HORIZONTAL:
            self.add_pad(self.real_sizer, self.padx)
        elif self.orient == wx.VERTICAL:
            self.add_pad(self.real_sizer, self.pady)

    def Add(self, *args, **kw):
        self.real_sizer.Add(*args, **kw)

    def AddMany(self, items):
        self.real_sizer.AddMany([(item, 0, wx.EXPAND) for item in items])

    def AddStretchSpacer(self, prop=1):
        self.real_sizer.AddStretchSpacer(prop)

    def AddSpacer(self, size):
        self.real_sizer.AddSpacer(round(size * SCALE))
