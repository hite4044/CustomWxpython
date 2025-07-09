import cwx
import wx

class HT_Scanner(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="HT Scanner")


if __name__ == "__main__":
    app = wx.App()
    frame = HT_Scanner(None)
    frame.Show()
    app.MainLoop()