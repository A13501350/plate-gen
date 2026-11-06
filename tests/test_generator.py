"""生成器测试。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import svgutils.transform as sg

import plate_gen
from cases import CASE_IDS, PLATE_CASES
from plate_gen import (
    PlateCategory,
    PlateGenerator,
    ResourceNotFoundError,
    UnsupportedCategoryError,
    get_plate_spec,
    parse_plate_number,
)

RESOURCE_ROOT = Path(plate_gen.__file__).parent / "resources"


def _glyph_group(figure: sg.SVGFigure) -> sg.GroupElement:
    return list(figure.root)[-1]


def _expected_glyph_count(case) -> int:
    parsed = parse_plate_number(case.category, case.number, position=case.position)
    variant = get_plate_spec(case.category).resolve_variant(case.position)
    return sum(len(parsed.fields[placement.field]) for placement in variant.placements)


@pytest.mark.parametrize("case", PLATE_CASES, ids=CASE_IDS)
def test_generate_each_category(generator: PlateGenerator, case) -> None:
    figure = generator.generate(case.category, case.number, position=case.position)
    variant = get_plate_spec(case.category).resolve_variant(case.position)

    assert figure.root.get("width") == str(variant.size[0])
    assert figure.root.get("height") == str(variant.size[1])
    assert len(list(_glyph_group(figure))) == _expected_glyph_count(case)


def test_render_to_file_creates_parent_directories(generator: PlateGenerator, output_dir: Path) -> None:
    path = output_dir / "nested" / "plate.svg"
    saved = generator.render_to_file(PlateCategory.SMALL_VEHICLE, "京A12345", path)
    assert saved == path
    assert path.is_file()
    assert path.stat().st_size > 0


def test_police_special_mark_uses_red(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.POLICE_VEHICLE, "京A1234警")
    groups = list(_glyph_group(figure))
    special_path = groups[-1].xpath(".//*[local-name()='path']")[0]
    normal_path = groups[0].xpath(".//*[local-name()='path']")[0]
    assert special_path.get("fill") == "#E60012"
    assert normal_path.get("fill") == "black"


@pytest.mark.parametrize(
    ("category", "number", "position", "radius"),
    [
        (PlateCategory.SMALL_VEHICLE, "京A12345", "front", 5.0),
        (PlateCategory.POLICE_VEHICLE, "京A1234警", "front", 7.0),
        (PlateCategory.POLICE_VEHICLE, "京A1234警", "rear", 8.0),
        (PlateCategory.POLICE_MOTORCYCLE, "京A1234警", "front", 7.0),
    ],
    ids=["small", "police-front", "police-rear", "police-moto"],
)
def test_separator_radius_follows_variant(
    generator: PlateGenerator, category, number, position, radius
) -> None:
    figure = generator.generate(category, number, position=position)
    separator = figure.root.xpath("//*[local-name()='circle'][@id='separator']")[0]
    assert float(separator.get("r")) == radius


def test_light_motorcycle_is_blue(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.LIGHT_MOTORCYCLE, "京A12345")
    background = figure.root.xpath("//*[local-name()='rect'][@id='background']")[0]
    assert background.get("fill") == "#223F99"


def test_low_speed_plate_size(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.LOW_SPEED_VEHICLE, "京A12345")
    assert figure.root.get("width") == "300"
    assert figure.root.get("height") == "165"
    assert len(list(_glyph_group(figure))) == 7


def test_generate_large_vehicle_rear_plate(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.LARGE_VEHICLE, "京A12345", position="rear")
    assert figure.root.get("width") == "440"
    assert figure.root.get("height") == "220"
    assert len(list(_glyph_group(figure))) == 7


def test_trailer_uses_rear_template(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.TRAILER, "京A1234挂")
    assert figure.root.get("width") == "440"
    assert figure.root.get("height") == "220"
    assert len(list(_glyph_group(figure))) == 7


def test_new_energy_background_is_not_recolored(generator: PlateGenerator) -> None:
    figure = generator.generate(PlateCategory.SMALL_NEW_ENERGY, "京AD12345")
    assert figure.root.get("width") == "480"
    assert figure.root.get("height") == "140"
    assert not figure.root.xpath("//*[local-name()='rect'][@id='background']")


def test_rear_position_is_rejected_for_other_categories(generator: PlateGenerator) -> None:
    with pytest.raises(UnsupportedCategoryError):
        generator.generate(PlateCategory.SMALL_VEHICLE, "京A12345", position="rear")


def test_env_var_overrides_resource_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PLATE_RESOURCES_DIR", str(tmp_path))
    generator = PlateGenerator()
    assert generator.resource_dir == tmp_path
    with pytest.raises(ResourceNotFoundError):
        generator.generate(PlateCategory.SMALL_VEHICLE, "京A12345")


def test_invalid_resource_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(ResourceNotFoundError):
        PlateGenerator(tmp_path / "missing")


def test_missing_glyph_raises(tmp_path: Path) -> None:
    root = tmp_path / "resources"
    (root / "backgrounds").mkdir(parents=True)
    (root / "fonts" / "blue").mkdir(parents=True)
    shutil.copy(RESOURCE_ROOT / "backgrounds" / "440×140.svg", root / "backgrounds" / "440×140.svg")
    shutil.copy(RESOURCE_ROOT / "fonts" / "blue" / "A.svg", root / "fonts" / "blue" / "A.svg")

    generator = PlateGenerator(root)
    with pytest.raises(ResourceNotFoundError):
        generator.generate(PlateCategory.SMALL_VEHICLE, "京A12345")
