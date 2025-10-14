import math
import typing
from dataclasses import dataclass

import wx
from PIL import ImageFont, Image, ImageDraw

from .lib.perf import Counter
from .tool.image_pil2wx import PilImg2WxImg


@dataclass
class TextRenderCache:
    text: str  # 文字
    font: str  # 字体信息NativeFontInfoDesc
    pos_decimal: tuple[float, float]  # 文字位置的小数

    text_bitmap: wx.GraphicsBitmap = None  # 文字渲染结果
    size: tuple[int, int] = None  # 文字图片的大小
    offset_pos: tuple[int, int] = None

    def __hash__(self):
        return hash(hash(self.text) + hash(self.font) + hash(self.pos_decimal))

    def __eq__(self, other):
        if not isinstance(other, TextRenderCache):
            return False
        return hash(self) == hash(other)


class TextCacheManager:
    def __init__(self):
        self.text_cache_cnt = 0
        self.max_text_cache_cnt = 1000
        self.rendered_text_cnt: dict[TextRenderCache, int] = {}
        self.rendered_text_cache: dict[TextRenderCache, TextRenderCache] = {}
        self.clear_timer: wx.Timer | None = None

        # 挂钩get_cache函数从而自动启动清理缓存计时器
        raw_get_cache = self.get_cache

        def get_cache_hook(req_info: TextRenderCache):
            ret = raw_get_cache(req_info)
            if not self.clear_timer:
                app = wx.GetApp()
                self.clear_timer = wx.Timer(app)
                app.Bind(wx.EVT_TIMER, self.clear_unused_cache, self.clear_timer)
                self.clear_timer.Start(1000 * 60)  # 60秒清理一次缓存
                setattr(self, "get_cache", raw_get_cache)
            return ret

        setattr(self, "get_cache", get_cache_hook)

    def get_cache(self, req_info: TextRenderCache):
        """尝试获取文字渲染缓存"""
        if req_info in self.rendered_text_cache:
            self.rendered_text_cnt[req_info] += 1
            return self.rendered_text_cache[req_info]
        return None

    def add_cache(self, info: TextRenderCache):
        """增加文字渲染缓存"""
        if info not in self.rendered_text_cache:
            self.text_cache_cnt += 1
        self.rendered_text_cache[info] = info
        self.rendered_text_cnt[info] = 1

    def remove_cache(self, info: TextRenderCache):
        """删除文字渲染缓存"""
        self.text_cache_cnt -= 1
        del self.rendered_text_cnt[info]
        return self.rendered_text_cache.pop(info)

    def clear_unused_cache(self, *_):
        """清除不常使用的文字渲染缓存, 直到缓存数量小于最大缓存大小的0.8倍"""
        if self.text_cache_cnt < self.max_text_cache_cnt:
            return
        clear_target = self.max_text_cache_cnt * 0.8

        cnt_dict: dict[int, list[TextRenderCache]] = {}
        for info, cnt in self.rendered_text_cnt.items():
            if cnt not in cnt_dict:
                cnt_dict[cnt] = [info]
            else:
                cnt_dict[cnt].append(info)
        cnt_list = list(cnt_dict.items())
        cnt_list.sort(key=lambda x: x[0])
        for cnt, info_list in cnt_list:
            for info in info_list:
                self.remove_cache(info)
                if self.text_cache_cnt < clear_target:
                    return


TheTextCacheManager = TextCacheManager()


class JumpSubClassCheck:
    """
    用于跳过wx.GraphicsContext的不可继承检查, 同时保持自动补全可用
    For jumping wx.GraphicsContext's non sub-classable check, and keep the auto compile usable
    """
    GCType: type[wx.GraphicsContext] = wx.GraphicsContext


JumpSubClassCheck.GCType = typing.cast(type[wx.GraphicsContext], object)


class CustomGraphicsContext(JumpSubClassCheck.GCType):
    """
    GraphicsContext的拓展类
    Extra class of GraphicsContext.
    """
    font_trace_map: dict[int, wx.Font] = {}

    def __init__(self, gc: wx.GraphicsContext):
        if 1 * 1.0 == 0:
            super().__init__()  # Never Called

        self.gc = gc
        self.current_font: wx.Font | None = None
        self.window = gc.GetWindow()
        top_level = gc.GetWindow().GetTopLevelParent()
        if hasattr(top_level, "WindowBlurEnabled") and getattr(top_level, "WindowBlurEnabled"):
            self.enable_transparent_text = True
        else:
            self.enable_transparent_text = False

    # 为日常调用提供重定向
    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self.gc, name)

    def CreateFont(self, font: wx.Font, col: wx.Colour):
        gc_font = self.gc.CreateFont(font, col)
        font.color = col
        self.font_trace_map[id(gc_font)] = font
        return gc_font

    def SetFont(self, font: wx.GraphicsFont):
        if id(font) in self.font_trace_map:
            self.current_font = self.font_trace_map[id(font)]
        else:
            self.current_font = None
        self.gc.SetFont(font)

    def DrawText(self, string: str, x: float, y: float):
        """通过PIL渲染文字实现绘制无黑边的完全透明度文字"""
        if not self.enable_transparent_text:
            self.gc.DrawText(string, x, y)
            return
        info = self.LoadTextRenderInfo(string, x, y)

        if t_info := TheTextCacheManager.get_cache(info):  # 使用已渲染缓存
            bitmap, size = t_info.text_bitmap, t_info.size
            offset_pos = (int(x), int(y))
        else:  # 新增字体渲染缓存
            wx_font = self.current_font if self.current_font else self.window.GetFont()
            bitmap, size = GCRender.RenderTransparentText(self, info, wx_font)
            info.size = size
            info.text_bitmap = bitmap
            TheTextCacheManager.add_cache(info)
            offset_pos = info.offset_pos

        self.gc.DrawBitmap(bitmap, *offset_pos, size[0], size[1])
        # print(len(TheTextCacheManager.rendered_text_cache))

    def LoadTextRenderInfo(self, string: str, x: float, y: float):
        wx_font = self.current_font if self.current_font else self.window.GetFont()
        pos_decimal = (x - int(x), y - int(y))
        return TextRenderCache(string, wx_font.NativeFontInfoDesc, pos_decimal, offset_pos=(int(x), int(y)))


def get_offset(border_width: float):
    if border_width == 1.0:
        return 0
    return border_width / 2


def ARC(angle: float):
    return math.pi * 2 * ((angle % 360) / 360)


class GCRender:
    @staticmethod
    def RenderTransparentText(gc: CustomGraphicsContext, info: TextRenderCache, wx_font: wx.Font) -> \
            tuple[wx.GraphicsBitmap, tuple[int, int]]:
        window = gc.GetWindow()
        font = ImageFont.truetype("C:\Windows\Fonts\msyh.ttc", wx_font.GetPointSize() // 0.75)

        # 获取文字大小
        sm_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        left, top, right, bottom = sm_draw.multiline_textbbox((0, 0), info.text, font=font)
        if left == top == right == bottom == 0:
            return gc.CreateBitmapFromImage(wx.Image(1, 1)), (1, 1)

        # 绘制文字
        image = Image.new("RGBA", typing.cast(tuple[int, int], (right - left, bottom)))
        draw = ImageDraw.Draw(image)
        color = wx_font.color.Get(True) if hasattr(wx_font, "color") else window.GetForegroundColour().Get(True)
        draw.multiline_text((-left + info.pos_decimal[0], 0 + info.pos_decimal[1]),
                            info.text, fill=color, font=font, spacing=2)

        # 转化并返回
        wx_image = PilImg2WxImg(image)
        return (
            gc.CreateBitmapFromImage(wx_image),
            typing.cast(tuple[int, int], wx_image.GetSize().Get())
        )

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
