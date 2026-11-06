"""SVG 模板操作工具（内部模块）。

所有函数都直接修改并返回传入的 :class:`svgutils.transform.SVGFigure`，
调用方应把返回值当作新的当前对象使用。
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from svgutils.transform import GroupElement, SVGFigure

from .types import PositionCoord

_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
_NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_COMMAND = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def _find(root: etree._Element, expression: str) -> list[etree._Element]:
    return root.xpath(f"//svg:{expression}", namespaces=_NAMESPACES)


def load_svg(path: str | Path) -> SVGFigure:
    """加载 SVG 文件并包装为 :class:`SVGFigure`。"""
    figure = SVGFigure()
    with open(path, encoding="utf-8") as handle:
        figure.root = etree.parse(handle, parser=etree.XMLParser(huge_tree=True)).getroot()
    return figure


def set_rect_fill(figure: SVGFigure, color: str) -> SVGFigure:
    """设置背景矩形（``rect#background``）的填充色。"""
    rects = _find(figure.root, "rect[@id='background']")
    if not rects:
        rects = _find(figure.root, "rect[contains(@mask, 'hole-mask')]")
    if not rects:
        raise ValueError("SVG 模板中缺少背景矩形元素")
    for rect in rects:
        rect.set("fill", color)
    return figure


def set_border_and_separator_color(figure: SVGFigure, color: str) -> SVGFigure:
    """统一设置边框描边色与分隔符填充色。"""
    borders = _find(figure.root, "rect[@id='border']")
    if not borders:
        raise ValueError("SVG 模板中缺少边框元素")
    borders[0].set("stroke", color)

    separators = _find(figure.root, "circle[@id='separator']")
    if not separators:
        raise ValueError("SVG 模板中缺少分隔符元素")
    separators[0].set("fill", color)
    return figure


def set_separator_position(figure: SVGFigure, position: PositionCoord) -> SVGFigure:
    """设置分隔符圆点的位置。"""
    separators = _find(figure.root, "circle[@id='separator']")
    if not separators:
        raise ValueError("SVG 模板中缺少分隔符元素")
    x, y = position
    separators[0].set("cx", str(x))
    separators[0].set("cy", str(y))
    return figure


def set_separator_radius(figure: SVGFigure, radius: float) -> SVGFigure:
    """设置分隔符圆点的半径。"""
    separators = _find(figure.root, "circle[@id='separator']")
    if not separators:
        raise ValueError("SVG 模板中缺少分隔符元素")
    separators[0].set("r", f"{radius:g}")
    return figure


def set_path_fill(figure: SVGFigure, color: str) -> SVGFigure:
    """把 SVG 中所有 ``path`` 的填充色设置为指定颜色。"""
    paths = _find(figure.root, "path")
    if not paths:
        raise ValueError("SVG 中缺少 path 元素")
    for path in paths:
        path.set("fill", color)
    return figure


def path_bbox(path_data: str) -> tuple[float, float, float, float]:
    """计算 path 数据的墨迹边界框 ``(x0, y0, x1, y1)``。

    字形使用 Potrace 从号牌图片描摹而来，path 坐标系跟随源图分辨率，
    不同字形的边界框大小并不一致，需要在放置时统一归一化。

    Args:
        path_data: SVG ``path`` 的 ``d`` 属性。

    Returns:
        墨迹的最小/最大 x、y 坐标。

    Raises:
        ValueError: path 中不含可解析的坐标点。
    """
    points: list[tuple[float, float]] = []
    cursor = (0.0, 0.0)
    position = 0
    while True:
        match = _COMMAND.search(path_data, position)
        if match is None:
            break
        command = match.group(0)
        start = match.end()
        next_match = _COMMAND.search(path_data, start)
        end = next_match.start() if next_match else len(path_data)
        values = [float(token) for token in _NUMBER.findall(path_data[start:end])]
        position = end

        if command in "Zz":
            continue
        if command in "Mm":
            for index in range(0, len(values) - 1, 2):
                if command == "m" and index:
                    cursor = (cursor[0] + values[index], cursor[1] + values[index + 1])
                else:
                    cursor = (values[index], values[index + 1])
                points.append(cursor)
        elif command in "Ll":
            for index in range(0, len(values) - 1, 2):
                if command == "l":
                    cursor = (cursor[0] + values[index], cursor[1] + values[index + 1])
                else:
                    cursor = (values[index], values[index + 1])
                points.append(cursor)
        elif command in "Cc":
            for index in range(0, len(values) - 5, 6):
                seq = values[index:index + 6]
                scale_x, scale_y = (cursor if command == "c" else (0.0, 0.0))
                points.extend(
                    [
                        (scale_x + seq[0], scale_y + seq[1]),
                        (scale_x + seq[2], scale_y + seq[3]),
                    ]
                )
                cursor = (scale_x + seq[4], scale_y + seq[5])
                points.append(cursor)
        elif command in "Ss":
            for index in range(0, len(values) - 3, 4):
                seq = values[index:index + 4]
                scale_x, scale_y = (cursor if command == "s" else (0.0, 0.0))
                points.extend(
                    [
                        (scale_x + seq[0], scale_y + seq[1]),
                        (scale_x + seq[2], scale_y + seq[3]),
                    ]
                )
                cursor = (scale_x + seq[2], scale_y + seq[3])
        elif command in "Qq":
            for index in range(0, len(values) - 3, 4):
                seq = values[index:index + 4]
                scale_x, scale_y = (cursor if command == "q" else (0.0, 0.0))
                points.append((scale_x + seq[0], scale_y + seq[1]))
                cursor = (scale_x + seq[2], scale_y + seq[3])
                points.append(cursor)
        elif command in "Aa":
            for index in range(0, len(values) - 6, 7):
                seq = values[index:index + 7]
                if command == "a":
                    cursor = (cursor[0] + seq[5], cursor[1] + seq[6])
                else:
                    cursor = (seq[5], seq[6])
                points.append(cursor)

    if not points:
        raise ValueError("path 数据中不含坐标点")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def place_glyph(
    figure: SVGFigure, em_size: PositionCoord, position: PositionCoord
) -> GroupElement:
    """按统一字面框归一化字形并定位。

    字形先按墨迹高度缩放到 ``em_size[1]``；墨迹宽度超过 ``em_size[0]`` 时
    横向压缩到字面宽度，否则保持原宽并在字面框内水平居中。这样不同来源、
    不同分辨率的描摹字形都获得一致的字面尺寸，字距可直接按字面框设计。

    Args:
        figure: 已加载的字形 SVG。
        em_size: 统一字面框 ``(宽, 高)``。
        position: 字面框左上角在底板坐标系中的位置。

    Returns:
        已应用变换的字形元素。

    Raises:
        ValueError: 字形不含 path 元素，或墨迹边界框退化。
    """
    paths = _find(figure.root, "path")
    if not paths:
        raise ValueError("字形 SVG 中缺少 path 元素")

    boxes = [path_bbox(path.get("d", "")) for path in paths]
    x0 = min(box[0] for box in boxes)
    y0 = min(box[1] for box in boxes)
    x1 = max(box[2] for box in boxes)
    y1 = max(box[3] for box in boxes)
    width = x1 - x0
    height = y1 - y0
    if width <= 0 or height <= 0:
        raise ValueError("字形墨迹边界框退化")

    em_width, em_height = em_size
    scale_y = em_height / height
    scale_x = min(1.0, em_width / width)
    offset_x = (em_width - width * scale_x) / 2
    x, y = position

    element = figure.getroot()
    element.root.set(
        "transform",
        f"translate({x + offset_x - x0 * scale_x:g},{y - y0 * scale_y:g}) "
        f"scale({scale_x:g},{scale_y:g})",
    )
    return element
