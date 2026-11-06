"""统一的异常体系。

所有异常都继承 :class:`PlateGenError`，同时保留对标准异常（``ValueError``、
``FileNotFoundError``）的继承，避免破坏调用方已有的 ``except`` 逻辑。
"""

from __future__ import annotations

from pathlib import Path


class PlateGenError(Exception):
    """plate-gen 所有异常的基类。"""


class InvalidPlateNumberError(PlateGenError, ValueError):
    """车牌号码不符合该种类的编码规则。"""

    def __init__(self, category: str, number: str, reason: str | None = None) -> None:
        self.category = category
        self.number = number
        self.reason = reason
        message = f"无效的车牌号 {number!r}（种类: {category}）"
        if reason:
            message = f"{message}: {reason}"
        super().__init__(message)


class UnsupportedCategoryError(PlateGenError, ValueError):
    """号牌种类、版式或配置不受支持。"""


class ResourceNotFoundError(PlateGenError, FileNotFoundError):
    """生成所需的资源文件缺失。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__(f"资源文件不存在: {self.path}")
