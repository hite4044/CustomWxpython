from enum import Flag, Enum

import wx


class ComfortFlag(Flag):
    @classmethod
    def format(cls, value: str | int | Flag):
        if isinstance(value, str):
            value = value.lower()
            result = 0
            for name in cls.__members__:
                if value.startswith(name.lower()) or value.endswith(name.lower()):
                    result |= cls.__members__[name].value
            return cls(result)
        elif isinstance(value, int):
            return cls(value)
        elif isinstance(value, Flag):
            return value


class CenterAlign(ComfortFlag):
    """定义文本放置的中心位置"""
    TOP = wx.TOP
    BOTTOM = wx.BOTTOM
    LEFT = wx.LEFT
    RIGHT = wx.RIGHT
    CENTER = wx.CENTRE


class ComfortEnum(Enum):
    @classmethod
    def format(cls, value: str | int | Enum):
        if isinstance(value, str):
            value = value.lower()
            for name in cls.__members__:
                if name.lower() == value:
                    return cls.__members__[name].value
            raise ValueError(f"Invalid TextWarp value: {value}")
        elif isinstance(value, int):
            return cls(value)
        elif isinstance(value, Enum):
            return value


class TextAlign(ComfortEnum):
    """文本的对齐方式"""
    LEFT = wx.ALIGN_LEFT
    CENTER = wx.ALIGN_CENTER
    RIGHT = wx.ALIGN_RIGHT


class TextWarp(ComfortEnum):
    """文本的换行方式"""
    WORD = 0
    CHAR = 1
    WORD_CHAR = 2



if __name__ == '__main__':
    print(CenterAlign.format("topleft"))
