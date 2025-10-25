import wx


class PyCommandEvent(wx.PyCommandEvent, wx.CommandEvent, wx.Event):
    """填补了types-wxpython中所缺失的子类"""

    def __init__(self, eventType, evt_id=wx.ID_ANY):
        wx.PyCommandEvent.__init__(self, eventType, evt_id)


class SimpleCommandEvent(PyCommandEvent):
    """一个简单的命令事件"""
    eventType: int = wx.NewEventType()

    def __init__(self, window: wx.Window):
        super().__init__(self.eventType, window.GetId())
        self.SetEventObject(window)
