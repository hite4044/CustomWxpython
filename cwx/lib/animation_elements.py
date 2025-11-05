import wx

from ..animation import Animation
from ..render import CustomGraphicsContext


class AnimationElement:
    CGC = CustomGraphicsContext  # 只是为了保持引用
    def draw(self, gc: 'CustomGraphicsContext'):
        pass


class DrawCallAE(AnimationElement):
    def __init__(self, func_name: str, *args):
        super().__init__()
        self.func_name = func_name
        self.args = args

    def draw(self, gc: 'CustomGraphicsContext'):
        func = getattr(gc, self.func_name)
        args = ((arg.value if isinstance(arg, Animation) else arg) for arg in self.args)
        func(*args)


class DrawLinesAE(AnimationElement):
    def __init__(self, anim: Animation, point2Ds: list[wx.Point2D] = None,
                 fill_style: wx.PolygonFillMode = wx.ODDEVEN_RULE):
        super().__init__()
        self.anim = anim
        self.point2Ds: list[wx.Point2D] = point2Ds
        self.fill_style = fill_style

    def draw(self, gc: 'CustomGraphicsContext'):
        if self.point2Ds is None:
            return

        value = self.anim.value
        if value == 0:
            return
        if value == 1:
            gc.DrawLines(self.point2Ds, self.fill_style)
            return

        point2Ds = self.point2Ds
        active_points = [point2Ds[0]]
        distances = [point2Ds[i].GetDistance(point2Ds[i + 1]) for i in range(len(point2Ds) - 1)]
        total_distance = sum(distances)
        left_distance = total_distance * min(max(value, 0), 1)
        distance = 0
        for i, distance in enumerate(distances):
            active_points.append(point2Ds[i + 1])
            if left_distance <= distance:
                break
            left_distance -= distance
        if left_distance != 0:
            last_second_pt = wx.Point2D(active_points[-2])
            last_pt = wx.Point2D(active_points[-1])
            percent = left_distance / distance
            last_pt[0] = last_second_pt[0] + (last_pt[0] - last_second_pt[0]) * percent
            last_pt[1] = last_second_pt[1] + (last_pt[1] - last_second_pt[1]) * percent
            active_points[-1] = last_pt

        gc.DrawLines(active_points, wx.ODDEVEN_RULE)
