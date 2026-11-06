"""CLI 测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from plate_gen import PlateCategory, parse_plate_number
from plate_gen.cli import _filename_for_number, _output_targets, main


def test_single_number_by_chinese_name(output_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = output_dir / "one.svg"
    code = main(
        ["--category", "小型汽车号牌", "--number", "京A12345", "--output", str(output)]
    )
    assert code == 0
    assert output.is_file()
    assert "已生成" in capsys.readouterr().out


def test_single_number_by_ascii_identifier(output_dir: Path) -> None:
    output = output_dir / "slug.svg"
    assert main(
        ["--category", "small_vehicle", "--number", "京A12345", "--output", str(output)]
    ) == 0
    assert output.is_file()


def test_list_categories(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-categories"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == len(PlateCategory) + 1
    for category in PlateCategory:
        assert any(category.value in line for line in lines)


def test_batch_random_numbers_are_named_by_number(
    output_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        ["--category", "小型汽车号牌", "--count", "3", "--output", str(output_dir)]
    )
    assert code == 0

    saved = [
        Path(line.removeprefix("已生成: "))
        for line in capsys.readouterr().out.strip().splitlines()
    ]
    assert len(saved) == 3
    assert sorted(path.name for path in output_dir.iterdir()) == sorted(
        path.name for path in saved
    )
    for path in saved:
        # 文件名去掉扩展名后应能解析回号码
        parsed = parse_plate_number(PlateCategory.SMALL_VEHICLE, path.stem)
        assert parsed.number == path.stem


def test_single_number_in_directory_is_named_by_number(output_dir: Path) -> None:
    output_dir.mkdir(parents=True)
    code = main(["--category", "小型汽车号牌", "--number", "京A12345", "--output", str(output_dir)])
    assert code == 0
    assert [path.name for path in output_dir.iterdir()] == ["京A12345.svg"]


def test_existing_name_gets_deterministic_suffix(output_dir: Path) -> None:
    output_dir.mkdir(parents=True)
    original = output_dir / "京A12345.svg"
    original.write_text("sentinel", encoding="utf-8")

    assert main(["--category", "小型汽车号牌", "--number", "京A12345", "--output", str(output_dir)]) == 0
    assert original.read_text(encoding="utf-8") == "sentinel"
    assert (output_dir / "京A12345-2.svg").is_file()

    assert main(["--category", "小型汽车号牌", "--number", "京A12345", "--output", str(output_dir)]) == 0
    assert (output_dir / "京A12345-3.svg").is_file()
    assert sorted(path.name for path in output_dir.iterdir()) == [
        "京A12345-2.svg",
        "京A12345-3.svg",
        "京A12345.svg",
    ]


def test_batch_with_filename_uses_parent_directory(output_dir: Path) -> None:
    output = output_dir / "plate.svg"
    assert main(["--category", "小型汽车号牌", "--count", "2", "--output", str(output)]) == 0
    names = sorted(path.name for path in output_dir.iterdir())
    assert len(names) == 2
    assert "plate.svg" not in names
    for name in names:
        parse_plate_number(PlateCategory.SMALL_VEHICLE, Path(name).stem)


def test_separator_character_is_sanitized(tmp_path: Path) -> None:
    assert _filename_for_number("京A·12345") == "京A-12345.svg"
    assert _output_targets(tmp_path / "out", ["京A·12345"]) == [
        tmp_path / "out" / "京A-12345.svg"
    ]


def test_count_one_keeps_requested_name(output_dir: Path) -> None:
    output = output_dir / "single.svg"
    assert main(["--category", "小型汽车号牌", "--count", "1", "--output", str(output)]) == 0
    assert output.is_file()


def test_explicit_number_ignores_count(output_dir: Path) -> None:
    output = output_dir / "explicit.svg"
    code = main(
        [
            "--category", "小型汽车号牌", "--number", "京A12345",
            "--count", "3", "--output", str(output),
        ]
    )
    assert code == 0
    assert [path.name for path in output_dir.iterdir()] == ["explicit.svg"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["--category", "小型汽车号牌", "--number", "京A12345X"],
        ["--category", "不存在种类", "--number", "京A12345"],
        ["--category", "小型汽车号牌", "--number", "京A12345", "--position", "rear"],
        ["--category", "使馆汽车号牌"],
    ],
)
def test_error_exit_codes(arguments: list[str], output_dir: Path) -> None:
    code = main([*arguments, "--output", str(output_dir / "error.svg")])
    assert code == 2


def test_missing_resource_exit_code(tmp_path: Path, output_dir: Path) -> None:
    code = main(
        [
            "--category", "小型汽车号牌", "--number", "京A12345",
            "--output", str(output_dir / "plate.svg"),
            "--resources", str(tmp_path / "missing"),
        ]
    )
    assert code == 1


def test_position_rear_generates_rear_plate(output_dir: Path) -> None:
    output = output_dir / "rear.svg"
    code = main(
        [
            "--category", "大型汽车号牌", "--number", "京A12345",
            "--position", "rear", "--output", str(output),
        ]
    )
    assert code == 0
    root = etree.parse(str(output)).getroot()
    assert (root.get("width"), root.get("height")) == ("440", "220")


def test_count_zero_is_rejected(output_dir: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--category", "小型汽车号牌", "--count", "0", "--output", str(output_dir)])


def test_missing_category_is_rejected(output_dir: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--number", "京A12345", "--output", str(output_dir / "plate.svg")])
