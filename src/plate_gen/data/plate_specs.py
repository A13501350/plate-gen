"""内置号牌规格表。

每种号牌对应用户可见的“号牌种类”，规格本身是声明式的：尺寸、底板、配色、
字体与字面框、字符摆放、号码结构都在这里定义。生成器、校验器与随机生成器
只读取规格，不包含任何按种类组合的分支。

尺寸、颜色、字面框与字符摆放依据《中华人民共和国机动车号牌》GA 36-2018：
表 1（分类、规格、颜色及适用范围）与图 1~图 19 的尺寸链。多行号牌（大型汽车
后号牌、挂车号牌、摩托车号牌、使馆摩托车号牌、低速车号牌）的每一行字高、字宽
和间距均不同，因此 ``Placement.box`` 按摆放单独声明，不再共用一个字面框。

标准未给出数值的部分（描摹字形的字体本身、反光膜色值、大型新能源后号牌底板
的精确渐变）为推断值，具体说明见 ``doc/plate_spec_matrix.md``。

资源路径均相对于资源根目录。字体目录按底色选择：黄底使用 ``fonts/yellow``
（缺字回退 ``fonts/blue``），其余使用 ``fonts/blue``，新能源使用
``fonts/green``。字形由 Potrace 从号牌图片描摹而来，加载时按墨迹归一化到
``Placement.box``，因此不同来源的字形度量不会混用。
"""

from __future__ import annotations

from pathlib import Path

from ..category import PlateCategory
from ..constants import DIGIT_CHARS, LETTERS, NEW_ENERGY_LETTERS, PROVINCE_CHARS
from ..numbering import (
    FieldRule,
    NumberFormat,
    alternatives_field,
    char_field,
    ga36_serial_field,
    positional_field,
    serial_length_for_slots,
)
from ..spec import BackgroundSpec, FontSpec, Palette, Placement, PlateSpec, VariantSpec

# ---- 资源模板 ----

_BG_440 = Path("backgrounds/440×140.svg")
_BG_220 = Path("backgrounds/220×140.svg")
_BG_300 = Path("backgrounds/300×165.svg")
_BG_REAR = Path("backgrounds/440×220/TrackRear.svg")
_BG_NE_SMALL = Path("backgrounds/480×140/Car.svg")
_BG_NE_LARGE = Path("backgrounds/480×140/Track.svg")

_BLUE = FontSpec(Path("fonts/blue"))
_YELLOW = FontSpec(Path("fonts/yellow"), fallback=Path("fonts/blue"))
_GREEN = FontSpec(Path("fonts/green"))

_BLUE_PALETTE = Palette(background="#223F99", text="white")
_YELLOW_PALETTE = Palette(background="#FFC210", text="black")
_WHITE_PALETTE = Palette(background="white", text="black")
_BLACK_PALETTE = Palette(background="black", text="white")
_POLICE_PALETTE = Palette(background="white", text="black", mark="#E60012")
_NE_PALETTE = Palette(background=None, text="black")

# ---- 号码字段 ----

_PROVINCE = char_field("province", PROVINCE_CHARS)
_ISSUER = char_field("issuer", LETTERS)
_DIGITS_3 = char_field("code", DIGIT_CHARS, length=3)
_SERIAL_DIGITS_3 = char_field("serial", DIGIT_CHARS, length=3)
_SERIAL_CONSULATE = positional_field("serial", DIGIT_CHARS, DIGIT_CHARS + LETTERS)
_SERIAL_NE_SMALL = FieldRule(
    "serial",
    (
        # 表6：首位新能源汽车字母，其余为数字
        (NEW_ENERGY_LETTERS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS),
        # 表6：首位新能源汽车字母、第二位为字母，其余为数字
        (NEW_ENERGY_LETTERS, LETTERS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS),
    ),
)
_SERIAL_NE_LARGE = positional_field(
    "serial", DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, DIGIT_CHARS, NEW_ENERGY_LETTERS
)

_HK_MARK = alternatives_field("mark", "港", "澳")
_POLICE_MARK = alternatives_field("mark", "警")
_TRAINING_MARK = alternatives_field("mark", "学")
_TRAILER_MARK = alternatives_field("mark", "挂")
_EMBASSY_MARK = alternatives_field("mark", "使")
_CONSULATE_MARK = alternatives_field("mark", "领")

# ---- 字位（格位）----
# 式样图中字位总数固定，序号与专用汉字此消彼长；数值取自各图的格位划分。
_SLOTS_440 = 7  # 图1~图5：省 1 + 机关 1 + 序号 5
_SLOTS_220 = 7  # 图9~图12：省 1 + 机关/专用汉字 1 + 序号行 5
_SLOTS_300 = 7  # 图19：省 1 + 机关 1 + 序号行 5
_SLOTS_REAR = 7  # 图6：首行省 1 + 机关 1 + 序号行 5
_SLOTS_NE = 8  # 图7/图8：省 1 + 机关 1 + 序号 6


def _ordinary_number(slots: int, mark: FieldRule | None = None) -> NumberFormat:
    """按版式字位推导普通序号长度。

    省简称与发牌机关固定占 2 格；专用汉字再占 1 格。序号长度由
    :func:`~plate_gen.numbering.serial_length_for_slots` 从总字位推出：
    无专用汉字的号牌必须填满 5 格，带专用汉字的号牌被汉字占去一格、固定 4 位。
    """
    mark_slots = 0 if mark is None else 1
    length = serial_length_for_slots(slots, fixed_slots=2, mark_slots=mark_slots)
    fields = (_PROVINCE, _ISSUER, ga36_serial_field("serial", (length,)))
    if mark is not None:
        fields += (mark,)
    return NumberFormat(fields)


_NORMAL_5 = _ordinary_number(_SLOTS_440)
_EMBASSY = NumberFormat((_DIGITS_3, _SERIAL_DIGITS_3, _EMBASSY_MARK))
_CONSULATE_CAR = NumberFormat((_PROVINCE, _DIGITS_3, _SERIAL_CONSULATE, _CONSULATE_MARK))
_CONSULATE_MOTORCYCLE = NumberFormat((_PROVINCE, _CONSULATE_MARK, _DIGITS_3, _SERIAL_CONSULATE))
_NE_SMALL = NumberFormat((_PROVINCE, _ISSUER, _SERIAL_NE_SMALL))
_NE_LARGE = NumberFormat((_PROVINCE, _ISSUER, _SERIAL_NE_LARGE))

_POLICE = _ordinary_number(_SLOTS_440, _POLICE_MARK)
_TRAINING = _ordinary_number(_SLOTS_440, _TRAINING_MARK)
_HK_MACAO = _ordinary_number(_SLOTS_440, _HK_MARK)
_TRAILER = _ordinary_number(_SLOTS_REAR, _TRAILER_MARK)

# ---- 字面框（单位毫米，数值取自式样图尺寸链）----

_BOX_440 = (45.0, 90.0)  # 图1~图5：字高 90、字宽 45
_BOX_NE_PROVINCE = (45.0, 90.0)  # 图7：省简称 45×90
_BOX_NE_CHAR = (43.0, 90.0)  # 图7：发牌机关与序号 43×90
_BOX_REAR_HEAD = (80.0, 60.0)  # 图6：后号牌首行 80×60
_BOX_REAR_SERIAL = (65.0, 110.0)  # 图6：后号牌序号行 65×110
_BOX_MOTO_PROVINCE = (50.0, 50.0)  # 图9：摩托车首行省简称 50×50
_BOX_MOTO_ISSUER = (50.0, 50.0)  # 图9：摩托车首行发牌机关/专用标记 50×50
_BOX_MOTO_SERIAL = (30.0, 60.0)  # 图9：摩托车序号行 30×60
_BOX_LOW_HEAD = (55.0, 45.0)  # 图19：低速车首行 55×45
_BOX_LOW_SERIAL = (45.0, 90.0)  # 图19：低速车序号行 45×90
_BOX_EMBASSY_MOTO = (35.0, 48.0)  # 图10：使馆摩托车两行数字 35×48
_BOX_EMBASSY_MARK = (45.0, 90.0)  # 图10：“使”45×90，跨两行

# ---- 440×140 坐标 ----
# 图1：左边距 15、字宽 45、字间距 12，间隔符宽 10。
_SERIAL_440 = ((151, 25), (208, 25), (265, 25), (322, 25), (379, 25))
_SERIAL_440_4 = _SERIAL_440[:4]
_MARK_440 = (379, 25)

# 图2（使馆汽车号牌）：右起 15.5、45、12。
_EMBASSY_CODE_440 = ((15.5, 25), (72.5, 25), (129.5, 25))
_EMBASSY_SERIAL_440 = ((208.5, 25), (265.5, 25), (322.5, 25))
_EMBASSY_MARK_440 = (379.5, 25)

# 图3（领馆汽车号牌）：省简称 + 3 位机构编号 + 2 位序号 + 领。
_CONSULATE_CODE_440 = ((72.5, 25), (129.5, 25), (186.5, 25))
_CONSULATE_SERIAL_440 = ((265.5, 25), (322.5, 25))

# ---- 220×140 坐标 ----
# 图9/图11/图12：首行整体居中，左边距 45、省简称 50、间隔符 10、发牌机关 50、
# 右边距 45；因此省简称 45 起、间隔符圆心 110、发牌机关 125 起。
# 序号行 15 起、字宽 30、字间距 10。
_MOTO_PROVINCE = ((45, 10),)
_MOTO_ISSUER = ((125, 10),)
_MOTO_SEPARATOR = (110, 35)
_SERIAL_220 = ((15, 70), (55, 70), (95, 70), (135, 70), (175, 70))
_SERIAL_220_4 = _SERIAL_220[:4]
_MARK_220 = (175, 70)

# 图10（使馆摩托车号牌）：两行各 3 位数字，15 起、字宽 35、间距 12.5；
# “使”45×90 位于 160，上边距 32（右侧竖向尺寸链 32、90），底边距 18。
_EMBASSY_CODE_220 = ((15, 11.5), (62.5, 11.5), (110, 11.5))
_EMBASSY_SERIAL_220 = ((15, 69.5), (62.5, 69.5), (110, 69.5))
_EMBASSY_MARK_220 = (160, 32)

# 图11（领馆摩托车号牌）：首行 沪·领，序号行 3 位机构编号 + 2 位序号。
_CONSULATE_CODE_220 = ((15, 70), (55, 70), (95, 70))
_CONSULATE_SERIAL_220 = ((135, 70), (175, 70))

# ---- 300×165 / 440×220 / 480×140 坐标 ----
# 图19（低速车号牌）：首行居中，省简称 70、发牌机关 175，字宽 55；
# 序号行 13.5 起、字宽 45、间距 12。
_SERIAL_300 = ((13.5, 65), (70.5, 65), (127.5, 65), (184.5, 65), (241.5, 65))

# 图6（大型汽车后号牌/挂车号牌）：首行省简称 110、发牌机关 250，字宽 80、字高 60；
# 序号行 27.6 起、字宽 65、间距 15、字高 110。
_SERIAL_REAR = ((27.6, 90), (107.6, 90), (187.6, 90), (267.6, 90), (347.6, 90))
_SERIAL_REAR_4 = _SERIAL_REAR[:4]
_MARK_REAR = (347.6, 90)

# 图7/图8（新能源汽车号牌）：省简称 15.5；发牌机关 69.5；序号 161.5 起、
# 字宽 43、间距 9。
_SERIAL_480 = ((161.5, 25), (213.5, 25), (265.5, 25), (317.5, 25), (369.5, 25), (421.5, 25))


def _variant(
    name: str,
    size: tuple[int, int],
    background: BackgroundSpec,
    font: FontSpec,
    palette: Palette,
    placements: tuple[Placement, ...],
    slots: int,
    mark_slots: int = 0,
) -> VariantSpec:
    return VariantSpec(name, size, background, font, palette, placements, slots, mark_slots)


def _single(variant: VariantSpec) -> dict[str, VariantSpec]:
    return {"default": variant}


PLATE_SPECS: tuple[PlateSpec, ...] = (
    PlateSpec(
        PlateCategory.SMALL_VEHICLE,
        PlateCategory.SMALL_VEHICLE.value,
        _NORMAL_5,
        _single(
            _variant(
                "default",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(134, 70)),
                _BLUE,
                _BLUE_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((72, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440, box=_BOX_440),
                ),
                _SLOTS_440,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.LARGE_VEHICLE,
        PlateCategory.LARGE_VEHICLE.value,
        _NORMAL_5,
        {
            "front": _variant(
                "front",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(134, 70)),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((72, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440, box=_BOX_440),
                ),
                _SLOTS_440,
            ),
            "rear": _variant(
                "rear",
                (440, 220),
                BackgroundSpec(_BG_REAR, separator=(220, 45)),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", ((110, 15),), box=_BOX_REAR_HEAD),
                    Placement("issuer", ((250, 15),), box=_BOX_REAR_HEAD),
                    Placement("serial", _SERIAL_REAR, box=_BOX_REAR_SERIAL),
                ),
                _SLOTS_REAR,
            ),
        },
        default_variant="front",
    ),
    PlateSpec(
        PlateCategory.POLICE_VEHICLE,
        PlateCategory.POLICE_VEHICLE.value,
        _POLICE,
        {
            "front": _variant(
                "front",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(77, 70), separator_radius=7.0),
                _BLUE,
                _POLICE_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((94, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440_4, box=_BOX_440),
                    Placement("mark", (_MARK_440,), box=_BOX_440, tint="mark"),
                ),
                _SLOTS_440,
                mark_slots=1,
            ),
            "rear": _variant(
                "rear",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(77, 70), separator_radius=8.0),
                _BLUE,
                _POLICE_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((94, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440_4, box=_BOX_440),
                    Placement("mark", (_MARK_440,), box=_BOX_440, tint="mark"),
                ),
                _SLOTS_440,
                mark_slots=1,
            ),
        },
        default_variant="front",
    ),
    PlateSpec(
        PlateCategory.TRAINING_VEHICLE,
        PlateCategory.TRAINING_VEHICLE.value,
        _TRAINING,
        _single(
            _variant(
                "default",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(134, 70)),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((72, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440_4, box=_BOX_440),
                    Placement("mark", (_MARK_440,), box=_BOX_440),
                ),
                _SLOTS_440,
                mark_slots=1,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.HK_MACAO_VEHICLE,
        PlateCategory.HK_MACAO_VEHICLE.value,
        _HK_MACAO,
        _single(
            _variant(
                "default",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(134, 70)),
                _BLUE,
                _BLACK_PALETTE,
                (
                    Placement("province", ((15, 25),), box=_BOX_440),
                    Placement("issuer", ((72, 25),), box=_BOX_440),
                    Placement("serial", _SERIAL_440_4, box=_BOX_440),
                    Placement("mark", (_MARK_440,), box=_BOX_440),
                ),
                _SLOTS_440,
                mark_slots=1,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.NORMAL_MOTORCYCLE,
        PlateCategory.NORMAL_MOTORCYCLE.value,
        _NORMAL_5,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220, separator=_MOTO_SEPARATOR),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", _MOTO_PROVINCE, box=_BOX_MOTO_PROVINCE),
                    Placement("issuer", _MOTO_ISSUER, box=_BOX_MOTO_ISSUER),
                    Placement("serial", _SERIAL_220, box=_BOX_MOTO_SERIAL),
                ),
                _SLOTS_220,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.POLICE_MOTORCYCLE,
        PlateCategory.POLICE_MOTORCYCLE.value,
        _POLICE,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220, separator=_MOTO_SEPARATOR, separator_radius=7.0),
                _BLUE,
                _POLICE_PALETTE,
                (
                    Placement("province", _MOTO_PROVINCE, box=_BOX_MOTO_PROVINCE),
                    Placement("issuer", _MOTO_ISSUER, box=_BOX_MOTO_ISSUER),
                    Placement("serial", _SERIAL_220_4, box=_BOX_MOTO_SERIAL),
                    Placement("mark", (_MARK_220,), box=_BOX_MOTO_SERIAL, tint="mark"),
                ),
                _SLOTS_220,
                mark_slots=1,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.TRAINING_MOTORCYCLE,
        PlateCategory.TRAINING_MOTORCYCLE.value,
        _TRAINING,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220, separator=_MOTO_SEPARATOR),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", _MOTO_PROVINCE, box=_BOX_MOTO_PROVINCE),
                    Placement("issuer", _MOTO_ISSUER, box=_BOX_MOTO_ISSUER),
                    Placement("serial", _SERIAL_220_4, box=_BOX_MOTO_SERIAL),
                    Placement("mark", (_MARK_220,), box=_BOX_MOTO_SERIAL),
                ),
                _SLOTS_220,
                mark_slots=1,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.LIGHT_MOTORCYCLE,
        PlateCategory.LIGHT_MOTORCYCLE.value,
        _NORMAL_5,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220, separator=_MOTO_SEPARATOR),
                _BLUE,
                _BLUE_PALETTE,
                (
                    Placement("province", _MOTO_PROVINCE, box=_BOX_MOTO_PROVINCE),
                    Placement("issuer", _MOTO_ISSUER, box=_BOX_MOTO_ISSUER),
                    Placement("serial", _SERIAL_220, box=_BOX_MOTO_SERIAL),
                ),
                _SLOTS_220,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.LOW_SPEED_VEHICLE,
        PlateCategory.LOW_SPEED_VEHICLE.value,
        _NORMAL_5,
        _single(
            _variant(
                "default",
                (300, 165),
                BackgroundSpec(_BG_300, separator=(150, 32.5)),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", ((70, 10),), box=_BOX_LOW_HEAD),
                    Placement("issuer", ((175, 10),), box=_BOX_LOW_HEAD),
                    Placement("serial", _SERIAL_300, box=_BOX_LOW_SERIAL),
                ),
                _SLOTS_300,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.TRAILER,
        PlateCategory.TRAILER.value,
        _TRAILER,
        _single(
            _variant(
                "default",
                (440, 220),
                BackgroundSpec(_BG_REAR, separator=(220, 45)),
                _YELLOW,
                _YELLOW_PALETTE,
                (
                    Placement("province", ((110, 15),), box=_BOX_REAR_HEAD),
                    Placement("issuer", ((250, 15),), box=_BOX_REAR_HEAD),
                    Placement("serial", _SERIAL_REAR_4, box=_BOX_REAR_SERIAL),
                    Placement("mark", (_MARK_REAR,), box=_BOX_REAR_SERIAL),
                ),
                _SLOTS_REAR,
                mark_slots=1,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.EMBASSY_VEHICLE,
        PlateCategory.EMBASSY_VEHICLE.value,
        _EMBASSY,
        _single(
            _variant(
                "default",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(191.5, 70)),
                _BLUE,
                _BLACK_PALETTE,
                (
                    Placement("code", _EMBASSY_CODE_440, box=_BOX_440),
                    Placement("serial", _EMBASSY_SERIAL_440, box=_BOX_440),
                    Placement("mark", (_EMBASSY_MARK_440,), box=_BOX_440),
                ),
                _SLOTS_440,
                mark_slots=1,
            )
        ),
        randomizable=False,
    ),
    PlateSpec(
        PlateCategory.EMBASSY_MOTORCYCLE,
        PlateCategory.EMBASSY_MOTORCYCLE.value,
        _EMBASSY,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220),
                _BLUE,
                _BLACK_PALETTE,
                (
                    Placement("code", _EMBASSY_CODE_220, box=_BOX_EMBASSY_MOTO),
                    Placement("serial", _EMBASSY_SERIAL_220, box=_BOX_EMBASSY_MOTO),
                    Placement("mark", (_EMBASSY_MARK_220,), box=_BOX_EMBASSY_MARK),
                ),
                _SLOTS_220,
                mark_slots=1,
            )
        ),
        randomizable=False,
    ),
    PlateSpec(
        PlateCategory.CONSULATE_VEHICLE,
        PlateCategory.CONSULATE_VEHICLE.value,
        _CONSULATE_CAR,
        _single(
            _variant(
                "default",
                (440, 140),
                BackgroundSpec(_BG_440, separator=(248.5, 70)),
                _BLUE,
                _BLACK_PALETTE,
                (
                    Placement("province", ((15.5, 25),), box=_BOX_440),
                    Placement("code", _CONSULATE_CODE_440, box=_BOX_440),
                    Placement("serial", _CONSULATE_SERIAL_440, box=_BOX_440),
                    Placement("mark", (_EMBASSY_MARK_440,), box=_BOX_440),
                ),
                _SLOTS_440,
                mark_slots=1,
            )
        ),
        randomizable=False,
    ),
    PlateSpec(
        PlateCategory.CONSULATE_MOTORCYCLE,
        PlateCategory.CONSULATE_MOTORCYCLE.value,
        _CONSULATE_MOTORCYCLE,
        _single(
            _variant(
                "default",
                (220, 140),
                BackgroundSpec(_BG_220, separator=_MOTO_SEPARATOR),
                _BLUE,
                _BLACK_PALETTE,
                (
                    Placement("province", _MOTO_PROVINCE, box=_BOX_MOTO_PROVINCE),
                    Placement("mark", _MOTO_ISSUER, box=_BOX_MOTO_ISSUER),
                    Placement("code", _CONSULATE_CODE_220, box=_BOX_MOTO_SERIAL),
                    Placement("serial", _CONSULATE_SERIAL_220, box=_BOX_MOTO_SERIAL),
                ),
                _SLOTS_220,
                mark_slots=1,
            )
        ),
        randomizable=False,
    ),
    PlateSpec(
        PlateCategory.SMALL_NEW_ENERGY,
        PlateCategory.SMALL_NEW_ENERGY.value,
        _NE_SMALL,
        _single(
            _variant(
                "default",
                (480, 140),
                BackgroundSpec(_BG_NE_SMALL, recolor=False),
                _GREEN,
                _NE_PALETTE,
                (
                    Placement("province", ((15.5, 25),), box=_BOX_NE_PROVINCE),
                    Placement("issuer", ((69.5, 25),), box=_BOX_NE_CHAR),
                    Placement("serial", _SERIAL_480, box=_BOX_NE_CHAR),
                ),
                _SLOTS_NE,
            )
        ),
    ),
    PlateSpec(
        PlateCategory.LARGE_NEW_ENERGY,
        PlateCategory.LARGE_NEW_ENERGY.value,
        _NE_LARGE,
        {
            # 图7：大型新能源汽车前号牌与小型新能源同版式，渐变绿底。
            "front": _variant(
                "front",
                (480, 140),
                BackgroundSpec(_BG_NE_SMALL, recolor=False),
                _GREEN,
                _NE_PALETTE,
                (
                    Placement("province", ((15.5, 25),), box=_BOX_NE_PROVINCE),
                    Placement("issuer", ((69.5, 25),), box=_BOX_NE_CHAR),
                    Placement("serial", _SERIAL_480, box=_BOX_NE_CHAR),
                ),
                _SLOTS_NE,
            ),
            # 图8：大型新能源汽车后号牌为黄绿底。
            "rear": _variant(
                "rear",
                (480, 140),
                BackgroundSpec(_BG_NE_LARGE, recolor=False),
                _GREEN,
                _NE_PALETTE,
                (
                    Placement("province", ((15.5, 25),), box=_BOX_NE_PROVINCE),
                    Placement("issuer", ((69.5, 25),), box=_BOX_NE_CHAR),
                    Placement("serial", _SERIAL_480, box=_BOX_NE_CHAR),
                ),
                _SLOTS_NE,
            ),
        },
        default_variant="front",
    ),
)

PLATE_SPEC_MAP: dict[PlateCategory, PlateSpec] = {
    spec.category: spec for spec in PLATE_SPECS
}
