"""命令行入口。"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .category import PlateCategory
from .exceptions import (
    InvalidPlateNumberError,
    ResourceNotFoundError,
    UnsupportedCategoryError,
)
from .generator import PlateGenerator
from .randomizer import random_numbers
from .spec import get_plate_spec, iter_plate_specs

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="plate-gen",
        description="生成符合 GA 36-2018 的中国机动车号牌 SVG 图像",
    )
    parser.add_argument(
        "--category",
        help="号牌种类：中文全名或 ASCII 标识（用 --list-categories 查看全部）",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="列出全部号牌种类及其尺寸、版式与随机支持情况",
    )
    parser.add_argument("--number", help="车牌号码；省略时按种类随机生成")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs"),
        help=(
            "输出路径。默认 outputs（目录），目录内按号码命名；"
            "末段带扩展名时视为具体文件路径"
        ),
    )
    parser.add_argument(
        "--resources",
        type=Path,
        help="资源目录；环境变量 PLATE_RESOURCES_DIR 优先级更高",
    )
    parser.add_argument("--count", type=int, default=5, help="随机生成数量（默认 5）")
    parser.add_argument(
        "--position",
        choices=("front", "rear"),
        default="front",
        help="大型汽车号牌的前/后版式（默认 front）；其余种类仅支持默认版式",
    )
    parser.add_argument("--debug", action="store_true", help="输出调试日志")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


_FILENAME_TRANSLATION = str.maketrans(
    {
        "·": "-",  # 间隔号：直接做文件名在不同平台/工具链下易出问题
        "<": "-",
        ">": "-",
        ":": "-",
        '"': "-",
        "/": "-",
        "\\": "-",
        "|": "-",
        "?": "-",
        "*": "-",
    }
)
"""号码转文件名时替换的字符。

合法号码只含省份简称、字母、数字、专用汉字与间隔号，其中只有 ``·`` 需要
替换；其余条目是为命令行输入边界兜底。合法号码不含 ``-``，故 ``·`` → ``-``
可逆。
"""


def _filename_for_number(number: str, suffix: str = ".svg") -> str:
    """把号码转换为文件名，只做最小必要替换且对合法号码可逆。"""
    return f"{number.translate(_FILENAME_TRANSLATION)}{suffix}"


def _unique_path(path: Path, reserved: set[Path]) -> Path:
    """同名文件已存在或本批次已占用时，追加确定性的 ``-2`` / ``-3`` 后缀。"""
    if not path.exists() and path not in reserved:
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists() and candidate not in reserved:
            return candidate
        index += 1


def _is_directory_target(output: Path) -> bool:
    """判断 ``--output`` 是否表示目录：已存在的目录或末段没有扩展名。"""
    return output.is_dir() or output.suffix == ""


def _output_targets(output: Path, numbers: list[str]) -> list[Path]:
    """为每个号码确定输出路径。

    - 目录语义（默认 ``outputs``、已存在目录、或末段无扩展名）：目录内按号码命名，
      同名时自动避让。
    - 文件语义（末段带扩展名且不是目录）：只有单张时按该路径写入并尊重用户命名；
      批量时取其父目录，仍按号码命名。
    """
    if len(numbers) == 1 and not _is_directory_target(output):
        return [output]

    directory = output if _is_directory_target(output) else output.parent
    reserved: set[Path] = set()
    targets: list[Path] = []
    for number in numbers:
        target = _unique_path(directory / _filename_for_number(number), reserved)
        reserved.add(target)
        targets.append(target)
    return targets


def _print_categories() -> None:
    print(f"{'标识':<24}{'显示名':<16}{'尺寸':<22}{'版式':<12}随机")
    for spec in iter_plate_specs():
        sizes = " / ".join(f"{width}×{height}" for width, height in (v.size for v in spec.variants.values()))
        variants = ",".join(spec.variants)
        randomizable = "是" if spec.randomizable else "否"
        print(
            f"{spec.category.name.lower():<24}"
            f"{spec.display_name:<16}"
            f"{sizes:<22}"
            f"{variants:<12}"
            f"{randomizable}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    """执行命令行程序并返回进程退出码。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.list_categories:
        _print_categories()
        return 0

    if args.category is None:
        parser.error("--category 为必填项（可用 --list-categories 查看全部种类）")
    if args.number is None and args.count < 1:
        parser.error("--count 必须大于 0")

    try:
        spec = get_plate_spec(PlateCategory.from_token(args.category))
    except UnsupportedCategoryError as exc:
        logger.error("%s", exc)
        return 2

    try:
        generator = PlateGenerator(args.resources)
        if args.number is not None:
            numbers = [args.number]
        else:
            numbers = random_numbers(spec.category, args.count)

        for number, output in zip(numbers, _output_targets(args.output, numbers)):
            saved = generator.render_to_file(
                spec.category, number, output, position=args.position
            )
            print(f"已生成: {saved}")
        return 0
    except ResourceNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except (InvalidPlateNumberError, UnsupportedCategoryError) as exc:
        logger.error("%s", exc)
        return 2
    except Exception:
        logger.exception("生成失败")
        return 1
