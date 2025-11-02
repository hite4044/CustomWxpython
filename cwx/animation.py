"""
CustomWxpython 的动画库, 提供诸多动画
Animation library of CustomWxpython, provide some animation.
"""
from bisect import bisect_left
from dataclasses import dataclass
from enum import Enum
from time import perf_counter

import wx

Num = int | float


class Animation:
    """一个动画, """

    def __init__(self, during: float):
        self.during = during  # 持续时间
        self.is_invent = False  # 是否为倒放
        self.has_finish = False  # 动画是否结束

        self.playing_start = -1  # 动画开始时间

    def set_invent(self, invent: bool):
        self.is_invent = invent

    def play(self):
        """播放动画, 并切换至动画的开头"""
        self.playing_start = perf_counter()
        self.has_finish = False

    def stop(self):
        """停止动画, 并切换至动画的结尾"""
        self.playing_start = -1
        self.has_finish = True

    @property
    def is_playing(self) -> bool:
        """是否正在播放动画"""
        return self.playing_start != -1 and not self.has_finish

    @property
    def raw_percent(self):
        """播放中, 获取当前动画播放的百分比"""
        return (perf_counter() - self.playing_start) / self.during

    @property
    def value(self) -> float:
        """动画的值"""
        if self.is_playing:
            percent = self.raw_percent
            if not self.has_finish and percent > 1:
                self.has_finish = True
                percent = 1
            else:
                percent = min(percent, 1)
        elif self.has_finish:
            percent = 1
        else:
            percent = 0
        return self.raw_get_value(percent)

    def get_next_frame_time(self, fps: float):
        return 1 / fps

    @property
    def int_value(self) -> int:
        return int(self.value)

    def raw_get_value(self, percent: float) -> float:
        return percent


class BlinkAnimation(Animation):
    def __init__(self, range_: tuple[Num, Num], threshold: float):
        super().__init__(0)
        self.range = range_
        self.threshold = threshold

    def raw_get_value(self, percent: float) -> Num:
        return self.range[1] if percent > self.threshold else self.range[0]


class KeyFrameCurves(Enum):
    """动画曲线, 用于KeyFrame(动画关键帧)"""
    BLINK = 0
    "突然闪现"

    SMOOTH = 1
    "平滑匀速运动"

    EASE_IN = 2
    "缓入"
    QUADRATIC_EASE_IN = 3
    "二次方缓入"
    CUBE_EASE_IN = 4
    "三次方缓入"

    EASE_OUT = 5
    "缓出"
    QUADRATIC_EASE_OUT = 6
    "二次方缓出"
    CUBE_EASE_OUT = 7
    "三次方缓出"

    QUADRATIC_EASE = 8
    "二次方缓动"
    CUBE_EASE = 9
    "三次方缓动"


@dataclass
class KeyFrame:
    """动画关键帧"""
    way: KeyFrameCurves  # 动画曲线
    percent: float  # 动画百分比
    data: float  # 指定百分比的数据值


class KeyFrameAnimation(Animation):
    def __init__(self, during: float, key_frames: list[KeyFrame]):
        super().__init__(during)
        self.percents: list[float] = sorted((key_frame.percent for key_frame in key_frames))
        self.key_frames: list[KeyFrame] = sorted((key_frame for key_frame in key_frames), key=lambda x: x.percent)
        if 0 not in self.percents:
            self.key_frames.insert(0, KeyFrame(KeyFrameCurves.BLINK, 0, self.key_frames[0].data))
            self.percents.insert(0, 0)
        if 1 not in self.percents:
            self.key_frames.append(KeyFrame(KeyFrameCurves.BLINK, 1, self.key_frames[-1].data))
            self.percents.append(1)

        self.raw_range = (self.key_frames[0].data, self.key_frames[-1].data)
        self.percent_offset = 0
        self.raw_during = float(self.during)

    def play(self):
        super().play()
        # print(f"Playing Animation: During: {self.during}, percent_offset: {self.percent_offset}")

    def get_next_frame_time(self, fps: float):
        frame_time = 1 / fps
        crt_time = perf_counter()
        if crt_time + frame_time > self.playing_start + self.during:
            return self.playing_start + self.during - crt_time
        return frame_time

    def raw_get_value(self, percent: float) -> float:
        if self.is_invent:
            percent = 1 - percent
        percent = min(max(percent * (1 - self.percent_offset), 0), 1)
        index = bisect_left(self.percents, percent) - 1
        frame = self.key_frames[index]

        start = frame.data

        if index >= len(self.percents) - 1:
            size = 0
            local_percent = 1
        else:
            next_frame = self.key_frames[index + 1]
            size = next_frame.data - frame.data
            local_percent = (percent - frame.percent) / (next_frame.percent - frame.percent)

        match frame.way:
            case KeyFrameCurves.BLINK:
                return start
            case KeyFrameCurves.SMOOTH:
                return start + size * local_percent
            case KeyFrameCurves.QUADRATIC_EASE:
                if local_percent < 0.5:
                    eased = 2 * (local_percent ** 2)
                else:
                    eased = -1 + 4 * local_percent - 2 * (local_percent ** 2)
                return start + size * eased
            case KeyFrameCurves.CUBE_EASE:
                if local_percent < 0.5:
                    eased = 4 * (local_percent ** 3)
                else:
                    eased = 1 - ((-2 * local_percent + 2) ** 3) / 2
                return start + size * eased
            case KeyFrameCurves.QUADRATIC_EASE_IN:
                return start + size * (local_percent ** 2)
            case KeyFrameCurves.CUBE_EASE_IN:
                return start + size * (local_percent ** 3)
            case KeyFrameCurves.QUADRATIC_EASE_OUT:
                return start + size * (1 - (1 - local_percent) ** 2)
            case KeyFrameCurves.CUBE_EASE_OUT:
                return start + size * (1 - (1 - local_percent) ** 3)
        raise NotImplementedError()

    def set_invent(self, invent: bool):
        super().set_invent(invent)
        if not self.is_playing:
            return

        raw_percent = (perf_counter() - self.playing_start) / self.raw_during
        self.percent_offset = 1 - raw_percent
        if invent:
            self.during = self.raw_during * raw_percent
        else:
            self.during = self.raw_during * (1 - raw_percent)
        self.playing_start = perf_counter()
        # print(f"Set Animation Invent {invent}: percent: {raw_percent},\n during: {self.during},\n percent_offset: {self.percent_offset}")

    def stop(self):
        self.during = float(self.raw_during)
        self.percent_offset = 0
        super().stop()


class EZKeyFrameAnimation(KeyFrameAnimation):
    def __init__(self, during: float, way: KeyFrameCurves, start: float, end: float):
        super().__init__(during, [KeyFrame(way, 0, 0.0), KeyFrame(way, 1, 1.0)])
        self.start = start
        self.end = end

    def set_range(self, start: float, end: float):
        self.start = start
        self.end = end

    @property
    def value(self) -> float:
        return super().value * (self.end - self.start) + self.start


import colorsys


class ColorGradientAnimation(KeyFrameAnimation):
    DEFAULT_FRAMES = [
        KeyFrame(KeyFrameCurves.SMOOTH, 0, 0),
        KeyFrame(KeyFrameCurves.SMOOTH, 1, 1)
    ]

    @staticmethod
    def rgb_to_hsl(color: wx.Colour):
        # 归一化到[0,1]
        r_norm, g_norm, b_norm = color.GetRed() / 255.0, color.GetGreen() / 255.0, color.GetBlue() / 255.0
        # colorsys使用0-1范围的H，需要转换为0-360
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        return h, s, l  # 转换为标准的HSL表示

    @staticmethod
    def hsl_to_rgb(h, s, l):
        """使用color sys将浮点HSL转换为整数RGB"""
        # 将H从0-360转换为0-1
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))

    def __init__(self, during: float, color1: wx.Colour, color2: wx.Colour, key_frames=None):
        if key_frames is None:
            key_frames = self.DEFAULT_FRAMES
        super().__init__(during, key_frames)
        self.color1 = color1
        self.color2 = color2

    def set_color(self, color1: wx.Colour, color2: wx.Colour):
        self.color1 = color1
        self.color2 = color2

    @staticmethod
    def mix_color(color1: wx.Colour, color2: wx.Colour, percent: float):
        hsl1 = ColorGradientAnimation.rgb_to_hsl(color1)
        hsl2 = ColorGradientAnimation.rgb_to_hsl(color2)
        new_hsl = (
            hsl1[0] * (1 - percent) + hsl2[0] * percent,
            hsl1[1] * (1 - percent) + hsl2[1] * percent,
            hsl1[2] * (1 - percent) + hsl2[2] * percent
        )
        new_rgb = ColorGradientAnimation.hsl_to_rgb(*new_hsl)
        return wx.Colour(*new_rgb, int(color1.Alpha() * (1 - percent) + color2.Alpha() * percent))

    @property
    def value(self) -> wx.Colour:
        percent = super().value
        return self.mix_color(self.color1, self.color2, percent)


class MultiColorGradientAnimation(Animation):
    """多颜色渐变动画, 通过set_target设置目标颜色, 这个类会自动处理渐变关系"""

    def __init__(self, during: float, *colors: tuple[str, wx.Colour]):
        super().__init__(during)
        self.colors: dict[str, wx.Colour] = dict(colors)
        self.current_name: str = colors[0][0]
        self.current_color: wx.Colour = self.colors[self.current_name]
        self.start_color: wx.Colour = self.current_color
        self.last_color: wx.Colour = self.current_color

    def set_default_target(self, name: str):
        self.current_name = name
        self.current_color = self.colors[name]

    def set_target(self, name: str, invent: bool = False):
        """设置目标颜色, 颜色将会从当前颜色渐变至"""
        self.set_invent(invent)
        self.start_color = self.last_color
        self.current_name = name
        self.current_color = self.colors[name]

    def __getitem__(self, name: str):
        return self.colors[name]

    def __setitem__(self, key: str, value: wx.Colour):
        self.colors[key] = value

    @property
    def value(self) -> wx.Colour:
        percent = super().value
        self.last_color = ColorGradientAnimation.mix_color(self.start_color, self.current_color, percent)
        return self.last_color


class MultiKeyFrameAnimation(Animation):
    def __init__(self, animations: dict[str, KeyFrameAnimation]):
        super().__init__(1.0)
        self.animations = animations
        self.playing_name: str | None = None
        self.playing_anim: KeyFrameAnimation | None = None

    @property
    def is_playing(self) -> bool:
        if self.playing_anim is None:
            return False
        return self.playing_anim.is_playing

    def get_next_frame_time(self, fps: float):
        return self.playing_anim.get_next_frame_time(fps)

    def set_invent(self, invent: bool):
        super().set_invent(invent)
        self.playing_anim.set_invent(invent)

    def set_sub_anim(self, name: str):
        if self.playing_anim != self.animations[name]:
            for anim in self.animations.values():
                anim.stop()
        self.playing_name = name
        self.playing_anim = self.animations[name]

    def play(self):
        return self.playing_anim.play()

    def stop(self):
        return self.playing_anim.stop()

    @property
    def value(self) -> float | wx.Colour:
        return self.playing_anim.value

    def __getitem__(self, item: str) -> KeyFrameAnimation:
        return self.animations[item]


class AnimationGroup(Animation):
    """动画组"""

    def __init__(self, group: dict[str, Animation]):
        super().__init__(1.0)
        self.animations = group

    def play(self):
        for animation in self.animations.values():
            animation.play()
        self.during = max(animation.during for animation in self.animations.values())
        super().play()

    def stop(self):
        for animation in self.animations.values():
            animation.stop()
        super().stop()

    def set_invent(self, invent: bool):
        for animation in self.animations.values():
            animation.is_invent = invent
        super().set_invent(invent)

    @property
    def is_playing(self) -> bool:
        return any(animation.is_playing for animation in self.animations.values())

    @property
    def value(self) -> object:
        raise NotImplementedError


def MAKE_ANIM_FRAMES(way: KeyFrameCurves):
    """
    以指定的动画曲线创建一个从0~1的关键帧列表

    """
    return [
        KeyFrame(way, 0, 0.0),
        KeyFrame(way, 1, 1.0)
    ]


def MAKE_ANIMATION(during: float, way: KeyFrameCurves = KeyFrameCurves.SMOOTH):
    return KeyFrameAnimation(during, MAKE_ANIM_FRAMES(way))
