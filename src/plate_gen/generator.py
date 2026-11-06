"""车牌 SVG 生成器。

生成过程只读取 :class:`~plate_gen.spec.VariantSpec`：底板、配色、字体与
字符摆放都是数据，因此不存在按号牌种类或版式书写的分支。
"""

from __future__ import annotations

import os
from pathlib import Path

import svgutils.transform as sg

from ._svg import (
    load_svg,
    place_glyph,
    set_border_and_separator_color,
    set_path_fill,
    set_rect_fill,
    set_separator_position,
    set_separator_radius,
)
from .category import PlateCategory
from .exceptions import ResourceNotFoundError
from .spec import FontSpec, VariantSpec, get_plate_spec
from .types import ParsedPlate, PlatePosition
from .validator import parse_plate_number

DEFAULT_RESOURCES_DIR = Path(__file__).resolve().parent / "resources"
"""包内默认资源目录。"""


class PlateGenerator:
    """生成中国机动车号牌 SVG 图像。

    资源目录按以下优先级确定：环境变量 ``PLATE_RESOURCES_DIR``、构造参数
    ``resource_dir``、包内 ``resources/``。

    Args:
        resource_dir: 自定义资源目录。

    Raises:
        ResourceNotFoundError: 资源目录不存在。
    """

    def __init__(self, resource_dir: str | Path | None = None) -> None:
        env_dir = os.getenv("PLATE_RESOURCES_DIR")
        if env_dir:
            self.resource_dir = Path(env_dir)
        elif resource_dir is not None:
            self.resource_dir = Path(resource_dir)
        else:
            self.resource_dir = DEFAULT_RESOURCES_DIR

        if not self.resource_dir.is_dir():
            raise ResourceNotFoundError(self.resource_dir)

    def generate(
        self,
        category: PlateCategory | str,
        number: str,
        *,
        position: PlatePosition | str = "front",
    ) -> sg.SVGFigure:
        """生成车牌 SVG。

        Args:
            category: 号牌种类。
            number: 符合该种类编码规则的车牌号码。
            position: 版式名；大型汽车号牌可选 ``rear``。

        Returns:
            :class:`svgutils.transform.SVGFigure` 对象，可直接保存或继续加工。

        Raises:
            UnsupportedCategoryError: 种类或版式无法识别。
            InvalidPlateNumberError: 号码不符合规范。
            ResourceNotFoundError: 底板或字形资源缺失。
        """
        spec = get_plate_spec(category)
        variant = spec.resolve_variant(position)
        parsed = parse_plate_number(spec.category, number, position=position)

        background = self._prepare_background(variant)
        elements = self._render_characters(parsed, variant)
        if elements:
            background.append(elements)
        return background

    def render_to_file(
        self,
        category: PlateCategory | str,
        number: str,
        output: str | Path,
        *,
        position: PlatePosition | str = "front",
    ) -> Path:
        """生成车牌并保存到文件，自动创建父目录。

        Returns:
            实际写入的文件路径。
        """
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.generate(category, number, position=position).save(str(output_path))
        return output_path

    def _prepare_background(self, variant: VariantSpec) -> sg.SVGFigure:
        background_path = self.resource_dir / variant.background.path
        if not background_path.is_file():
            raise ResourceNotFoundError(background_path)

        figure = load_svg(background_path)
        if not variant.background.recolor:
            return figure

        if variant.palette.background is None:
            raise ValueError(f"{variant.name} 声明了改色但缺少背景色")
        figure = set_rect_fill(figure, variant.palette.background)
        figure = set_border_and_separator_color(figure, variant.palette.text)
        if variant.background.separator is not None:
            figure = set_separator_position(figure, variant.background.separator)
            figure = set_separator_radius(figure, variant.background.separator_radius)
        return figure

    def _render_characters(
        self, parsed: ParsedPlate, variant: VariantSpec
    ) -> list[sg.GroupElement]:
        elements: list[sg.GroupElement] = []
        for placement in variant.placements:
            text = parsed.fields.get(placement.field)
            if text is None:
                raise ValueError(f"{variant.name} 引用了未定义的号码字段: {placement.field}")
            if len(text) > len(placement.coords):
                raise ValueError(
                    f"{variant.name} 的字段 {placement.field} 有 {len(text)} 个字符，"
                    f"但只配置了 {len(placement.coords)} 个坐标"
                )

            color = (
                variant.palette.mark
                if placement.tint == "mark" and variant.palette.mark is not None
                else variant.palette.text
            )
            for char, coord in zip(text, placement.coords):
                figure = load_svg(self._glyph_path(char, variant.font))
                elements.append(
                    place_glyph(
                        set_path_fill(figure, color),
                        placement.box or variant.font.em_box,
                        coord,
                    )
                )
        return elements

    def _glyph_path(self, char: str, font: FontSpec) -> Path:
        primary = self.resource_dir / font.directory / f"{char}.svg"
        if primary.is_file():
            return primary
        if font.fallback is not None:
            fallback = self.resource_dir / font.fallback / f"{char}.svg"
            if fallback.is_file():
                return fallback
        raise ResourceNotFoundError(primary)
