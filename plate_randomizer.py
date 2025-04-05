import random
from typing import Dict, List, Tuple, Optional

# 省份简称列表
PROVINCES = [
    '京', '沪', '津', '渝', '冀', '晋', '蒙', '辽', '吉', '黑',
    '苏', '浙', '皖', '闽', '赣', '鲁', '豫', '鄂', '湘', '粤',
    '桂', '琼', '川', '贵', '云', '藏', '陕', '甘', '青', '宁', '新'
]

# 字母集合（排除I、O）
LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'

# 新能源车牌字母
NEW_ENERGY_PURE_ELECTRIC = 'DABCE'  # 纯电动车
NEW_ENERGY_NON_ELECTRIC = 'FGHJK'   # 非纯电动车

class PlateRandomizer:
    """车牌号码随机生成器
    
    根据GA36-2018标准生成符合规范的车牌号码
    
    Attributes:
        config (Dict): 生成规则配置
    """
    
    # 字母位置规则映射表（规则编号 -> 字母位置索引列表）
    LETTER_POSITION_RULES = {
        1: [],     # 全数字
        2: [0],    # 第1位字母
        3: [0,1],  # 第1-2位字母
        4: [1],    # 第2位字母
        5: [2],    # 第3位字母
        6: [3],    # 第4位字母
        7: [4],    # 第5位字母（仅5位序号）
        8: [0,4],  # 第1、5位字母
        9: [3,4],  # 第4、5位字母
        10: [0,2], # 第1、3位字母
        11: [1,2], # 第2、3位字母
        12: [0,3], # 第1、4位字母
        13: [1,3], # 第2、4位字母
        14: [1,4], # 第2、5位字母
        15: [2,3], # 第3、4位字母
        16: [2,4]  # 第3、5位字母
    }
    
    # 不同序号长度下启用的规则
    ENABLED_RULES = {
        4: [1,2,3,4,5,6,10,11,12,13,15],  # 4位序号启用的规则
        5: list(range(1,17))                # 5位序号启用的规则
    }
    
    RULES: Dict[str, Dict] = {
        'blue': {
            'province_weights': [10]*31,
            'pattern': [
                ('province', 1),
                ('letter', 1),
                ('serial', 5)  # 5位序号，符合字母位置组合规则
            ]
        },
        'green_small': {  # 小型新能源
            'province_weights': [15 if p in ['京', '沪', '粤'] else 10 for p in PROVINCES],
            'pattern': [
                ('province', 1),
                ('letter', 1),
                ('serial', 6)  # 6位序号，首位必须是字母
            ]
        },
        'green_large': {  # 大型新能源
            'province_weights': [15 if p in ['京', '沪', '粤'] else 10 for p in PROVINCES],
            'pattern': [
                ('province', 1),
                ('letter', 1),
                ('serial', 6)  # 6位序号，前5位数字，末位字母
            ]
        }
    }

    def __init__(self):
        """初始化随机生成规则"""
        self.config = self.RULES.copy()

    def _generate_serial_by_rule(self, length: int) -> str:
        """根据字母位置组合规则生成序号
        
        Args:
            length: 序号长度，4或5位
            
        Returns:
            符合规则的序号字符串
        """
        if length not in (4, 5):
            raise ValueError(f"序号长度必须为4或5位，当前: {length}")
        
        # 随机选择一个启用的规则
        rule_id = random.choice(self.ENABLED_RULES[length])
        letter_positions = self.LETTER_POSITION_RULES[rule_id]
        
        # 生成序号
        serial = [''] * length
        for i in range(length):
            if i in letter_positions:
                serial[i] = random.choice(LETTERS)
            else:
                serial[i] = str(random.randint(0, 9))
        
        return ''.join(serial)

    def random_blue(self) -> str:
        """生成蓝牌号码
        
        Returns:
            符合GA36-2018标准的蓝牌号码
        """
        # 随机选择省份和发牌机关代号
        province = random.choices(PROVINCES, weights=self.config['blue']['province_weights'])[0]
        org_code = random.choice(LETTERS)
        
        # 随机决定序号长度（4位或5位）
        serial_length = random.choice([4, 5])
        serial = self._generate_serial_by_rule(serial_length)
        
        # 组合车牌号
        return f"{province}{org_code}{serial}"

    def random_green_small(self) -> str:
        """生成小型新能源车牌号码
        
        Returns:
            符合GA36-2018标准的小型新能源车牌号码
        """
        # 随机选择省份和发牌机关代号
        province = random.choices(
            PROVINCES, 
            weights=self.config['green_small']['province_weights']
        )[0]
        org_code = random.choice(LETTERS)
        
        # 随机决定是纯电动还是非纯电动
        is_pure_electric = random.choice([True, False])
        first_letter = random.choice(NEW_ENERGY_PURE_ELECTRIC if is_pure_electric else NEW_ENERGY_NON_ELECTRIC)
        
        # 随机决定是否使用双字母模式
        use_double_letter = random.choice([True, False])
        
        if use_double_letter:
            # 第二位也是字母
            second_letter = random.choice(LETTERS)
            # 剩余4位是数字
            remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(4))
            serial = f"{first_letter}{second_letter}{remaining_digits}"
        else:
            # 全部5位都是数字
            digits = ''.join(str(random.randint(0, 9)) for _ in range(5))
            serial = f"{first_letter}{digits}"
        
        return f"{province}{org_code}{serial}"

    def random_green_large(self) -> str:
        """生成大型新能源车牌号码
        
        Returns:
            符合GA36-2018标准的大型新能源车牌号码
        """
        # 随机选择省份和发牌机关代号
        province = random.choices(
            PROVINCES, 
            weights=self.config['green_large']['province_weights']
        )[0]
        org_code = random.choice(LETTERS)
        
        # 随机决定是纯电动还是非纯电动
        is_pure_electric = random.choice([True, False])
        last_letter = random.choice(NEW_ENERGY_PURE_ELECTRIC if is_pure_electric else NEW_ENERGY_NON_ELECTRIC)
        
        # 前5位是数字
        digits = ''.join(str(random.randint(0, 9)) for _ in range(5))
        
        return f"{province}{org_code}{digits}{last_letter}"

    def random_green(self, is_small: Optional[bool] = None) -> str:
        """生成新能源车牌号码
        
        Args:
            is_small: 是否生成小型新能源车牌，None表示随机选择
            
        Returns:
            符合GA36-2018标准的新能源车牌号码
        """
        if is_small is None:
            is_small = random.choice([True, False])
            
        if is_small:
            return self.random_green_small()
        else:
            return self.random_green_large()

    @staticmethod
    def generate(plate_type: str, count: int = 1) -> List[str]:
        """批量生成车牌号码
        
        Args:
            plate_type: 车牌类型，支持'blue'(蓝牌)、'green'(新能源)、
                       'green_small'(小型新能源)、'green_large'(大型新能源)
            count: 生成数量
            
        Returns:
            车牌号码列表
        
        Raises:
            ValueError: 不支持的车牌类型
        """
        generator = PlateRandomizer()
        results = []
        
        for _ in range(count):
            if plate_type == 'blue':
                results.append(generator.random_blue())
            elif plate_type == 'green':
                results.append(generator.random_green())
            elif plate_type == 'green_small':
                results.append(generator.random_green_small())
            elif plate_type == 'green_large':
                results.append(generator.random_green_large())
            else:
                raise ValueError(f"不支持的车牌类型: {plate_type}")
        
        return results