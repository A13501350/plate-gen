from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional, Union, TypedDict, Literal
from pathlib import Path
import logging
from exceptions import InvalidVehicleComboError
from plate_types import PlateType, VehicleType, CharPositionDict

logger = logging.getLogger(__name__)

@dataclass
class PlateConfig:
    """车牌配置类
    
    用于存储车牌的配置信息，包括尺寸、字体、背景图片、颜色等。
    提供了车牌类型验证、配置加载等功能。
    
    Attributes:
        size: 车牌尺寸，格式为(宽, 高)，单位为像素
        font_path: 字体文件路径，用于渲染车牌文字
        background_path: 背景图片路径，用于车牌底板
        colors: 颜色配置，键为颜色名称(如'background', 'text')，值为颜色代码(如'#223F99')
        char_positions: 字符位置信息，用于确定车牌上每个字符的位置
    """
    size: Tuple[int, int]
    font_path: Path
    background_path: Path
    colors: Dict[str, str]
    char_positions: CharPositionDict


    @classmethod
    def get_plate_category(cls, plate_type: PlateType, vehicle: VehicleType) -> str:
        """根据车牌类型和车辆类型获取分类
        
        根据输入的车牌类型和车辆类型，返回对应的车牌分类名称，用于后续配置查找。
        不同的组合会产生不同的分类结果，部分组合可能无效。
        
        Args:
            plate_type: 车牌类型，必须是以下值之一：'普通', '大型', '使馆', '领馆'
            vehicle: 车辆类型，必须是以下值之一：'汽车', '摩托车', '新能源', '低速车', '轻便摩托车'
            
        Returns:
            str: 车牌分类名称，如'领馆汽车'、'使馆汽车'、'大型新能源'、'小型新能源'等
            
        Raises:
            ValueError: 当车牌类型或车辆类型未识别时抛出
            InvalidVehicleComboError: 当车牌类型与车辆类型组合无效时抛出，例如'使馆-新能源'组合
        """
        # 定义有效的车牌类型和车辆类型
        valid_plate_types = ['普通', '大型', '使馆', '领馆']
        valid_vehicles = ['汽车', '摩托车', '新能源', '低速车', '轻便摩托车']
        
        # 验证输入参数
        if plate_type not in valid_plate_types:
            raise ValueError(f"未识别的车牌类型: {plate_type}")
        if vehicle not in valid_vehicles:
            raise ValueError(f"未识别的车辆类型: {vehicle}")
            
        # 根据不同组合返回分类名称
        if plate_type in ['使馆', '领馆']:
            if vehicle in ['汽车', '摩托车']:
                return f"{plate_type}{vehicle}"
            else:
                raise InvalidVehicleComboError(f"无效的组合: {plate_type}-{vehicle}", vehicle)
        elif vehicle == '新能源':
            if plate_type == '大型':
                return '大型新能源'
            elif plate_type == '普通':
                return '小型新能源'
            else:
                raise InvalidVehicleComboError(f"无效的组合: {plate_type}-{vehicle}", vehicle)
        elif plate_type == '大型':
            return '普通'
        else:
            return f"{plate_type}"
    
    @classmethod
    def get_config_by_full_name(cls, plate_full_name: str) -> 'PlateConfig':
        """根据车牌全名获取对应的配置
        
        通过车牌全名查找匹配的配置。首先尝试精确匹配，
        如果找不到则使用模糊匹配规则查找最接近的配置。
        
        Args:
            plate_full_name: 车牌全名，如"小型汽车号牌"、"大型新能源汽车号牌"等
            
        Returns:
            PlateConfig: 对应的车牌配置对象
            
        Raises:
            KeyError: 当提供的车牌类型不存在时抛出
        """
        from resources.plate_configs import PLATE_CONFIG_MAP
        
        try:
            return PLATE_CONFIG_MAP[plate_full_name]
        except KeyError:
            raise KeyError(f"未找到车牌类型: {plate_full_name}")
        