"""规格表完整性测试。

规格是唯一数据源：这里检查种类覆盖、资源存在、字段与坐标对齐、字形覆盖，
任何一处遗漏都会让生成结果不可用。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

import plate_gen
from plate_gen import (
    PlateCategory,
    UnsupportedCategoryError,
    get_plate_spec,
    iter_plate_specs,
    parse_plate_number,
)

RESOURCE_ROOT = Path(plate_gen.__file__).parent / "resources"
CATEGORIES = list(PlateCategory)
NON_RANDOMIZABLE = {
    PlateCategory.EMBASSY_VEHICLE,
    PlateCategory.EMBASSY_MOTORCYCLE,
    PlateCategory.CONSULATE_VEHICLE,
    PlateCategory.CONSULATE_MOTORCYCLE,
}


def _variants(spec):
    return list(spec.variants.values())


EXPECTED_SLOTS = {
    PlateCategory.SMALL_VEHICLE: (7, 0, 5),
    PlateCategory.LARGE_VEHICLE: (7, 0, 5),
    PlateCategory.POLICE_VEHICLE: (7, 1, 4),
    PlateCategory.TRAINING_VEHICLE: (7, 1, 4),
    PlateCategory.HK_MACAO_VEHICLE: (7, 1, 4),
    PlateCategory.NORMAL_MOTORCYCLE: (7, 0, 5),
    PlateCategory.POLICE_MOTORCYCLE: (7, 1, 4),
    PlateCategory.TRAINING_MOTORCYCLE: (7, 1, 4),
    PlateCategory.LIGHT_MOTORCYCLE: (7, 0, 5),
    PlateCategory.LOW_SPEED_VEHICLE: (7, 0, 5),
    PlateCategory.TRAILER: (7, 1, 4),
    PlateCategory.EMBASSY_VEHICLE: (7, 1, 3),
    PlateCategory.EMBASSY_MOTORCYCLE: (7, 1, 3),
    PlateCategory.CONSULATE_VEHICLE: (7, 1, 2),
    PlateCategory.CONSULATE_MOTORCYCLE: (7, 1, 2),
    PlateCategory.SMALL_NEW_ENERGY: (8, 0, 6),
    PlateCategory.LARGE_NEW_ENERGY: (8, 0, 6),
}
"""字位表：(总格数, 专用汉字占格, 序号可用格)。"""


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_slot_table_matches_expected(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    expected = EXPECTED_SLOTS[category]
    for variant in _variants(spec):
        assert (
            variant.slots,
            variant.mark_slots,
            variant.serial_slots,
        ) == expected, f"{category.value} / {variant.name} 字位与预期不符"


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_placements_use_exactly_the_declared_slots(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    for variant in _variants(spec):
        assert sum(len(placement.coords) for placement in variant.placements) == variant.slots
        serial = next(p for p in variant.placements if p.field == "serial")
        assert len(serial.coords) == variant.serial_slots


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_serial_lengths_are_derived_from_slots(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    rule = next(field for field in spec.number.fields if field.name == "serial")
    for variant in _variants(spec):
        assert rule.max_length == variant.serial_slots
        assert all(len(pattern) <= variant.serial_slots for pattern in rule.patterns)


def test_spec_map_covers_every_category() -> None:
    specs = iter_plate_specs()
    assert [spec.category for spec in specs] == CATEGORIES
    assert len(specs) == len(CATEGORIES)


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_display_name_matches_category(category: PlateCategory) -> None:
    assert get_plate_spec(category).display_name == category.value


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_default_variant_is_defined(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    assert spec.default_variant in spec.variants


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_resources_exist(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    for relative in spec.resources:
        assert (RESOURCE_ROOT / relative).exists(), f"{category.value} 缺少资源 {relative}"
    for variant in _variants(spec):
        assert (RESOURCE_ROOT / variant.background.path).is_file()
        assert (RESOURCE_ROOT / variant.font.directory).is_dir()
        if variant.font.fallback is not None:
            assert (RESOURCE_ROOT / variant.font.fallback).is_dir()


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_variant_size_matches_background(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    for variant in _variants(spec):
        root = etree.parse(str(RESOURCE_ROOT / variant.background.path)).getroot()
        size = (int(root.get("width")), int(root.get("height")))
        assert size == variant.size, f"{category.value} / {variant.name} 尺寸与底板不一致"


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_placements_reference_declared_fields(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    field_lengths = spec.number.max_lengths()
    for variant in _variants(spec):
        placed = {placement.field for placement in variant.placements}
        assert placed == set(field_lengths), (
            f"{category.value} / {variant.name} 的摆放字段 {placed} 与号码字段 "
            f"{set(field_lengths)} 不一致"
        )
        for placement in variant.placements:
            assert len(placement.coords) >= field_lengths[placement.field], (
                f"{category.value} / {variant.name} 的 {placement.field} 需要 "
                f"{field_lengths[placement.field]} 个坐标，实际只有 {len(placement.coords)} 个"
            )


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_number_fields_are_placed_once(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    for variant in _variants(spec):
        names = [placement.field for placement in variant.placements]
        assert len(names) == len(set(names)), f"{category.value} / {variant.name} 字段重复摆放"


@pytest.mark.parametrize("category", CATEGORIES, ids=lambda item: item.name)
def test_every_possible_glyph_exists(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    for variant in _variants(spec):
        for field in spec.number.fields:
            for pattern in field.patterns:
                for charset in pattern:
                    for char in charset:
                        primary = RESOURCE_ROOT / variant.font.directory / f"{char}.svg"
                        fallback = (
                            RESOURCE_ROOT / variant.font.fallback / f"{char}.svg"
                            if variant.font.fallback is not None
                            else None
                        )
                        assert primary.is_file() or (fallback is not None and fallback.is_file()), (
                            f"{category.value} / {variant.name} 缺少字形 {char}"
                        )


def test_randomizable_flags() -> None:
    for category in CATEGORIES:
        assert get_plate_spec(category).randomizable is (category not in NON_RANDOMIZABLE)


def test_sample_numbers_parse_for_every_category() -> None:
    from cases import PLATE_CASES

    covered = {case.category for case in PLATE_CASES}
    assert covered == set(CATEGORIES)
    for case in PLATE_CASES:
        parse_plate_number(case.category, case.number, position=case.position)


@pytest.mark.parametrize("token", ["不存在的号牌", "", "普通"])
def test_unknown_spec_raises(token: str) -> None:
    with pytest.raises(UnsupportedCategoryError):
        get_plate_spec(token)
