import re
from typing import Literal, TypedDict, Optional

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

PLATE_REGEX_MAP = {
    # 一般类（小型/大型/摩托车/轻便摩托车/低速车）：省、自治区、直辖市简称+发牌机关代号+序号{5}
    "普通号牌": r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{5})$',

    # 专用汽车/摩托车类（挂车/教练/警用/港澳）：省、自治区、直辖市简称+发牌机关代号+序号{4}+[专用号牌简称用汉字]
    "专用号牌": r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{4})([警学挂港澳试超])$',
    
    # 新能源类（小型/大型新能源汽车）：省、自治区、直辖市简称+发牌机关代号+序号{6}
    '新能源号牌': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{6})$',
    
    # 领馆类
    # 领馆汽车：省、自治区、直辖市简称+驻华外交机构编号{3}+序号{2}+领
    "领馆汽车号牌": r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})(\d{3})([0-9A-HJ-NP-Z]{2})领$',
    # 领馆摩托车：省、自治区、直辖市简称+领+驻华外交机构编号{3}+序号{2}
    "领馆摩托车号牌": r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})领(\d{3})([0-9A-HJ-NP-Z]{2})$',
    
    # 使馆类：驻华外交机构编号{3}+序号{3}+使
    "使馆汽车号牌": r'^(\d{3})([0-9A-HJ-NP-Z]{3})使$',
    "使馆摩托车号牌": r'^(\d{3})([0-9A-HJ-NP-Z]{3})使$',
}

class ParsedPlateNumber(TypedDict, total=False):
    """车牌号码解析结果类型
    
    包含车牌各组成部分的字典，根据不同车牌类型返回不同字段。
    具体取决于车牌类型和解析结果。
    """
    plate_type: PlateCategoryName  # 车牌全名
    origin_number: str  # 原始车牌号码
    province: Optional[str]  # 省份简称，1个汉字
    org_code: Optional[str]  # 发牌机关代号，1个字母
    serial: Optional[str]  # 序列号
    special_mark: Optional[str]  # 专用标记，如警、学等
    embassy_code: Optional[str]  # 使馆/领馆代码

# --- Custom Exception ---

class InvalidPlateNumberError(ValueError):
    pass

# --- Function Implementation ---

def parse_plate_number(full_type: str, number: str) -> ParsedPlateNumber:
    """解析车牌号并返回各组成部分
    
    Args:
        full_type (str): 车牌完整式样的名称，例如 "小型汽车号牌"
        number (str): 车牌号码
        
    Returns:
        ParsedPlateNumber: 包含车牌各部分的字典。
            
    Raises:
        InvalidPlateNumberError: 如果车牌号格式与声明的类型不匹配。
        ValueError: 如果传入了不支持的车牌类型。
    """
    # 将车牌全名映射到对应的正则表达式键和解析逻辑
    # 解析逻辑是一个lambda函数，它接收一个匹配组的元组并返回一个包含解析后字段的字典
    TYPE_PARSER_MAP = {
        '小型汽车号牌': ('普通号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),
        '大型汽车前号牌': ('普通号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),
        '普通摩托车号牌': ('普通号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),
        '轻便摩托车号牌': ('普通号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),
        '低速车号牌': ('普通号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),

        '警用汽车号牌': ('专用号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2], 'special_mark': m[3]}),
        '教练汽车号牌': ('专用号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2], 'special_mark': m[3]}),
        '挂车号牌': ('专用号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2], 'special_mark': m[3]}),
        '港澳入出境车号牌': ('专用号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2], 'special_mark': m[3]}),
        '警用摩托车号牌': ('专用号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2], 'special_mark': m[3]}),

        '小型新能源汽车号牌': ('新能源号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),
        '大型新能源汽车号牌': ('新能源号牌', lambda m: {'province': m[0], 'org_code': m[1], 'serial': m[2]}),

        '使馆汽车号牌': ('使馆汽车号牌', lambda m: {'embassy_code': m[0], 'serial': m[1], 'special_mark': '使'}),
        '使馆摩托车号牌': ('使馆摩托车号牌', lambda m: {'embassy_code': m[0], 'serial': m[1], 'special_mark': '使'}),

        '领馆汽车号牌': ('领馆汽车号牌', lambda m: {'province': m[0], 'embassy_code': m[1], 'serial': m[2], 'special_mark': '领'}),
        '领馆摩托车号牌': ('领馆摩托车号牌', lambda m: {'province': m[0], 'embassy_code': m[1], 'serial': m[2], 'special_mark': '领'}),
    }

    # 1. 检查是否为支持的类型
    if full_type not in TYPE_PARSER_MAP:
        raise ValueError(f"不支持的车牌类型: {full_type}")

    # 2. 获取对应的正则表达式和解析器
    regex_key, parser_func = TYPE_PARSER_MAP[full_type]
    regex_pattern = PLATE_REGEX_MAP[regex_key]

    # 3. 进行正则匹配
    match = re.match(regex_pattern, number)
    if not match:
        raise InvalidPlateNumberError(f"车牌号 '{number}' 格式与类型 '{full_type}' 不匹配")

    # 4. 使用对应的解析器提取信息
    parsed_data = parser_func(match.groups())

    # 5. 构建并返回最终结果字典
    result: ParsedPlateNumber = {
        'plate_type': full_type,
        'origin_number': number,
        **parsed_data
    }
    
    return result

# --- Example Usage ---
if __name__ == '__main__':
    # 示例1: 小型汽车
    plate1 = parse_plate_number('小型汽车号牌', '粤B123D4')
    print(f"解析 '粤B123D4': {plate1}")
    # -> {'plate_type': '小型汽车号牌', 'origin_number': '粤B123D4', 'province': '粤', 'org_code': 'B', 'serial': '123D4'}

    # 示例2: 新能源汽车
    plate2 = parse_plate_number('小型新能源汽车号牌', '沪AD12345')
    print(f"解析 '沪AD12345': {plate2}")
    # -> {'plate_type': '小型新能源汽车号牌', 'origin_number': '沪AD12345', 'province': '沪', 'org_code': 'A', 'serial': 'D12345'}

    # 示例3: 教练车
    plate3 = parse_plate_number('教练汽车号牌', '京A5678学')
    print(f"解析 '京A5678学': {plate3}")
    # -> {'plate_type': '教练汽车号牌', 'origin_number': '京A5678学', 'province': '京', 'org_code': 'A', 'serial': '5678', 'special_mark': '学'}

    # 示例4: 使馆汽车
    plate4 = parse_plate_number('使馆汽车号牌', '123001使')
    print(f"解析 '123001使': {plate4}")
    # -> {'plate_type': '使馆汽车号牌', 'origin_number': '123001使', 'embassy_code': '123', 'serial': '001', 'special_mark': '使'}
    
    # 示例5: 领馆摩托车
    plate5 = parse_plate_number('领馆摩托车号牌', '川领21301')
    print(f"解析 '川领21301': {plate5}")
    # -> {'plate_type': '领馆摩托车号牌', 'origin_number': '川领21301', 'province': '川', 'embassy_code': '213', 'serial': '01', 'special_mark': '领'}

    # 示例6: 格式错误
    try:
        parse_plate_number('小型汽车号牌', '京A1234') # 序列号位数不足
    except InvalidPlateNumberError as e:
        print(f"格式错误测试: {e}")
        # -> 格式错误测试: 车牌号 '京A1234' 格式与类型 '小型汽车号牌' 不匹配

    # 示例7: 类型不支持
    try:
        parse_plate_number('临时行驶车号牌', '临京A12345') # 该类型不在映射中
    except ValueError as e:
        print(f"类型不支持测试: {e}")
        # -> 类型不支持测试: 不支持的车牌类型: 临时行驶车号牌