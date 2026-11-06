"""公共类型定义。

本模块只包含类型别名与数据结构，可安全地被任意模块导入。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from .category import PlateCategory

PlatePosition = Literal["front", "rear"]
"""大型汽车号牌的安装位置；其余种类只支持默认版式。"""

PositionCoord = tuple[float, float]
"""字符字面框左上角坐标 ``(x, y)``。"""


@dataclass(frozen=True, slots=True)
class ParsedPlate:
    """车牌号码解析结果。

    Attributes:
        category: 号牌种类。
        number: 原始号码。
        fields: 按规格字段名拆分的号码片段，例如
            ``{"province": "京", "issuer": "A", "serial": "12345"}``。
        variant: 实际使用的版式名（``default`` / ``front`` / ``rear``）。
    """

    category: PlateCategory
    number: str
    fields: Mapping[str, str]
    variant: str = "default"

    @property
    def province(self) -> str | None:
        """省、自治区、直辖市简称。"""
        return self.fields.get("province")

    @property
    def org_code(self) -> str | None:
        """发牌机关代号（单个字母）。"""
        return self.fields.get("issuer")

    @property
    def serial(self) -> str:
        """序号部分。"""
        return self.fields.get("serial", "")

    @property
    def special_mark(self) -> str | None:
        """专用标记，如 ``警``、``学``、``挂``。"""
        return self.fields.get("mark")

    @property
    def embassy_code(self) -> str | None:
        """使馆 / 领馆代码。"""
        return self.fields.get("code")
