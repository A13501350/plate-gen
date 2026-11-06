"""号牌规格模型：每种号牌一份声明式描述。

规格把尺寸、底板、配色、字体、字面框、字符摆放与号码结构放在一起，
生成器、校验器与随机生成器都只读取规格，不再按“类型 + 车型”组合写分支。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .category import PlateCategory
from .exceptions import UnsupportedCategoryError
from .numbering import NumberFormat
from .types import PositionCoord


@dataclass(frozen=True, slots=True)
class FontSpec:
    """字形资源与字面框。

    Attributes:
        directory: 字形目录，相对于资源根目录。
        fallback: 主目录缺字时的回退目录；``None`` 表示不回退。
        em_box: 统一字面框 ``(宽, 高)``，字形按墨迹归一化到该尺寸。
    """

    directory: Path
    fallback: Path | None = None
    em_box: tuple[float, float] = (45.0, 90.0)


@dataclass(frozen=True, slots=True)
class BackgroundSpec:
    """底板模板与改色方式。

    Attributes:
        path: 底板 SVG，相对于资源根目录。
        recolor: 是否按配色重绘背景、边框与分隔符；``False`` 表示底板自带
            配色，原样使用（新能源底板）。
        separator: 分隔符圆点位置；``None`` 表示该底板没有分隔符。
        separator_radius: 分隔符圆点半径，单位毫米。GA 36-2018 各版式的间隔符
            直径并不相同（图 4 为 14、图 5 为 16、图 12 为 14，其余为 10），
            因此半径按版式声明。
    """

    path: Path
    recolor: bool = True
    separator: PositionCoord | None = None
    separator_radius: float = 5.0


@dataclass(frozen=True, slots=True)
class Palette:
    """号牌配色。

    Attributes:
        background: 底板填充色；``None`` 仅与 ``recolor=False`` 搭配。
        text: 字符、边框与分隔符颜色。
        mark: 专用标记的独立颜色（如警用号牌的红色“警”字）。
    """

    background: str | None
    text: str
    mark: str | None = None


@dataclass(frozen=True, slots=True)
class Placement:
    """一类字段在底板上的摆放规则。

    Attributes:
        field: 引用的号码字段名。
        coords: 字面框左上角坐标，按字符顺序排列。
        box: 该摆放的字面框（宽, 高），单位毫米；``None`` 时使用
            :attr:`FontSpec.em_box`。GA 36-2018 的式样图对多行号牌的每一行
            给出了不同的字高与字宽（如图6 后号牌首行 80×60、序号行 65×110），
            因此字面框按摆放声明。
        tint: 着色键；``"mark"`` 表示使用 ``Palette.mark``，``None`` 使用
            ``Palette.text``。
    """

    field: str
    coords: tuple[PositionCoord, ...]
    box: tuple[float, float] | None = None
    tint: str | None = None


@dataclass(frozen=True, slots=True)
class VariantSpec:
    """一种物理版式（尺寸 + 底板 + 摆放）。

    大多数号牌只有 ``default`` 一种版式；大型汽车号牌有 ``front`` / ``rear``。

    Attributes:
        slots: 该版式的总字位数（格位）。字位总数固定，序号与专用汉字此消彼长，
            数值取自式样图的格位划分（如 440×140 为省 1 + 机关 1 + 序号 5 = 7）。
        mark_slots: 专用汉字占用的格数（无专用汉字为 0，通常为 1）。

    序号可用格数由 :attr:`serial_slots` 推出，不在各处并列写死。
    """

    name: str
    size: tuple[int, int]
    background: BackgroundSpec
    font: FontSpec
    palette: Palette
    placements: tuple[Placement, ...]
    slots: int
    mark_slots: int = 0

    def __post_init__(self) -> None:
        placed = sum(len(placement.coords) for placement in self.placements)
        if placed != self.slots:
            raise ValueError(
                f"{self.name} 声明了 {self.slots} 个字位，但摆放占用了 {placed} 个"
            )
        marked = sum(
            len(placement.coords)
            for placement in self.placements
            if placement.field == "mark"
        )
        if marked != self.mark_slots:
            raise ValueError(
                f"{self.name} 声明了 {self.mark_slots} 个专用汉字格位，"
                f"但摆放占用了 {marked} 个"
            )

    @property
    def serial_slots(self) -> int:
        """序号可用格数 = 总字位 − 序号以外各字段占用的格数。"""
        fixed = sum(
            len(placement.coords)
            for placement in self.placements
            if placement.field != "serial"
        )
        return self.slots - fixed


@dataclass(frozen=True, slots=True)
class PlateSpec:
    """一种号牌的完整规格。

    Attributes:
        category: 号牌种类。
        display_name: 中文显示名。
        number: 号码结构规则。
        variants: 版式集合，至少包含 ``default_variant``。
        default_variant: 未指定版式时使用的键。
        randomizable: 是否允许随机生成号码。
    """

    category: PlateCategory
    display_name: str
    number: NumberFormat
    variants: Mapping[str, VariantSpec]
    default_variant: str = "default"
    randomizable: bool = True

    def __post_init__(self) -> None:
        """校验号码结构与各版式的字位数一致。

        序号长度由版式的 ``serial_slots`` 推出，这里防止号码规则与格位脱节。
        """
        serial_rule = next(
            (field for field in self.number.fields if field.name == "serial"), None
        )
        if serial_rule is None:
            return
        for name, variant in self.variants.items():
            if serial_rule.max_length != variant.serial_slots:
                raise ValueError(
                    f"{self.display_name} / {name} 的序号最长 {serial_rule.max_length} 位，"
                    f"但版式只留出 {variant.serial_slots} 格"
                )

    def resolve_variant(self, position: str | None = None) -> VariantSpec:
        """按版式名查询物理规格。

        ``position`` 为 ``None`` 时使用默认版式；``front`` 在仅有默认版式的
        种类上会落到 ``default``，这是统一的解析规则，不针对具体种类。

        Raises:
            UnsupportedCategoryError: 版式不受支持。
        """
        if position is None:
            key = self.default_variant
        elif position in self.variants:
            key = position
        elif position == "front" and self.default_variant == "default" and "default" in self.variants:
            key = "default"
        else:
            keys = "、".join(self.variants)
            raise UnsupportedCategoryError(
                f"{self.display_name} 不支持版式 {position!r}；可用版式: {keys}"
            )

        variant = self.variants.get(key)
        if variant is None:
            raise UnsupportedCategoryError(
                f"{self.display_name} 的默认版式 {key!r} 未定义"
            )
        return variant

    @property
    def resources(self) -> tuple[Path, ...]:
        """该规格声明的全部资源路径。"""
        paths: list[Path] = []
        for variant in self.variants.values():
            if variant.background.path not in paths:
                paths.append(variant.background.path)
            if variant.font.directory not in paths:
                paths.append(variant.font.directory)
            if variant.font.fallback is not None and variant.font.fallback not in paths:
                paths.append(variant.font.fallback)
        return tuple(paths)


def get_plate_spec(category: PlateCategory | str) -> PlateSpec:
    """按种类查询规格。

    Raises:
        UnsupportedCategoryError: 种类无法识别或没有对应规格。
    """
    from .data.plate_specs import PLATE_SPEC_MAP

    resolved = PlateCategory.from_token(category)
    spec = PLATE_SPEC_MAP.get(resolved)
    if spec is None:
        raise UnsupportedCategoryError(f"未找到号牌规格: {resolved.value}")
    return spec


def iter_plate_specs() -> tuple[PlateSpec, ...]:
    """按枚举顺序返回全部规格。"""
    from .data.plate_specs import PLATE_SPEC_MAP

    return tuple(PLATE_SPEC_MAP[category] for category in PlateCategory)
