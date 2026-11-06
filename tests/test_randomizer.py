"""随机生成器测试。"""

from __future__ import annotations

import random

import pytest

from plate_gen import (
    PlateCategory,
    PlateRandomizer,
    UnsupportedCategoryError,
    get_plate_spec,
    parse_plate_number,
    random_numbers,
)

RANDOMIZABLE = [
    category for category in PlateCategory
    if category not in {
        PlateCategory.EMBASSY_VEHICLE,
        PlateCategory.EMBASSY_MOTORCYCLE,
        PlateCategory.CONSULATE_VEHICLE,
        PlateCategory.CONSULATE_MOTORCYCLE,
    }
]


@pytest.mark.parametrize("category", RANDOMIZABLE, ids=lambda item: item.name)
def test_random_numbers_are_valid(category: PlateCategory) -> None:
    numbers = random_numbers(category, 50, random.Random(7))
    assert len(numbers) == 50
    for number in numbers:
        parse_plate_number(category, number)


def test_random_is_reproducible_with_seed() -> None:
    first = random_numbers(PlateCategory.SMALL_VEHICLE, 10, random.Random(42))
    second = random_numbers(PlateCategory.SMALL_VEHICLE, 10, random.Random(42))
    assert first == second


def test_new_energy_structures() -> None:
    small = random_numbers(PlateCategory.SMALL_NEW_ENERGY, 20, random.Random(3))
    for number in small:
        assert number[2] in "DABCEFGHJK"
        assert number[3:].isdigit() or (number[3].isalpha() and number[4:].isdigit())

    large = random_numbers(PlateCategory.LARGE_NEW_ENERGY, 20, random.Random(3))
    for number in large:
        assert number[-1] in "DABCEFGHJK"
        assert number[-6:-1].isdigit()


def test_serial_lengths_follow_the_spec() -> None:
    """无标记种类没有可留空的格位，随机结果长度恒为 7。"""
    for number in random_numbers(PlateCategory.SMALL_VEHICLE, 50, random.Random(5)):
        assert len(number) == 7
    for number in random_numbers(PlateCategory.NORMAL_MOTORCYCLE, 50, random.Random(5)):
        assert len(number) == 7


@pytest.mark.parametrize("category", RANDOMIZABLE, ids=lambda item: item.name)
def test_random_numbers_fill_every_slot(category: PlateCategory) -> None:
    spec = get_plate_spec(category)
    variant = spec.resolve_variant()
    for number in random_numbers(category, 60, random.Random(11)):
        parsed = parse_plate_number(category, number)
        assert len(number) == variant.slots
        assert len(parsed.serial) == variant.serial_slots


def test_zero_count_returns_empty_list() -> None:
    assert PlateRandomizer().generate(PlateCategory.SMALL_VEHICLE, 0) == []


def test_negative_count_raises() -> None:
    with pytest.raises(ValueError):
        PlateRandomizer().generate(PlateCategory.SMALL_VEHICLE, -1)


@pytest.mark.parametrize("category", ["黄色号牌", "未知种类", "普通"])
def test_unknown_category_raises(category: str) -> None:
    with pytest.raises(UnsupportedCategoryError):
        random_numbers(category, 1)


@pytest.mark.parametrize(
    "category",
    [
        PlateCategory.EMBASSY_VEHICLE,
        PlateCategory.EMBASSY_MOTORCYCLE,
        PlateCategory.CONSULATE_VEHICLE,
        PlateCategory.CONSULATE_MOTORCYCLE,
    ],
)
def test_special_categories_are_not_randomizable(category: PlateCategory) -> None:
    with pytest.raises(UnsupportedCategoryError):
        random_numbers(category, 1)
