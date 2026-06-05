from dataclasses import dataclass


class ElementStyle:
    pass


@dataclass
class RectElementStyle(ElementStyle):
    width: float = 0
    height: float = 0
    round: float = 0


@dataclass
class TextElementStyle(ElementStyle):
    text: str = ""


ELEMENT_STYLE_MAP = {
    "text": TextElementStyle,
    "rect": RectElementStyle
}
