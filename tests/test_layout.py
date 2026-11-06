"""版面几何测试：字形必须归一化到声明的字面框，且落在底板内、不相互重叠。

断言直接读取生成结果中每个字形元素的变换矩阵与 path 边界，因此字体度量
异常（例如描摹残留导致汉字过宽）、坐标或字面尺寸不合理时都会失败。

GA 36-2018 的式样图对多行号牌的每一行给出了不同的字高与字宽（如图6 后号牌
首行 80×60、序号行 65×110），因此字面框按 ``Placement.box`` 校验，而不是
整块号牌共用一个字面框。
"""

from __future__ import annotations

import re
from itertools import groupby
from types import SimpleNamespace

import pytest

from cases import CASE_IDS, PLATE_CASES
from plate_gen import PlateCategory, PlateGenerator, get_plate_spec, parse_plate_number
from plate_gen._svg import path_bbox

_TRANSFORM = re.compile(r"translate\(([^,]+),([^)]+)\) scale\(([^,]+),([^)]+)\)")


def _element_bbox(element) -> tuple[float, float, float, float]:
    paths = element.root.xpath(".//*[local-name()='path']")
    assert paths, "字形元素中缺少 path"
    boxes = [path_bbox(path.get("d", "")) for path in paths]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _boxes(
    generator: PlateGenerator, case
) -> list[
    tuple[
        str,
        float,
        float,
        float,
        float,
        float,
        tuple[float, float, float, float, float, float],
        tuple[float, float],
    ]
]:
    """返回 (字符, 左, 上, 右, 下, 行基准 y, 原始墨迹框, 字面框) 列表。"""
    spec = get_plate_spec(case.category)
    variant = spec.resolve_variant(case.position)
    parsed = parse_plate_number(case.category, case.number, position=case.position)

    expected = [
        (char, coord, placement.box or variant.font.em_box)
        for placement in variant.placements
        for char, coord in zip(parsed.fields[placement.field], placement.coords)
    ]
    elements = generator._render_characters(parsed, variant)
    assert len(expected) == len(elements)

    boxes = []
    for (char, (_, y), em_box), element in zip(expected, elements):
        left, top, right, bottom = _element_bbox(element)
        tx, ty, sx, sy = (
            float(value) for value in _TRANSFORM.fullmatch(element.root.get("transform")).groups()
        )
        boxes.append(
            (
                char,
                tx + left * sx,
                ty + top * sy,
                tx + right * sx,
                ty + bottom * sy,
                y,
                (left, top, right, bottom, sx, sy),
                em_box,
            )
        )
    return boxes


@pytest.mark.parametrize("case", PLATE_CASES, ids=CASE_IDS)
def test_glyphs_fill_declared_em_box(generator: PlateGenerator, case) -> None:
    for char, *_, ink, (em_width, em_height) in _boxes(generator, case):
        left, top, right, bottom, scale_x, scale_y = ink
        assert abs((bottom - top) * scale_y - em_height) < 1e-2, f"{char} 字高未归一化"
        assert (right - left) * scale_x <= em_width + 1e-2, f"{char} 字宽超出字面框"


@pytest.mark.parametrize("case", PLATE_CASES, ids=CASE_IDS)
def test_glyphs_stay_within_plate(generator: PlateGenerator, case) -> None:
    width, height = get_plate_spec(case.category).resolve_variant(case.position).size
    for char, left, top, right, bottom, *_ in _boxes(generator, case):
        assert left >= 0, f"{case.id} 的字形 {char} 越过左边界"
        assert top >= 0, f"{case.id} 的字形 {char} 越过上边界"
        assert right <= width, f"{case.id} 的字形 {char} 越过右边界"
        assert bottom <= height, f"{case.id} 的字形 {char} 越过下边界"


@pytest.mark.parametrize("case", PLATE_CASES, ids=CASE_IDS)
def test_glyphs_do_not_overlap(generator: PlateGenerator, case) -> None:
    boxes = sorted(_boxes(generator, case), key=lambda box: box[5])
    for _, row in groupby(boxes, key=lambda box: box[5]):
        ordered = sorted(row, key=lambda box: box[1])
        for previous, current in zip(ordered, ordered[1:]):
            assert previous[3] <= current[1] + 0.01, (
                f"{case.id} 的 {previous[0]} 与 {current[0]} 字符重叠："
                f"前字右边界 {previous[3]:.2f} > 后字左边界 {current[1]:.2f}"
            )


@pytest.mark.parametrize(
    ("category", "number", "position"),
    [
        (PlateCategory.SMALL_VEHICLE, "京A12345", None),
        (PlateCategory.LARGE_VEHICLE, "京A12345", None),
        (PlateCategory.LARGE_VEHICLE, "京A12345", "rear"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A12345", None),
        (PlateCategory.LIGHT_MOTORCYCLE, "京A12345", None),
        (PlateCategory.LOW_SPEED_VEHICLE, "京A12345", None),
    ],
)
def test_unmarked_plate_fills_every_slot(
    generator: PlateGenerator,
    category: PlateCategory,
    number: str,
    position: str | None,
) -> None:
    """无专用汉字的号牌序号必须填满 5 格，渲染后画布上没有空槽。"""
    variant = get_plate_spec(category).resolve_variant(position)
    assert variant.mark_slots == 0
    assert len(number) == variant.slots == variant.serial_slots + 2
    assert sum(len(placement.coords) for placement in variant.placements) == variant.slots

    boxes = _boxes(
        generator,
        SimpleNamespace(category=category, number=number, position=position),
    )
    assert len(boxes) == variant.slots


@pytest.mark.parametrize(
    ("category", "number"),
    [
        (PlateCategory.POLICE_VEHICLE, "京A1234警"),
        (PlateCategory.TRAINING_VEHICLE, "京A1234学"),
        (PlateCategory.HK_MACAO_VEHICLE, "京A1234港"),
        (PlateCategory.POLICE_MOTORCYCLE, "京A1234警"),
        (PlateCategory.TRAINING_MOTORCYCLE, "京A1234学"),
        (PlateCategory.TRAILER, "京A1234挂"),
        (PlateCategory.EMBASSY_VEHICLE, "123456使"),
        (PlateCategory.EMBASSY_MOTORCYCLE, "123456使"),
        (PlateCategory.CONSULATE_VEHICLE, "京1234B领"),
        (PlateCategory.CONSULATE_MOTORCYCLE, "京领1234B"),
    ],
)
def test_marked_plate_fills_every_declared_slot(
    generator: PlateGenerator, category: PlateCategory, number: str
) -> None:
    variant = get_plate_spec(category).resolve_variant()
    boxes = _boxes(
        generator, SimpleNamespace(category=category, number=number, position=None)
    )
    assert len(boxes) == variant.slots
    assert sum(len(placement.coords) for placement in variant.placements) == variant.slots
