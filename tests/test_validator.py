"""校验器测试：覆盖全部号牌种类与非法路径。"""

from __future__ import annotations

import pytest

from plate_gen import (
    InvalidPlateNumberError,
    ParsedPlate,
    PlateCategory,
    UnsupportedCategoryError,
    get_plate_spec,
    parse_plate_number,
)
from plate_gen.numbering import ga36_serial_field

from cases import CASE_IDS, PLATE_CASES


@pytest.mark.parametrize("case", PLATE_CASES, ids=CASE_IDS)
def test_parse_returns_category_and_fields(case) -> None:
    parsed = parse_plate_number(case.category, case.number, position=case.position)
    assert isinstance(parsed, ParsedPlate)
    assert parsed.category is case.category
    assert parsed.variant == get_plate_spec(case.category).resolve_variant(case.position).name
    assert parsed.serial


def test_parse_results_cover_every_category() -> None:
    covered = {case.category for case in PLATE_CASES}
    assert covered == set(PlateCategory)


def test_large_vehicle_position_selects_front_or_rear() -> None:
    front = parse_plate_number(PlateCategory.LARGE_VEHICLE, "京A12345")
    assert front.variant == "front"
    rear = parse_plate_number(PlateCategory.LARGE_VEHICLE, "京A12345", position="rear")
    assert rear.variant == "rear"
    assert rear.province == "京"
    assert rear.serial == "12345"


def test_default_variant_is_used_for_normal_categories() -> None:
    parsed = parse_plate_number(PlateCategory.SMALL_VEHICLE, "京A12345")
    assert parsed.variant == "default"


@pytest.mark.parametrize(
    ("category", "position"),
    [
        (PlateCategory.SMALL_VEHICLE, "rear"),
        (PlateCategory.TRAILER, "rear"),
        (PlateCategory.HK_MACAO_VEHICLE, "rear"),
        (PlateCategory.EMBASSY_VEHICLE, "rear"),
        (PlateCategory.SMALL_VEHICLE, "side"),
    ],
)
def test_invalid_position_raises(category: PlateCategory, position: str) -> None:
    with pytest.raises(UnsupportedCategoryError):
        parse_plate_number(category, "京A12345", position=position)


@pytest.mark.parametrize(
    ("category", "number", "field", "value"),
    [
        (PlateCategory.SMALL_VEHICLE, "京A12345", "province", "京"),
        (PlateCategory.SMALL_VEHICLE, "京A12345", "issuer", "A"),
        (PlateCategory.SMALL_VEHICLE, "京A12345", "serial", "12345"),
        (PlateCategory.POLICE_VEHICLE, "京A1234警", "mark", "警"),
        (PlateCategory.EMBASSY_VEHICLE, "123456使", "code", "123"),
        (PlateCategory.EMBASSY_VEHICLE, "123456使", "serial", "456"),
        (PlateCategory.CONSULATE_VEHICLE, "京1234B领", "province", "京"),
        (PlateCategory.CONSULATE_VEHICLE, "京1234B领", "code", "123"),
        (PlateCategory.CONSULATE_VEHICLE, "京1234B领", "serial", "4B"),
        (PlateCategory.CONSULATE_MOTORCYCLE, "京领1234B", "mark", "领"),
        (PlateCategory.SMALL_NEW_ENERGY, "京AD12345", "serial", "D12345"),
        (PlateCategory.LARGE_NEW_ENERGY, "京A12345D", "serial", "12345D"),
    ],
)
def test_parsed_fields(
    category: PlateCategory, number: str, field: str, value: object
) -> None:
    parsed = parse_plate_number(category, number)
    assert parsed.fields[field] == value


def test_convenience_properties() -> None:
    embassy = parse_plate_number(PlateCategory.EMBASSY_VEHICLE, "123456使")
    assert embassy.province is None
    assert embassy.org_code is None
    assert embassy.embassy_code == "123"
    assert embassy.special_mark == "使"

    consulate = parse_plate_number(PlateCategory.CONSULATE_MOTORCYCLE, "京领1234B")
    assert consulate.province == "京"
    assert consulate.embassy_code == "123"
    assert consulate.serial == "4B"


@pytest.mark.parametrize(
    ("category", "number"),
    [
        (PlateCategory.SMALL_VEHICLE, "京A12345X"),
        (PlateCategory.SMALL_VEHICLE, "京A1234"),
        (PlateCategory.SMALL_VEHICLE, "京I12345"),
        (PlateCategory.SMALL_VEHICLE, "京AO1234"),
        (PlateCategory.SMALL_VEHICLE, "京AABC4"),
        (PlateCategory.SMALL_VEHICLE, "京AABC12"),
        (PlateCategory.SMALL_VEHICLE, "京A1234警"),
        (PlateCategory.SMALL_VEHICLE, "京A1234挂"),
        (PlateCategory.POLICE_VEHICLE, "京A12345警"),
        (PlateCategory.POLICE_VEHICLE, "京A1234学"),
        (PlateCategory.TRAINING_VEHICLE, "京A12345学"),
        (PlateCategory.TRAINING_VEHICLE, "京A1234警"),
        (PlateCategory.HK_MACAO_VEHICLE, "京A12345港"),
        (PlateCategory.HK_MACAO_VEHICLE, "京A1234使"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A123"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A1234"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A123456"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A1234警"),
        (PlateCategory.LIGHT_MOTORCYCLE, "京A1234"),
        (PlateCategory.LIGHT_MOTORCYCLE, "京A1234警"),
        (PlateCategory.LOW_SPEED_VEHICLE, "京A1234"),
        (PlateCategory.LOW_SPEED_VEHICLE, "京A1234警"),
        (PlateCategory.TRAILER, "京A12345挂"),
        (PlateCategory.EMBASSY_VEHICLE, "12345使"),
        (PlateCategory.EMBASSY_VEHICLE, "1234567使"),
        (PlateCategory.EMBASSY_VEHICLE, "123456领"),
        (PlateCategory.CONSULATE_VEHICLE, "京123450领"),
        (PlateCategory.CONSULATE_VEHICLE, "京123AB领"),
        (PlateCategory.CONSULATE_VEHICLE, "京领1234B"),
        (PlateCategory.CONSULATE_MOTORCYCLE, "京1234B领"),
        (PlateCategory.CONSULATE_MOTORCYCLE, "京领123AB"),
        (PlateCategory.SMALL_NEW_ENERGY, "京A12345D"),
        (PlateCategory.SMALL_NEW_ENERGY, "京AZ12345"),
        (PlateCategory.SMALL_NEW_ENERGY, "京AD1234"),
        (PlateCategory.SMALL_NEW_ENERGY, "京AD123456"),
        (PlateCategory.LARGE_NEW_ENERGY, "京A12345Z"),
        (PlateCategory.LARGE_NEW_ENERGY, "京AD12345"),
    ],
)
def test_invalid_numbers_raise(category: PlateCategory, number: str) -> None:
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number(category, number)


@pytest.mark.parametrize("category", ["未知种类", "不存在的号牌", "普通汽车"])
def test_unknown_category_raises(category: str) -> None:
    with pytest.raises(UnsupportedCategoryError):
        parse_plate_number(category, "京A12345")


def test_category_token_aliases() -> None:
    assert PlateCategory.from_token("小型汽车号牌") is PlateCategory.SMALL_VEHICLE
    assert PlateCategory.from_token("SMALL_VEHICLE") is PlateCategory.SMALL_VEHICLE
    assert PlateCategory.from_token("small_vehicle") is PlateCategory.SMALL_VEHICLE
    assert PlateCategory.from_token(PlateCategory.SMALL_VEHICLE) is PlateCategory.SMALL_VEHICLE


def test_every_category_has_a_spec() -> None:
    for category in PlateCategory:
        assert get_plate_spec(category).category is category


MARKED_NUMBERS = [
    (PlateCategory.POLICE_VEHICLE, "京A1234警"),
    (PlateCategory.TRAINING_VEHICLE, "京A1234学"),
    (PlateCategory.HK_MACAO_VEHICLE, "京A1234港"),
    (PlateCategory.HK_MACAO_VEHICLE, "京A1234澳"),
    (PlateCategory.POLICE_MOTORCYCLE, "京A1234警"),
    (PlateCategory.TRAINING_MOTORCYCLE, "京A1234学"),
    (PlateCategory.TRAILER, "京A1234挂"),
]


@pytest.mark.parametrize(
    ("category", "number"), MARKED_NUMBERS, ids=[number for _, number in MARKED_NUMBERS]
)
def test_marked_serial_is_capped_by_the_mark_slot(
    category: PlateCategory, number: str
) -> None:
    variant = get_plate_spec(category).resolve_variant()
    assert variant.mark_slots == 1
    assert variant.serial_slots == variant.slots - 3

    parsed = parse_plate_number(category, number)
    assert len(parsed.serial) == variant.serial_slots == 4

    # 专用汉字占一格，序号再多一位就超出总字位
    over = f"{number[:-1]}5{number[-1]}"
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number(category, over)


@pytest.mark.parametrize(
    ("category", "number"),
    [
        (PlateCategory.SMALL_VEHICLE, "京A1234"),
        (PlateCategory.LARGE_VEHICLE, "京A1234"),
        (PlateCategory.NORMAL_MOTORCYCLE, "京A1234"),
        (PlateCategory.LIGHT_MOTORCYCLE, "京A1234"),
        (PlateCategory.LOW_SPEED_VEHICLE, "京A1234"),
    ],
)
def test_unmarked_plate_rejects_four_digit_serial(
    category: PlateCategory, number: str
) -> None:
    """无专用汉字的号牌必须填满 5 个序号格，裸 4 位在真实号牌上不出现。"""
    variant = get_plate_spec(category).resolve_variant()
    assert variant.serial_slots == 5
    with pytest.raises(InvalidPlateNumberError) as error:
        parse_plate_number(category, number)
    message = str(error.value)
    assert number in message
    assert "编码规则" in message


@pytest.mark.parametrize(
    ("category", "number"),
    [
        (PlateCategory.POLICE_MOTORCYCLE, "京A12345警"),
        (PlateCategory.TRAINING_MOTORCYCLE, "京A12345学"),
    ],
)
def test_marked_motorcycle_rejects_five_digit_serial(
    category: PlateCategory, number: str
) -> None:
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number(category, number)


def test_ga36_rules_are_derived_from_the_data_table() -> None:
    four_digit = ga36_serial_field("serial", (4,))
    five_digit = ga36_serial_field("serial", (5,))
    assert len(four_digit.patterns) == 11
    assert len(five_digit.patterns) == 16
    assert {len(pattern) for pattern in four_digit.patterns} == {4}
    assert {len(pattern) for pattern in five_digit.patterns} == {5}


@pytest.mark.parametrize(
    "serial",
    [
        "12345", "A2345", "AB345", "1B345", "12C45", "123D5", "1234E",
        "A234E", "123DE", "A2C45", "1BC45", "A23D5", "1B3D5", "1B34E", "12CD5", "12C4E",
    ],
)
def test_five_digit_serial_rules(serial: str) -> None:
    assert parse_plate_number(PlateCategory.SMALL_VEHICLE, f"京A{serial}").serial == serial


@pytest.mark.parametrize(
    "serial",
    ["1234", "A234", "AB34", "1B34", "12C4", "123D", "A2C4", "1BC4", "A23D", "1B3D", "12CD"],
)
def test_four_digit_serial_rules(serial: str) -> None:
    """4 位序号只出现在专用汉字占掉末格的号牌上。"""
    assert parse_plate_number(PlateCategory.POLICE_VEHICLE, f"京A{serial}警").serial == serial


@pytest.mark.parametrize("serial", ["ABC4", "AB1C", "O234", "I234", "ABC12", "AB1CD", "1234O"])
def test_invalid_serial_rules(serial: str) -> None:
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number(PlateCategory.SMALL_VEHICLE, f"京A{serial}")


def test_exception_hierarchy() -> None:
    assert issubclass(InvalidPlateNumberError, ValueError)
    assert issubclass(UnsupportedCategoryError, ValueError)
