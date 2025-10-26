import wx

import cwx
from cwx.style import TopLevelStyle
from cwx.lib.flag_parser import parse_flag
from cwx.lib.sizer import PaddedBoxSizer
from cwx.widgets.frame import Dialog


class MessageDialog(Dialog):
    def __init__(self, parent: wx.Window | None, message: str, caption: str = "Title",
                 style: int = wx.OK | wx.CENTRE, pos=wx.DefaultPosition,
                 widget_style: TopLevelStyle | None = None):
        super().__init__(parent, title=caption, pos=pos, style=wx.CAPTION, widget_style=widget_style)

        self.icon_type = parse_flag(style, wx.ICON_INFORMATION, wx.ICON_WARNING, wx.ICON_ERROR, wx.ICON_QUESTION, default=wx.ICON_INFORMATION)
        self.btn_type = parse_flag(style, wx.OK, wx.OK | wx.CANCEL, wx.YES_NO, default=wx.OK)

        self.context = cwx.StaticText(self, label=message)
        self.buttons = []

        with PaddedBoxSizer(wx.VERTICAL) as sizer:
            with PaddedBoxSizer(wx.HORIZONTAL, padx=16, pady=16) as content_stack:
                content_stack.Add(self.context, 1, wx.EXPAND)
            sizer.Add(content_stack, 1, wx.EXPAND)

            sizer.Add(cwx.StaticLine(self), 0, wx.EXPAND)

            self.ok_btn: cwx.Button | None = None
            self.yes_btn: cwx.Button | None = None
            self.no_btn: cwx.Button | None = None
            self.cancel_btn: cwx.Button | None = None
            with PaddedBoxSizer(wx.HORIZONTAL, padx=12, pady=16) as btn_stack:
                btn_stack.AddStretchSpacer()
                if self.btn_type == wx.OK:
                    self.ok_btn = cwx.Button(self, "确定").SetId(wx.ID_OK)
                    buttons = [self.ok_btn]
                elif self.btn_type == wx.OK | wx.CANCEL:
                    self.ok_btn = cwx.Button(self, "确定").SetId(wx.ID_OK)
                    self.cancel_btn = cwx.Button(self, "取消").SetId(wx.ID_CANCEL)
                    buttons = [self.ok_btn, self.cancel_btn]
                elif self.btn_type == wx.YES_NO:
                    self.yes_btn = cwx.Button(self, "是").SetId(wx.ID_YES)
                    self.no_btn = cwx.Button(self, "否").SetId(wx.ID_NO)
                    buttons = [self.yes_btn, self.no_btn]
                elif self.btn_type == wx.YES_NO | wx.CANCEL:
                    self.yes_btn = cwx.Button(self, "是").SetId(wx.ID_YES)
                    self.no_btn = cwx.Button(self, "否").SetId(wx.ID_NO)
                    self.cancel_btn = cwx.Button(self, "取消").SetId(wx.ID_CANCEL)
                    buttons = [self.yes_btn, self.no_btn, self.cancel_btn]
                else:
                    raise ValueError("Invalid button type")
                for i, btn in enumerate(buttons):
                    if i != 0:
                        btn_stack.AddSpacer(8)
                    btn_stack.Add(btn, 0, wx.EXPAND)
            sizer.Add(btn_stack, 0, wx.EXPAND)

        self.SetMinClientSize((350, -1))
        self.SetSizer(sizer)
        self.Fit()

        self.Bind(cwx.EVT_BUTTON, self.on_button)

    def on_button(self, event: wx.Event):
        self.EndModal(event.GetId())

    def __del__(self):
        self.Destroy()

    # 传统绑定
    def SetOKCancelLabels(self, ok: str, cancel: str):
        self._SetBtnLabel(self.ok_btn, ok)
        self._SetBtnLabel(self.cancel_btn, cancel)

    def SetOKLabel(self, ok: str):
        self._SetBtnLabel(self.ok_btn, ok)

    def SetYesNoCancelLabels(self, yes: str, no: str, cancel: str):
        self._SetBtnLabel(self.yes_btn, yes)
        self._SetBtnLabel(self.no_btn, no)
        self._SetBtnLabel(self.cancel_btn, cancel)

    def SetYesNoLabels(self, yes: str, no: str):
        self._SetBtnLabel(self.yes_btn, yes)
        self._SetBtnLabel(self.no_btn, no)

    @staticmethod
    def _SetBtnLabel(btn: wx.Button | None, label: str):
        if btn is None:
            return
        btn.SetLabel(label)



if __name__ == '__main__':
    app = wx.App()
    dlg = MessageDialog(None, "Hello World", "你好", style=wx.CENTRE | wx.OK | wx.CANCEL)
    print(dlg.ShowModal())