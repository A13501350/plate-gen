"""号码结构规则：用数据描述字段与逐位置字符类。

一种号牌的号码被表示为一组有序字段；每个字段由一个或多个“逐位置字符类
模板”构成。校验、随机生成都从同一份模板出发，不需要为每种号牌写分支。

示例：普通号牌 ``京A12345`` 对应三个字段::

    province: ("京沪津渝...",)
    issuer:   ("ABCDEFGHJKLMNPQRSTUVWXYZ",)
    serial:   ("0123456789",)*5 等若干备选模板
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .constants import DIGIT_CHARS, LETTERS, SERIAL_LETTER_RULES, SERIAL_RULES_BY_LENGTH


def serial_length_for_slots(slots: int, fixed_slots: int, mark_slots: int = 0) -> int:
    """按格位推导序号位数。

    总字位数减去省简称、发牌机关等固定字段与专用汉字占用的格数，就是序号
    必须填满的格数。GA 36-2018 表 3 的“4 位或 5 位”是按号牌类型分列的位数
    类别：无专用汉字的号牌用满 5 格，带专用汉字的号牌被汉字占去一格、固定
    4 位。不存在无标记却只写 4 位、留空第 5 格的号牌。
    """
    available = slots - fixed_slots - mark_slots
    if available <= 0:
        raise ValueError(
            f"总字位 {slots} 减去固定字段 {fixed_slots} 与专用汉字 {mark_slots} 格后，"
            "没有可用的序号格位"
        )
    return available


def _char_class(charset: str) -> str:
    """把字符集合转成安全的单字符正则类。"""
    return "[" + "".join(re.escape(char) for char in charset) + "]"


@dataclass(frozen=True, slots=True)
class FieldRule:
    """号码中的一个字段。

    Attributes:
        name: 字段名，生成时用于取值与定位（``province`` / ``issuer`` /
            ``serial`` / ``mark`` / ``code``）。
        patterns: 备选模板；每个模板是“逐位置字符集合”的元组。模板长度
            即该字段的长度，多个模板可表达不同长度或不同字符约束。
    """

    name: str
    patterns: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        if not self.patterns or any(not pattern for pattern in self.patterns):
            raise ValueError(f"字段 {self.name} 的模板不能为空")

    @property
    def max_length(self) -> int:
        """该字段可能出现的最长长度。"""
        return max(len(pattern) for pattern in self.patterns)

    def fragment(self) -> str:
        """生成带命名分组的正则片段。"""
        alternatives = [
            "".join(_char_class(charset) for charset in pattern)
            for pattern in self.patterns
        ]
        body = alternatives[0] if len(alternatives) == 1 else f"(?:{'|'.join(alternatives)})"
        return f"(?P<{self.name}>{body})"

    def sample(self, rng: random.Random) -> str:
        """按模板随机生成一个字段值。"""
        pattern = rng.choice(self.patterns)
        return "".join(rng.choice(charset) for charset in pattern)


@dataclass(frozen=True, slots=True)
class NumberFormat:
    """一种号牌的完整号码结构。"""

    fields: tuple[FieldRule, ...]

    def __post_init__(self) -> None:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError(f"号码字段名重复: {names}")

    def compile(self) -> re.Pattern[str]:
        """编译为整串匹配的正则表达式。"""
        return _compiled(self.fields)

    def parse(self, number: str) -> dict[str, str] | None:
        """按格式拆分号码；不匹配时返回 ``None``。"""
        match = self.compile().fullmatch(number)
        if match is None:
            return None
        return {key: value for key, value in match.groupdict().items() if value is not None}

    def random(self, rng: random.Random) -> str:
        """按字段顺序随机生成号码。"""
        return "".join(field.sample(rng) for field in self.fields)

    def max_lengths(self) -> dict[str, int]:
        """每个字段的最大长度，用于校验坐标容量。"""
        return {field.name: field.max_length for field in self.fields}


_COMPILED: dict[tuple[FieldRule, ...], re.Pattern[str]] = {}


def _compiled(fields: tuple[FieldRule, ...]) -> re.Pattern[str]:
    pattern = _COMPILED.get(fields)
    if pattern is None:
        pattern = re.compile("".join(field.fragment() for field in fields))
        _COMPILED[fields] = pattern
    return pattern


def char_field(name: str, charset: str, length: int = 1) -> FieldRule:
    """构造固定长度的单字符集合字段。"""
    return FieldRule(name, ((charset,) * length,))


def alternatives_field(name: str, *chars: str) -> FieldRule:
    """构造“每次只出现其中一个字面字符”的字段，如 ``港`` / ``澳``。"""
    return FieldRule(name, tuple((char,) for char in chars))


def positional_field(name: str, *charsets: str) -> FieldRule:
    """构造逐位置约束的字段，如领馆序号 ``数字 + 数字或字母``。"""
    return FieldRule(name, (tuple(charsets),))


def ga36_serial_field(name: str, lengths: tuple[int, ...] = (5,)) -> FieldRule:
    """按 GA 36-2018 的字母位置规则构造序号字段。

    规则数据来自 :data:`plate_gen.constants.SERIAL_LETTER_RULES` 与
    :data:`plate_gen.constants.SERIAL_RULES_BY_LENGTH`，这里只是把它展开成
    逐位置字符类模板，不新增任何规则。
    """
    patterns: list[tuple[str, ...]] = []
    for length in lengths:
        for rule in SERIAL_RULES_BY_LENGTH[length]:
            letter_positions = SERIAL_LETTER_RULES[rule]
            patterns.append(
                tuple(
                    LETTERS if index in letter_positions else DIGIT_CHARS
                    for index in range(length)
                )
            )
    return FieldRule(name, tuple(patterns))
