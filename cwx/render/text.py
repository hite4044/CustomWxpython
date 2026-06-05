import cairocffi as cairo
import pangocairocffi as pangocairo
import pangocffi as pango
import wx


class GenericFont:
    """Define all font information for the text rendering."""
    face_name: str = "微软雅黑"
    size: float = 12.0
    weight: int = 500
    italic: bool = False
    underline: bool = False

    def __hash__(self):
        return hash((self.face_name, self.size, self.weight, self.italic, self.underline))


class TextRenderInfo:
    """Define all information which is used to the text rendering."""
    text: str
    use_html: bool | None
    font: GenericFont
    color: wx.Colour
    spacing: float
    align: wx.Alignment
    width: float
    height: float

    __align_map = {
        wx.ALIGN_LEFT: pango.Alignment.LEFT,
        wx.ALIGN_CENTER: pango.Alignment.CENTER,
        wx.ALIGN_CENTRE: pango.Alignment.CENTER,
        wx.ALIGN_RIGHT: pango.Alignment.RIGHT,
    }

    def __hash__(self):
        return hash((self.text, self.font, self.color))

    @property
    def pango_align(self) -> pango.Alignment:
        """Translate wxpython's align class into pango's align class."""
        try:
            return self.__align_map[self.align]
        except KeyError:
            raise ValueError("Invalid text align, it must be wx.ALIGN_LEFT, wx.ALIGN_CENTER(wx.ALIGN_CENTRE) "
                             f"or wx.ALIGN_RIGHT, but current align is {self.align}.")


class TextRenderResult:
    bitmap: bytes
    size: tuple[int, int]


def create_empty_context() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def translate_to_layout(info: TextRenderInfo, context: cairo.Context = None) -> pango.Layout:
    if context is None:
        context = create_empty_context()
    layout = pangocairo.create_layout(context)
    layout.alignment = info.pango_align
    if info.use_html is False:
        layout.apply_markup(info.text.replace("<", "&lt;").replace(">", "&gt;"))
    else:
        layout.apply_markup(info.text)
    layout.spacing = info.spacing
    return layout


def render_text(info: TextRenderInfo) -> TextRenderResult:
    extent_layout = translate_to_layout(info)
    WIDTH = HEIGHT = extent_layout.get_size()

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    context = cairo.Context(surface)
    context.translate(0, HEIGHT / 2)

    # Build the layout
    layout = pangocairo.create_layout(context)
    layout.width = pango.units_from_double(WIDTH)
    layout.alignment = pango.Alignment.CENTER
    layout.apply_markup('<span font="italic 30">Fuck Wxpython Back Render</span>')
    layout.get_extents()

    # Render the layout
    pangocairo.show_layout(context, layout)
    pangocairo.
