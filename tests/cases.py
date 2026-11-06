"""测试共用的号牌样例。"""

from __future__ import annotations

from dataclasses import dataclass

from plate_gen import PlateCategory


@dataclass(frozen=True)
class PlateCase:
    """一条样例：种类 + 号码 + 版式。"""

    category: PlateCategory
    number: str
    position: str = "front"

    @property
    def id(self) -> str:
        return f"{self.category.name}-{self.number}-{self.position}"


PLATE_CASES: tuple[PlateCase, ...] = (
    PlateCase(PlateCategory.SMALL_VEHICLE, "京A12345"),
    PlateCase(PlateCategory.LARGE_VEHICLE, "京A12345"),
    PlateCase(PlateCategory.LARGE_VEHICLE, "京A12345", "rear"),
    PlateCase(PlateCategory.POLICE_VEHICLE, "京A1234警"),
    PlateCase(PlateCategory.TRAINING_VEHICLE, "京A1234学"),
    PlateCase(PlateCategory.HK_MACAO_VEHICLE, "粤Z1234港"),
    PlateCase(PlateCategory.HK_MACAO_VEHICLE, "京A1234澳"),
    PlateCase(PlateCategory.NORMAL_MOTORCYCLE, "京A12345"),
    PlateCase(PlateCategory.POLICE_MOTORCYCLE, "京A1234警"),
    PlateCase(PlateCategory.TRAINING_MOTORCYCLE, "京A1234学"),
    PlateCase(PlateCategory.LIGHT_MOTORCYCLE, "京A12345"),
    PlateCase(PlateCategory.LOW_SPEED_VEHICLE, "京A12345"),
    PlateCase(PlateCategory.TRAILER, "京A1234挂"),
    PlateCase(PlateCategory.EMBASSY_VEHICLE, "123456使"),
    PlateCase(PlateCategory.EMBASSY_MOTORCYCLE, "123456使"),
    PlateCase(PlateCategory.CONSULATE_VEHICLE, "京1234B领"),
    PlateCase(PlateCategory.CONSULATE_MOTORCYCLE, "京领1234B"),
    PlateCase(PlateCategory.SMALL_NEW_ENERGY, "京AD12345"),
    PlateCase(PlateCategory.SMALL_NEW_ENERGY, "京AA12345"),
    PlateCase(PlateCategory.LARGE_NEW_ENERGY, "京A12345D"),
)

CASE_IDS = [case.id for case in PLATE_CASES]
