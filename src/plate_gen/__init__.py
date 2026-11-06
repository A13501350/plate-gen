"""plate-gen：生成符合 GA 36-2018 的中国机动车号牌 SVG 图像。

典型用法::

    from plate_gen import PlateCategory, PlateGenerator

    generator = PlateGenerator()
    generator.render_to_file(PlateCategory.SMALL_VEHICLE, "京A12345", "outputs/plate.svg")
"""

__version__ = "1.0.0"

from .category import PlateCategory
from .exceptions import (
    InvalidPlateNumberError,
    PlateGenError,
    ResourceNotFoundError,
    UnsupportedCategoryError,
)
from .generator import PlateGenerator
from .numbering import FieldRule, NumberFormat
from .randomizer import PlateRandomizer, random_numbers
from .spec import (
    BackgroundSpec,
    FontSpec,
    Palette,
    Placement,
    PlateSpec,
    VariantSpec,
    get_plate_spec,
    iter_plate_specs,
)
from .types import ParsedPlate, PlatePosition, PositionCoord
from .validator import parse_plate_number

__all__ = [
    "BackgroundSpec",
    "FieldRule",
    "FontSpec",
    "InvalidPlateNumberError",
    "NumberFormat",
    "Palette",
    "ParsedPlate",
    "Placement",
    "PlateCategory",
    "PlateGenError",
    "PlateGenerator",
    "PlatePosition",
    "PlateRandomizer",
    "PlateSpec",
    "PositionCoord",
    "ResourceNotFoundError",
    "UnsupportedCategoryError",
    "VariantSpec",
    "__version__",
    "get_plate_spec",
    "iter_plate_specs",
    "parse_plate_number",
    "random_numbers",
]
