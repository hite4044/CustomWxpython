import wx


def set_multi_size_icon(toplevel: wx.TopLevelWindow, path: str):
    icons = wx.IconBundle()
    sizes = [16, 24, 32, 48, 64]
    raw = wx.Image()
    raw.LoadFile(path)
    for size in sizes:
        scaled = raw.Copy()
        scaled = scaled.Rescale(size, size, wx.IMAGE_QUALITY_HIGH)
        print(scaled.GetSize())
        icons.AddIcon(wx.Icon(scaled.ConvertToBitmap()))
    icons.AddIcon(wx.Icon(raw.ConvertToBitmap()))
    toplevel.SetIcons(icons)
