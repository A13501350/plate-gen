"""规格驱动的车牌号码随机生成器。

每种号牌能生成什么样的号码，由该种类规格里的
:class:`~plate_gen.numbering.NumberFormat` 决定；不再有“类型 + 车型”到
蓝牌/绿牌的映射。
"""

from __future__ import annotations

import random

from .category import PlateCategory
from .exceptions import UnsupportedCategoryError
from .spec import get_plate_spec


class PlateRandomizer:
    """车牌号码随机生成器。

    Args:
        rng: 随机数生成器，可注入 ``random.Random(seed)`` 以复现结果。
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()

    def random_number(self, category: PlateCategory | str) -> str:
        """生成一个符合该种类编码规则的号码。

        Raises:
            UnsupportedCategoryError: 种类无法识别，或该种类不支持随机生成。
        """
        spec = get_plate_spec(category)
        if not spec.randomizable:
            raise UnsupportedCategoryError(
                f"{spec.display_name} 不支持随机生成，请使用 --number 指定号码"
            )
        return spec.number.random(self._rng)

    def generate(self, category: PlateCategory | str, count: int = 1) -> list[str]:
        """批量生成号码。

        Raises:
            ValueError: 数量为负。
        """
        if count < 0:
            raise ValueError(f"生成数量不能为负数: {count}")
        return [self.random_number(category) for _ in range(count)]


def random_numbers(
    category: PlateCategory | str,
    count: int = 1,
    rng: random.Random | None = None,
) -> list[str]:
    """按种类生成随机号码。

    Raises:
        UnsupportedCategoryError: 种类无法识别或不支持随机生成。
        ValueError: 数量为负。
    """
    return PlateRandomizer(rng).generate(category, count)
