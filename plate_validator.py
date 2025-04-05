import re
from typing import Optional, Union, Tuple
from plate_config import PlateConfig, PlateType, VehicleType
from exceptions import InvalidPlateNumberError, InvalidVehicleComboError
import logging

from plate_types import NormalParsedPlateNumber, ParsedPlateNumber, EmbassyParsedPlateNumber, ConsulateParsedPlateNumber, NewEnergyParsedPlateNumber, PlateCategoryName

logger = logging.getLogger(__name__)

PLATE_REGEX_MAP = {

    # 领馆汽车：省、自治区、直辖市简称+驻华外交机构编号{3}+序号{2}+领
    # 领馆摩托车：省、自治区、直辖市简称+领+驻华外交机构编号{3}+序号{2}
    '领馆汽车': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})(\d{3})([0-9A-HJ-NP-Z]{2})领$',
    '领馆摩托车': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})领(\d{3})([0-9A-HJ-NP-Z]{2})$',
    
    # 使馆类：驻华外交机构编号{3}+序号{3}+使
    '使馆汽车': r'^(\d{3})(\d{3})使$',
    '使馆摩托车': r'^(\d{3})(\d{3})使$',
    
    # 普通类：省、自治区、直辖市简称+发牌机关代号+序号{4,5}+[专用号牌简称用汉字]
    '普通': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{4,5})([警学挂港澳试超])?$',
    
    # 新能源类：省、自治区、直辖市简称+发牌机关代号+序号{6}
    '大型新能源': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{6})$',
    '小型新能源': r'^([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1})([A-HJ-NP-Z]{1})([0-9A-HJ-NP-Z]{6})$',
}

def validate_embassy_consulate_serial(plate_type: str, groups: tuple) -> None:
    """验证使馆/领馆车牌序号"""
    # 外交编号校验
    if not (groups[0].isdigit() or len(groups[0]) == 3):
        raise InvalidPlateNumberError(plate_type, f"外交代码必须为数字: {groups[0]}")

    # 根据车牌类型选择验证规则
    if plate_type == '领馆汽车' or plate_type == '领馆摩托车':
        # 序号长度校验
        if len(groups[1]) != 2:
            raise InvalidPlateNumberError(plate_type, f"序号长度错误: {groups[1]}")
        # 序号内容校验
        if not (groups[1][0].isdigit() and (groups[1][1].isdigit() or groups[1][1].isalpha())):
            raise InvalidPlateNumberError(plate_type, f"序号内容错误: {groups[1]}")
    elif plate_type == '使馆汽车' or plate_type == '使馆摩托车':
        # 序号长度校验
        if len(groups[1]) != 3:
            raise InvalidPlateNumberError(plate_type, f"序号长度错误: {groups[1]}")
        # 序号内容校验
        if not all(c.isdigit() for c in groups[1]):
            raise InvalidPlateNumberError(plate_type, f"序号内容错误: {groups[1]}")

def validate_normal_serial(plate_type: str, groups: Tuple, special_mark: Optional[str]) -> None:
    """验证普通车牌序号"""
    serial_length = len(groups[2])
    
    # 定义16种启用顺序的字母位置规则
    valid_patterns = {
        4: [1,2,3,4,5,6,10,11,12,13,15],
        5: list(range(1,17))
    }
    
    # 检查序号是否符合字母位置组合规则
    if not validate_serial_pattern(groups[2], valid_patterns[serial_length]):
        raise InvalidPlateNumberError(plate_type, "序号字母位置组合不符合规范")
    
    # 专用简称位置校验
    if special_mark:
        required_mark = {'警用':'警', '教练':'学'}.get(plate_type)
        if required_mark and special_mark != required_mark:
            raise InvalidPlateNumberError(plate_type, f"专用简称位置错误，应为{required_mark}")

def validate_new_energy_serial(plate_type: str, plate_category: str, serial_number: str) -> None:
    """验证新能源车牌序号"""
    # 新能源车牌序号长度必须为6位
    if len(serial_number) != 6:
        raise InvalidPlateNumberError(plate_type, "新能源车牌序号长度错误")
    
    # 小型新能源车牌序号规则
    if plate_category == '小型新能源':
        # 第1位必须是字母
        if not serial_number[0].isalpha():
            raise InvalidPlateNumberError(plate_type, "小型新能源序号首位必须是字母")
        
        # 纯电动车：首位为D/A/B/C/E，其他位数字；或首位+次位字母组合
        if serial_number[0] in 'DABCE':
            if serial_number[1].isalpha():
                # 第二位可以是任意字母（除O/I外），其余必须是数字
                if not all(c.isdigit() for c in serial_number[2:]):
                    raise InvalidPlateNumberError(plate_type, "小型新能源序号第3-6位必须是数字")
            else:
                # 第2-6位必须是数字
                if not all(c.isdigit() for c in serial_number[1:]):
                    raise InvalidPlateNumberError(plate_type, "小型新能源序号第2-6位必须是数字")
        # 非纯电动车：首位为F/G/H/J/K，其他位数字；或首位+次位字母组合
        elif serial_number[0] in 'FGHJK':
            if serial_number[1].isalpha():
                # 第二位可以是任意字母（除O/I外），其余必须是数字
                if not all(c.isdigit() for c in serial_number[2:]):
                    raise InvalidPlateNumberError(plate_type, "小型新能源序号第3-6位必须是数字")
            else:
                # 第2-6位必须是数字
                if not all(c.isdigit() for c in serial_number[1:]):
                    raise InvalidPlateNumberError(plate_type, "小型新能源序号第2-6位必须是数字")
        else:
            raise InvalidPlateNumberError(plate_type, "小型新能源车牌首位字母不符合规范")
    
    # 大型新能源车牌规则
    elif plate_category == '大型新能源':
        # 第1-5位必须是数字
        if not all(c.isdigit() for c in serial_number[:5]):
            raise InvalidPlateNumberError(plate_type, "大型新能源车牌前5位必须是数字")
        
        # 第6位必须是字母
        if not serial_number[5].isalpha():
            raise InvalidPlateNumberError(plate_type, "大型新能源车牌第6位必须是字母")
        
        # 纯电动车：第6位为D/A/B/C/E
        # 非纯电动车：第6位为F/G/H/J/K
        if serial_number[5] not in 'DABCEFGHJK':
            raise InvalidPlateNumberError(plate_type, "大型新能源车牌末位字母不符合规范")
        if serial_number[5] in 'OI':
            raise InvalidPlateNumberError(plate_type, "新能源车牌不能使用字母O/I")

def parse_plate_number(plate_type: PlateType, vehicle: VehicleType, number: str) -> ParsedPlateNumber:
    """解析车牌号并返回各组成部分
    
    Args:
        plate_type: 车牌类型：['普通', '大型', '使馆', '领馆']
        vehicle: 适用车型：['汽车', '摩托车', '新能源', '低速车', '轻便摩托车']
        number: 车牌号码
        
    Returns:
        包含车牌各组成部分的字典，根据不同车牌类型返回不同字段：
        - 普通车牌: {province, org_code, serial, [special_mark], plate_full_name}
        - 新能源车牌: {province, org_code, serial, plate_full_name}
        - 使馆车牌: {embassy_code, serial, plate_full_name}
        - 领馆车牌: {province, embassy_code, serial, plate_full_name}
        
    Raises:
        InvalidPlateNumberError: 车牌号格式错误
        ValueError: 不支持的车牌类型或车型组合无效
    """
        
    plate_category = PlateConfig.get_plate_category(plate_type, vehicle)
    pattern = PLATE_REGEX_MAP.get(plate_category)
    
    if not pattern:
        logger.error(f"未知车牌类型: {plate_type}")
        raise ValueError(f"Unsupported plate type: {plate_type}")

    # 执行正则匹配
    match = re.fullmatch(pattern, number, flags=re.UNICODE)
    if not match:
        logger.warning(f"车牌号格式错误: {plate_type} - {number}")
        raise InvalidPlateNumberError(plate_type, number)

    # 提取正则匹配组
    groups = match.groups()

    if len(groups) < 2:
        logger.warning(f"车牌号格式错误: {plate_type} - {number}")
        raise InvalidPlateNumberError(plate_type, number)

    if len(groups) < 3 and (plate_category not in ['使馆汽车', '使馆摩托车', '领馆汽车', '领馆摩托车']):
        logger.warning(f"车牌号格式错误: {plate_type} - {number}")
        raise InvalidPlateNumberError(plate_type, number)
    
    # 处理使馆车牌
    if plate_category in ['使馆汽车', '使馆摩托车']:
        validate_embassy_consulate_serial(plate_type, groups)
        embassy_plate_name: PlateCategoryName = f"使馆{vehicle}号牌"
        embassy_result: EmbassyParsedPlateNumber = {
            'embassy_code': groups[0],
            'serial': groups[1],
            'plate_full_name': embassy_plate_name
        }
        return embassy_result

    if len(groups) < 3:
        logger.warning(f"车牌号格式错误: {plate_type} - {number}")
        raise InvalidPlateNumberError(plate_type, number)
    
    # 处理领馆车牌
    if plate_category in ['领馆汽车', '领馆摩托车']:
        validate_embassy_consulate_serial(plate_type, groups[1:])
        consulate_plate_name: PlateCategoryName = f"领馆{vehicle}号牌"
        consulate_result: ConsulateParsedPlateNumber = {
            'province': groups[0],
            'embassy_code': groups[1],
            'serial': groups[2],
            'plate_full_name': consulate_plate_name
        }
        return consulate_result

    if not groups:
        raise InvalidPlateNumberError(plate_type, "无效的车牌格式")
    
    province_short = groups[0]
    org_code = groups[1] if len(groups)>1 else None  # 发牌机关代号
    special_mark = groups[-1] if len(groups)>3 else None  # 专用简称
    serial_number = groups[2] if len(groups)>2 else None  # 序号

    # 省简称校验
    if province_short:
        valid_provinces = ['京','津','沪','渝','冀','豫','云','辽','黑','湘','皖','鲁','新','苏','浙','赣','鄂','桂','甘','晋','蒙','陕','吉','闽','贵','粤','青','藏','川','宁','琼']
        if province_short not in valid_provinces:
            raise InvalidPlateNumberError(plate_type, f"无效的省简称: {province_short}")

    # 确定车牌全名
    plate_full_name: PlateCategoryName = "小型汽车号牌"  # 默认值
    
    # 处理新能源车牌
    if vehicle == '新能源':
        if plate_type == '大型':
            plate_full_name = "大型新能源汽车号牌"
        elif plate_type == '普通':
            plate_full_name = "小型新能源汽车号牌"
        else:
            raise InvalidVehicleComboError(f"无效的组合: {plate_type}-{vehicle}", vehicle)
            
        # 验证新能源车牌序号
        if org_code and province_short and serial_number:
            # 机关代号校验
            if not org_code.isalpha():
                raise InvalidPlateNumberError(plate_type, "机关代号须为字母组合")
                                
            # 特殊字符校验
            if any(c in number for c in {'O', 'I', 'o', 'i'}):
                raise InvalidPlateNumberError(plate_type, "包含禁用字母O/I")
                
            validate_new_energy_serial(plate_type, plate_category, serial_number)
            new_energy_result: NewEnergyParsedPlateNumber = {
                'province': province_short,
                'org_code': org_code,
                'serial': serial_number,
                'plate_full_name': plate_full_name
            }
            return new_energy_result
        else:
            raise InvalidPlateNumberError(plate_type, "无效的车牌格式")
    
    # 处理普通车牌和大型车牌
    if plate_type == '普通':
        if vehicle == '汽车':
            # 检查是否有专用简称
            if special_mark:
                if special_mark == '警':
                    plate_full_name = "警用汽车号牌"
                elif special_mark == '学':
                    plate_full_name = "教练汽车号牌"
                elif special_mark == '港' or special_mark == '澳':
                    plate_full_name = "港澳入出境车号牌"
                else:
                    plate_full_name = "小型汽车号牌"
            else:
                plate_full_name = "小型汽车号牌"
        elif vehicle == '摩托车':
            if special_mark and special_mark == '警':
                plate_full_name = "警用摩托车号牌"
            else:
                plate_full_name = "普通摩托车号牌"
        elif vehicle == '轻便摩托车':
            plate_full_name = "轻便摩托车号牌"
        elif vehicle == '低速车':
            plate_full_name = "低速车号牌"
        else:
            plate_full_name = "小型汽车号牌"
    
    elif plate_type == '大型':
        if vehicle == '汽车':
            if special_mark:
                if special_mark == '挂':
                    plate_full_name = "挂车号牌"
                else:
                    plate_full_name = "大型汽车前号牌"
            else:
                plate_full_name = "大型汽车前号牌"
    
    # 标准车牌格式校验
    if org_code and province_short and serial_number:
        # 原有机关代号校验
        if not org_code.isalpha():
            raise InvalidPlateNumberError(plate_type, "机关代号须为字母组合")
                            
        # 特殊字符校验
        if any(c in number for c in {'O', 'I', 'o', 'i'}):
            raise InvalidPlateNumberError(plate_type, "包含禁用字母O/I")
            
        # 根据车牌类型验证序号
        if plate_category == '普通':
            validate_normal_serial(plate_type, groups, special_mark)
            normal_result: NormalParsedPlateNumber = {
                'province': province_short,
                'org_code': org_code,
                'serial': serial_number,
                'plate_full_name': plate_full_name,
                'special_mark': None
            }
            if special_mark:
                normal_result['special_mark'] = special_mark
            return normal_result
    else:
        raise InvalidPlateNumberError(plate_type, "无效的车牌格式")

    # 如果没有匹配任何类型，抛出异常
    raise InvalidPlateNumberError(plate_type, "无效的车牌格式")


def validate_serial_pattern(serial: str, enabled_rules: list) -> bool:
    """
    校验序号部分是否符合GA36-2018标准字母位置组合规则
    :param serial: 需要校验的序号段（4或5位）
    :param enabled_rules: 当前序号长度下启用的规则编号列表
    :return: 是否符合任意一个启用规则
    规则说明（数字位置从0开始计数）：
     1. 全数字
     2. 第1位字母
     3. 第1-2位字母
     4. 第2位字母
     5. 第3位字母
     6. 第4位字母
     7. 第5位字母（仅5位序号）
     8. 第1和5位字母
     9. 第4和5位字母
    10. 第1和3位字母
    11. 第2和3位字母
    12. 第1和4位字母
    13. 第2和4位字母
    14. 第2和5位字母
    15. 第3和4位字母
    16. 第3和5位字母
    """

    # 字母位置映射表（规则编号 -> 字母位置索引列表）
    # 四位序号禁用规则：7,8,9,14,16
    rule_patterns = {
        1: [],   # 全数字
        2: [0],  # 第1位字母
        3: [0,1],# 第1-2位字母
        4: [1],  # 第2位字母
        5: [2],  # 第3位字母
        6: [3],  # 第4位字母
        7: [4],  # 第5位字母（仅5位序号）
        8: [0,4],
        9: [3,4],
        10: [0,2],
        11: [1,2],
        12: [0,3],
        13: [1,3],
        14: [1,4],
        15: [2,3],
        16: [2,4]
    }

    # 验证序号长度
    if len(serial) not in (4,5):
        raise ValueError("序号长度必须为4或5位")

    for rule in enabled_rules:
        # 检查规则有效性
        if rule not in rule_patterns or rule <1 or rule >16:
            raise ValueError(f"无效规则编号: {rule}")

        letter_positions = rule_patterns[rule]
        valid = True
        
        # 检查字母位置是否超出序号长度范围
        max_pos = 4 if len(serial)==5 else 3
        if any(pos > max_pos for pos in letter_positions):
            continue

        for idx in range(len(serial)):
            char = serial[idx]
            if idx in letter_positions:
                if not char.isalpha() or char in {'O','I'}:
                    valid = False
                    break
            else:
                if not char.isdigit():
                    valid = False
                    break
        
        if valid:
            return True
    
    return False