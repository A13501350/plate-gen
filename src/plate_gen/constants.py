"""项目级常量。

省份、字母集与序号规则都只在这里定义一次，号码结构（见
:mod:`plate_gen.numbering`）与规格表共用。
"""

from __future__ import annotations

from typing import Final

PROVINCES: Final = (
    "京", "沪", "津", "渝", "冀", "晋", "蒙", "辽", "吉", "黑",
    "苏", "浙", "皖", "闽", "赣", "鲁", "豫", "鄂", "湘", "粤",
    "桂", "琼", "川", "贵", "云", "藏", "陕", "甘", "青", "宁", "新",
)
"""31 个省级行政区简称。"""

PROVINCE_CHARS: Final = "".join(PROVINCES)
"""用于拼装正则字符类的省份字符串。"""

LETTERS: Final = "ABCDEFGHJKLMNPQRSTUVWXYZ"
"""发牌机关代号与序号可用字母，按标准排除 I、O。"""

DIGIT_CHARS: Final = "0123456789"
"""阿拉伯数字字符集合。"""

NEW_ENERGY_PURE_ELECTRIC: Final = "DABCE"
"""小型新能源纯电动车首位字母。"""

NEW_ENERGY_NON_ELECTRIC: Final = "FGHJK"
"""小型新能源非纯电动车首位字母。"""

NEW_ENERGY_LETTERS: Final = NEW_ENERGY_PURE_ELECTRIC + NEW_ENERGY_NON_ELECTRIC
"""新能源号牌允许的专用字母集合。"""

SERIAL_LETTER_RULES: Final[dict[int, tuple[int, ...]]] = {
    1: (),
    2: (0,),
    3: (0, 1),
    4: (1,),
    5: (2,),
    6: (3,),
    7: (4,),
    8: (0, 4),
    9: (3, 4),
    10: (0, 2),
    11: (1, 2),
    12: (0, 3),
    13: (1, 3),
    14: (1, 4),
    15: (2, 3),
    16: (2, 4),
}
"""GA 36-2018 普通号牌序号的 16 种字母位置规则。"""

SERIAL_RULES_BY_LENGTH: Final[dict[int, tuple[int, ...]]] = {
    4: (1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 15),
    5: tuple(range(1, 17)),
}
"""不同序号长度下启用的规则编号。"""
