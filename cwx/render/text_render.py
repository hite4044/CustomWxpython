from collections import namedtuple
from dataclasses import dataclass
from io import BytesIO
from math import ceil
from typing import Union

from PIL import Image, ImageEnhance, ImageDraw

from cwx.lib.perf import Counter
from cwx.tool.image_pil2wx import PilImg2WxImg

timer = Counter()
timer.start()
import cairocffi
import pangocffi
import pangocairocffi
from pangocffi import WrapMode

print("渲染库初始化耗时", timer.endT())

from cwx.render.constants import *

P_SCALE = 1024


@dataclass
class TextAttr:
    font_family: str = "sans"
    font_size: int = 9

    italic: bool = False
    weight: int = 400
    underline: bool = False

    strike: bool = False
    strike_style: str = "solid"
    strike_color: wx.Colour = wx.BLACK

    spacing: int = 0
    line_spacing: int = 0

    @classmethod
    def from_wx_font(cls, data: wx.Font):
        new = cls()
        new.font_family = data.GetFaceName()
        new.font_size = data.GetPointSize()
        new.weight = data.GetWeight()
        new.italic = wx.FONTSTYLE_ITALIC == data.GetStyle()
        new.underline = data.GetUnderlined()
        return new

    def update_value(self, old: 'TextAttr'):
        """迁移old的属性至自身"""
        for name in getattr(old, "__dataclass_fields__").keys():
            value = getattr(old, name)
            if isinstance(value, wx.Colour):
                value = wx.Colour(value.Get())
            setattr(self, name, value)

    def merge(self, extra: 'TextAttr'):
        """迁移extra被修改的属性至自身"""
        for name in getattr(extra, "__dataclass_fields__").keys():
            value = getattr(extra, name)
            if value != getattr(DEFAULT_TEXT_ATTR, name):
                setattr(self, name, value)

    def __hash__(self):
        value_dict = self.__dict__.copy()
        value_dict.pop("strike_color")
        return hash(str(value_dict) + str(self.strike_color.Get()))


"""Reserved for internal use. You shouldn't modify it."""
DEFAULT_TEXT_ATTR = TextAttr()


@dataclass
class TextParagraph(TextAttr):
    text: str = ""

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def as_html(self) -> str:
        return f'<span font="Microsoft YaHei UI">{self.text}</span>'

    def __hash__(self):
        return hash(super().__hash__() + hash(self.text))


class AdvancedText:
    def __init__(self, border: tuple[int, int] | None = None, warp: TextWarp | str = TextWarp.WORD,
                 align: Union[TextAlign, str] = TextAlign.LEFT,
                 text: str | None = None, global_attr: TextAttr | None = None, paragraphs: list[TextParagraph] = None,
                 html_text: str | None = None):
        if paragraphs is None:
            paragraphs = []
        self.border: tuple[int, int] | None = border
        self.warp: TextWarp = TextWarp.format(warp)
        self.align: TextAlign = TextAlign.format(align)

        self.text: str | None = text
        self.global_attr: TextAttr = global_attr if global_attr else TextAttr()
        self.paragraphs: list[TextParagraph] = paragraphs
        self.html_text: str | None = html_text

    def as_html(self) -> str:
        if self.html_text is not None:
            return self.html_text
        if self.text is not None:
            para = TextParagraph(self.text)
            if self.global_attr:
                para.update_value(self.global_attr)
            return para.as_html()
        return "".join([p.as_html() for p in self.paragraphs])

    def __hash__(self):
        rst = hash(str([self.border, self.warp, self.text, self.html_text]))
        rst += hash(self.global_attr)
        for p in self.paragraphs:
            rst += hash(p)
        return hash(rst)


"""A rect with a format of (x, y, width, height)"""
SimpleRect = namedtuple("SimpleRect", ["x", "y", "width", "height"])


@dataclass
class TextBitmap:
    bitmap: wx.GraphicsBitmap
    size: tuple[int, int]
    logical_rect: SimpleRect
    ink_rect: SimpleRect


class TextRender:
    """Text Render of CustomWxpython"""
    MAX_CACHE_SIZE = 1000
    FONT_CACHE: dict[int, TextBitmap] = {}

    enable_text_enhance = True
    enhance_factor = 0.25

    @classmethod
    def create_layout_by_context(cls, context: cairocffi.Context, text: AdvancedText):
        """
        根据text定义的文字属性创建pangocairo布局
        :param context: 用于创建布局的cairo上下文
        :param text: 文字
        """
        # 创建布局
        layout = pangocairocffi.create_layout(context)
        layout.wrap = getattr(WrapMode, text.warp.name)
        layout.width = text.border[0] * 1024 if text.border else -1
        layout.height = text.border[1] * 1024 if text.border else -1
        layout.alignment = getattr(pangocffi.Alignment, text.align.name)
        layout.apply_markup(text.as_html())
        return layout

    @classmethod
    def create_test_layout(cls, text: AdvancedText):
        """创建用于获取布局信息的pangocairo布局. 所有数据需要经过除以P_SCALE并乘以SCALE可得真实像素数"""
        bbox_surface = cairocffi.ImageSurface(cairocffi.FORMAT_A8, 1, 1)
        context = cairocffi.Context(bbox_surface)

        return cls.create_layout_by_context(context, text)

    @classmethod
    def get_text_bbox(cls, text: AdvancedText) -> tuple[SimpleRect, SimpleRect]:
        """获取文字的逻辑边界框与渲染边界框, 格式为(x, y, width, height). 未经过dpi换算"""
        layout = cls.create_test_layout(text)

        log_r, ink_r = layout.get_extents()
        return (SimpleRect(log_r.x / P_SCALE, log_r.y / P_SCALE, log_r.width / P_SCALE, log_r.height / P_SCALE),
                SimpleRect(ink_r.x / P_SCALE, ink_r.y / P_SCALE, ink_r.width / P_SCALE, ink_r.height / P_SCALE))

    @classmethod
    def get_partial_text_extents(cls, text: AdvancedText) -> list[float]:
        """获取每个字符的渲染x"""
        layout = cls.create_test_layout(text)
        layout_iter = layout.get_iter()
        result = []
        while True:
            result.append(layout_iter.get_char_extents().x / P_SCALE)
            if not layout_iter.next_char():
                break
        result.append(layout_iter.get_char_extents().x / P_SCALE)
        result.pop(0)
        return result

    @classmethod
    def render(cls, gc: wx.GraphicsContext, text: AdvancedText, color: wx.Colour,
               render_scale: float = 1) -> TextBitmap:
        # 测试缓存
        text_hash = hash(text) + hash(color.Get())
        if text_hash in TextRender.FONT_CACHE:
            return TextRender.FONT_CACHE[text_hash]

        logical_rect, ink_rect = TextRender.get_text_bbox(text)

        width = max(ceil(ink_rect.width * render_scale), 1)
        height = max(ceil(ink_rect.height * render_scale), 1)

        canvas = cairocffi.ImageSurface(cairocffi.FORMAT_A8, width, height)
        context = cairocffi.Context(canvas)
        context.transform(cairocffi.Matrix(render_scale, 0, 0, render_scale, 0, 0))

        # 设置文本颜色
        context.set_source_rgba(
            1.0, 1.0, 1.0,
            color.Alpha() / 255.0 if color.Alpha() else 1.0
        )

        # 创建布局
        layout = cls.create_layout_by_context(context, text)

        # 渲染文字
        context.move_to(-ink_rect.x // 1024, -ink_rect.y // 1024)
        pangocairocffi.show_layout(context, layout)
        canvas.flush()

        # 提取并增强文字单色图
        # timer = Counter().start()
        alpha_png = BytesIO()
        canvas.write_to_png(alpha_png)
        alpha_image = Image.open(alpha_png)
        if TextRender.enable_text_enhance:
            alpha_image = ImageEnhance.Brightness(alpha_image).enhance(1 + TextRender.enhance_factor)

        # 合成alpha图片
        image = Image.new("RGBA", (width, height), (color.Red(), color.Green(), color.Blue(), 255))
        image.putalpha(alpha_image)
        # draw = ImageDraw.Draw(image)
        # draw.rectangle((0, 0, width - 1, height - 1), None, outline=(255, 0, 0, 255))

        graphics_bitmap = gc.CreateBitmap(PilImg2WxImg(image).ConvertToBitmap())
        # print(timer.endT())
        canvas.finish()

        # 缓存
        result = TextBitmap(
            bitmap=graphics_bitmap,
            size=(width, height),
            logical_rect=logical_rect,
            ink_rect=ink_rect
        )
        if len(TextRender.FONT_CACHE) >= TextRender.MAX_CACHE_SIZE:
            # 移除最旧的缓存项
            oldest_key = next(iter(TextRender.FONT_CACHE))
            del TextRender.FONT_CACHE[oldest_key]

        TextRender.FONT_CACHE[text_hash] = result

        return result


if __name__ == "__main__":
    t = TextParagraph("114514")
    t.italic = True
    print(t.__dict__)
