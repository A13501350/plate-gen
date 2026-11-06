"""号牌种类：唯一分类维度。

每种号牌种类对应一份声明式规格（见 :mod:`plate_gen.spec`）。旧实现的
“类型 + 车型”双轴已废弃，本模块只保留种类这一条轴。
"""

from __future__ import annotations

from enum import Enum

from .exceptions import UnsupportedCategoryError


class PlateCategory(str, Enum):
    """全部号牌种类。

    枚举值是号牌的中文全名，同时也是对外展示名称；枚举成员名是稳定的
    ASCII 标识，可在命令行与配置中使用。
    """

    SMALL_VEHICLE = "小型汽车号牌"
    LARGE_VEHICLE = "大型汽车号牌"
    POLICE_VEHICLE = "警用汽车号牌"
    TRAINING_VEHICLE = "教练汽车号牌"
    HK_MACAO_VEHICLE = "港澳入出境车号牌"
    NORMAL_MOTORCYCLE = "普通摩托车号牌"
    POLICE_MOTORCYCLE = "警用摩托车号牌"
    TRAINING_MOTORCYCLE = "教练摩托车号牌"
    LIGHT_MOTORCYCLE = "轻便摩托车号牌"
    LOW_SPEED_VEHICLE = "低速车号牌"
    TRAILER = "挂车号牌"
    EMBASSY_VEHICLE = "使馆汽车号牌"
    EMBASSY_MOTORCYCLE = "使馆摩托车号牌"
    CONSULATE_VEHICLE = "领馆汽车号牌"
    CONSULATE_MOTORCYCLE = "领馆摩托车号牌"
    SMALL_NEW_ENERGY = "小型新能源汽车号牌"
    LARGE_NEW_ENERGY = "大型新能源汽车号牌"

    @classmethod
    def from_token(cls, token: str | PlateCategory) -> PlateCategory:
        """把用户输入解析为种类。

        接受三种等价写法：中文全名、枚举成员名（``SMALL_VEHICLE``）、
        小写标识（``small_vehicle``）。

        Raises:
            UnsupportedCategoryError: 输入无法匹配任何种类。
        """
        if isinstance(token, cls):
            return token

        text = token.strip()
        for category in cls:
            if text == category.value:
                return category

        upper = text.upper()
        if upper in cls.__members__:
            return cls[upper]

        lowered = text.lower()
        for name, category in cls.__members__.items():
            if name.lower() == lowered:
                return category

        available = "、".join(f"{name.lower()}（{category.value}）" for name, category in cls.__members__.items())
        raise UnsupportedCategoryError(f"未识别的号牌种类: {token!r}；可用种类: {available}")
