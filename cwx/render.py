import math
import typing

import wx
from PIL import ImageFont, Image, ImageDraw

from .lib.perf import Counter
from .tool.image_pil2wx import PilImg2WxImg

rendered_texts: dict[str, tuple[wx.GraphicsBitmap, tuple[int, int]]] = {}


class GraphicsContextWarper:
    """一个GraphicsContext的拓展类, 用于实现对某些方法进行渲染逻辑覆盖"""
    def __init__(self, gc: wx.GraphicsContext):
        self.gc = gc
        self.window = gc.GetWindow()
        self.raw_func_stack = []

    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self.gc, name)

    def DrawText(self, string: str, x: float, y: float):
        """通过PIL渲染文字实现绘制无黑边的完全透明度文字"""
        wx_font = self.window.GetFont()
        render_key = string + wx_font.GetFaceName() + str(wx_font.GetPixelSize()[1])

        if not string:
            return
        if render_key in rendered_texts:
            bitmap, size = rendered_texts[render_key]
            self.gc.DrawBitmap(bitmap, x, y, size[0], size[1])
            return

        window = typing.cast(typing.Any, self.gc.GetWindow())
        bitmap, size = self.render_text(window, string)
        self.gc.DrawBitmap(bitmap, x, y, size[0], size[1])
        rendered_texts[render_key] = (bitmap, size)

    def render_text(self, window, string: str) -> tuple[wx.GraphicsBitmap, tuple[int, int]]:
        timer = Counter(create_start=True)
        wx_font = window.GetFont()
        font = ImageFont.truetype("C:\Windows\Fonts\msyh.ttc", wx_font.GetPixelSize().GetHeight())
        left, top, right, bottom = font.getbbox(string)
        image = Image.new("RGBA", typing.cast(tuple[int, int], (right - left, bottom)))
        draw = ImageDraw.Draw(image)
        draw.text((-left, 0), string, fill=window.style.fg.Get(includeAlpha=True), font=font)

        wx_image = PilImg2WxImg(image)
        print(self.gc.GetWindow().__class__.__name__, timer.endT())
        return self.gc.CreateBitmap(wx_image.ConvertToBitmap()), typing.cast(tuple[int, int], wx_image.GetSize().Get())


def get_offset(border_width: float):
    if border_width == 1.0:
        return 0
    elif 1.5 < border_width % 2.0 < 2.0 or 0.0 < border_width % 2.0 < 0.5:
        return border_width / 2
    return border_width // 2


def ARC(angle: float):
    return math.pi * 2 * ((angle % 360) / 360)


class GCRender:
    @staticmethod
    def RenderBorder(gc: wx.GraphicsContext, border_width: float, corner_radius: float):
        """
        渲染一个紧密贴合控件外部的边框
        Render a perfect border
        """
        w, h = gc.GetSize()
        path = gc.CreatePath()
        offset = get_offset(border_width)
        dn_offset = border_width - offset
        pad = offset + corner_radius
        dn_pad = dn_offset + corner_radius
        radius = corner_radius

        path.AddArc(pad, pad, radius, ARC(270), ARC(180), 0)
        # path.AddLineToPoint(offset, h - pad)
        path.AddArc(pad, h - dn_pad, radius, ARC(180), ARC(90), 0)
        # path.AddLineToPoint(w - pad, h - dn_offset)
        path.AddArc(w - dn_pad, h - dn_pad, radius, ARC(90), ARC(0), 0)
        # path.AddLineToPoint(w - dn_offset, pad)
        path.AddArc(w - dn_pad, pad, radius, ARC(0), ARC(270), 0)
        path.AddLineToPoint(pad, offset)

        gc.DrawPath(path)

        return offset, dn_offset
