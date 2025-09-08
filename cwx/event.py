import wx


class PyCommandEvent(wx.PyCommandEvent, wx.CommandEvent, wx.Event):
    """填补了types-wxpython中所缺失的子类"""
    def __init__(self, eventType, evt_id=wx.ID_ANY):
        super().__init__(eventType, evt_id)
