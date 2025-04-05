from typing import TypedDict, Optional, Literal, Union, List, Tuple

# 定义车牌类型和车辆类型的字面量类型
PlateType = Literal['普通', '大型', '使馆', '领馆']
VehicleType = Literal['汽车', '摩托车', '新能源', '低速车', '轻便摩托车']

# 定义字符位置坐标类型
PositionCoord = Tuple[float, float]

# 定义字符位置配置字典类型
class CharPositionDict(TypedDict, total=False):
    """字符位置配置字典类型
    
    用于定义车牌上各个字符的位置坐标。不同类型的车牌可能包含不同的字段。
    """
    province: PositionCoord  # 省份字符位置
    letter: PositionCoord  # 字母字符位置
    separator: PositionCoord  # 分隔符位置
    digits: List[PositionCoord]  # 数字字符位置列表
    diplomatic: List[PositionCoord]  # 使/领馆专用字符位置
    special_mark: PositionCoord  # 特殊标记位置


# 车牌全名类型
PlateCategoryName = Literal[
    '小型汽车号牌',
    '大型汽车前号牌',
    '警用汽车号牌',
    '教练汽车号牌',
    '港澳入出境车号牌',
    '普通摩托车号牌',
    '警用摩托车号牌',
    '轻便摩托车号牌',
    '低速车号牌',
    '挂车号牌',
    '使馆汽车号牌',
    '使馆摩托车号牌',
    '领馆汽车号牌',
    '领馆摩托车号牌',
    '大型新能源汽车号牌',
    '小型新能源汽车号牌',
]

# 基础车牌解析结果类型
class BaseParsedPlateNumber(TypedDict):
    """车牌号码解析结果的基础类型
    
    所有类型的车牌解析结果都包含的字段
    """
    plate_full_name: PlateCategoryName  # 车牌全名

# 使馆车牌解析结果类型
class EmbassyParsedPlateNumber(BaseParsedPlateNumber):
    """使馆车牌号码解析结果类型
    
    格式: {embassy_code, serial}
    例如: 123456使
    """
    embassy_code: str  # 使馆代码，3位数字
    serial: str  # 序列号，3位数字

# 领馆车牌解析结果类型
class ConsulateParsedPlateNumber(BaseParsedPlateNumber):
    """领馆车牌号码解析结果类型
    
    格式: {province, embassy_code, serial}
    例如: 粤领123AB
    """
    province: str  # 省份简称，1个汉字
    embassy_code: str  # 领馆代码，3位数字
    serial: str  # 序列号，2位字符

# 普通车牌解析结果类型
class NormalParsedPlateNumber(BaseParsedPlateNumber):
    """普通车牌号码解析结果类型
    
    格式: {province, org_code, serial, special_mark?}
    例如: 粤B12345
    """
    province: str  # 省份简称，1个汉字
    org_code: str  # 发牌机关代号，1个字母
    serial: str  # 序列号，4-5位字符
    special_mark: Optional[str]  # 专用标记，如警、学等

# 新能源车牌解析结果类型
class NewEnergyParsedPlateNumber(BaseParsedPlateNumber):
    """新能源车牌号码解析结果类型
    
    格式: {province, org_code, serial}
    例如: 粤B123456
    """
    province: str  # 省份简称，1个汉字
    org_code: str  # 发牌机关代号，1个字母
    serial: str  # 序列号，6位字符

# 统一车牌解析结果类型
ParsedPlateNumber = Union[
    EmbassyParsedPlateNumber,
    ConsulateParsedPlateNumber,
    NormalParsedPlateNumber,
    NewEnergyParsedPlateNumber
]