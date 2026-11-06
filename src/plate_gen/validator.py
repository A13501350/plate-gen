"""号牌号码解析与规范性校验。

校验完全由 :class:`~plate_gen.spec.PlateSpec` 的号码结构驱动：先用规格编译
出的正则拆分字段，再按版本查找物理规格。这里没有任何按种类组合的分支。
"""

from __future__ import annotations

from types import MappingProxyType

from .category import PlateCategory
from .exceptions import InvalidPlateNumberError
from .spec import get_plate_spec
from .types import ParsedPlate, PlatePosition


def parse_plate_number(
    category: PlateCategory | str,
    number: str,
    *,
    position: PlatePosition | str = "front",
) -> ParsedPlate:
    """解析并校验车牌号码。

    Args:
        category: 号牌种类；接受中文全名或 ASCII 标识。
        number: 待解析的车牌号码。
        position: 版式名；仅大型汽车号牌有 ``front`` / ``rear`` 两种，
            其余种类只接受默认版式（``front`` 会解析为 ``default``）。

    Returns:
        包含种类、版式与各字段的不可变 :class:`ParsedPlate`。

    Raises:
        UnsupportedCategoryError: 种类或版式无法识别。
        InvalidPlateNumberError: 号码不符合该种类的编码规则。
    """
    spec = get_plate_spec(category)
    variant = spec.resolve_variant(position)

    fields = spec.number.parse(number)
    if fields is None:
        raise InvalidPlateNumberError(
            spec.display_name,
            number,
            "号码不符合该种类的编码规则",
        )

    return ParsedPlate(
        category=spec.category,
        number=number,
        fields=MappingProxyType(fields),
        variant=variant.name,
    )
