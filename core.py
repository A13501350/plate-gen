import svgutils.transform as sg
import re
from pathlib import Path
from typing import Tuple, List, Dict, Optional, Union, cast
import logging
import json
import os
from plate_config import PlateConfig, PlateType, VehicleType, CharPositionDict
from exceptions import InvalidPlateNumberError
from plate_validator import parse_plate_number
from plate_types import NewEnergyParsedPlateNumber, ParsedPlateNumber, EmbassyParsedPlateNumber, ConsulateParsedPlateNumber, NormalParsedPlateNumber

from exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)

# 默认资源目录路径
DEFAULT_RESOURCES_DIR = Path(__file__).parent / 'resources'

class PlateGenerator:
    """车牌生成核心类

    Attributes:
        resource_dir (Path): SVG资源文件存储路径
    
    Methods:
        __init__: 初始化资源目录
        generate: 生成车牌SVG图像
    """
    

    def __init__(self, resource_dir=None):
        """初始化资源目录路径

        Args:
            resource_dir (str, optional): 资源目录路径，优先级低于环境变量PLATE_RESOURCES_DIR
        
        Raises:
            ResourceNotFoundError: 当资源目录不存在时抛出
        """
        # 优先使用环境变量指定的路径
        env_path = os.getenv('PLATE_RESOURCES_DIR')
        if env_path:
            self.resource_dir = Path(env_path)
        elif resource_dir:
            self.resource_dir = Path(resource_dir)
        else:
            self.resource_dir = DEFAULT_RESOURCES_DIR
            
        if not self.resource_dir.exists():
            raise ResourceNotFoundError(str(self.resource_dir))


    def _get_plate_config(self, parsed_number: ParsedPlateNumber) -> tuple[PlateConfig, Path, Path]:
        """获取车牌配置信息
        
        Args:
            parsed_number: 解析后的车牌号码信息字典
            
        Returns:
            tuple: (config, bg_file, font_dir, coord) 配置对象、背景文件路径、字体目录路径、坐标配置
            
        Raises:
            ResourceNotFoundError: 资源文件缺失时抛出
            ValueError: 配置错误时抛出
        """
        # 获取车牌配置
        config = PlateConfig.get_config_by_full_name(parsed_number['plate_full_name'])

        # 提取配置信息
        size = config.size
        bg_type = config.background_path.stem
        
        # 加载背景模板
        bg_file = self.resource_dir / config.background_path
        if not bg_file.exists():
            raise ResourceNotFoundError(str(bg_file))
        
        # 获取字体目录
        font_dir = self.resource_dir / config.font_path
        if not font_dir.exists():
            raise ResourceNotFoundError(str(font_dir))
            
        return config, bg_file, font_dir
    
    def _prepare_background(self, plate_full_name: str, config: PlateConfig, bg_file: Path) -> sg.SVGFigure:
        """准备车牌背景
        
        Args:
            config: 车牌配置对象
            bg_file: 背景文件路径
            
        Returns:
            SVGFigure: 处理后的背景SVG对象
        """
        # 使用svg_utils加载和处理SVG
        from utils.svg_utils import load_svg, set_rect_color, set_border_and_separator_color
        
        # 特殊处理新能源车牌
        if '新能源' in plate_full_name:
            # 根据车型选择对应的预制背景
            if '大型' in plate_full_name:
                # 大型新能源车牌使用Track.svg
                prebuilt_bg_file = self.resource_dir / 'backgrounds' / '480×140' / 'Track.svg'
            else:
                # 小型新能源车牌使用Car.svg
                prebuilt_bg_file = self.resource_dir / 'backgrounds' / '480×140' / 'Car.svg'
                
            # 检查预制背景文件是否存在
            if not prebuilt_bg_file.exists():
                logger.warning(f"预制新能源背景文件不存在: {prebuilt_bg_file}，将使用默认背景")
            else:
                logger.info(f"使用预制新能源背景: {prebuilt_bg_file}")
                return load_svg(prebuilt_bg_file)
        
        # 非新能源车牌或预制背景不存在时，使用原有逻辑处理
        background = load_svg(bg_file)
        
        # 获取颜色配置
        fill_color = config.colors.get('background')
        font_color = config.colors.get('text')
        
        # 动态填充背景色
        if fill_color is not None:
            background = set_rect_color(background, fill_color)
        else:
            logger.warning(f"未找到背景颜色配置，将使用默认颜色")
            background = set_rect_color(background, '#223F99')
        
        # 更新边框和分隔符颜色
        if font_color is not None:
            background = set_border_and_separator_color(background, font_color)
        else:
            logger.warning(f"未找到字体颜色配置，将使用默认颜色")
            background = set_border_and_separator_color(background, '#FFFFFF')
        
        # 获取并设置间隔符位置
        if 'separator' in config.char_positions:
            from utils.svg_utils import set_separator_position
            background = set_separator_position(background, config.char_positions['separator'])
        else:
            logger.warning(f"未找到间隔符位置配置")
            
        return background
    
    def _fill_plate_characters(self, plate_type: PlateType, parsed_number: ParsedPlateNumber, font_dir: Path, config: PlateConfig) -> list:
        """填充车牌字符
        
        Args:
            parsed_number: 解析后的车牌号码信息字典
            font_dir: 字体目录路径
            coord: 坐标配置字典
            
        Returns:
            list: SVG元素列表
            
        Raises:
            ResourceNotFoundError: 资源文件缺失时抛出
            ValueError: 配置错误时抛出
        """
        elements = []
        plate_category = parsed_number['plate_full_name']
        coord = config.char_positions
        
        # 获取文字颜色配置
        font_color = config.colors.get('text')
        if font_color is None:
            logger.warning("未找到文字颜色配置，将使用默认颜色")
            font_color = '#FFFFFF'
            
        # 导入SVG工具函数
        from utils.svg_utils import set_path_color

        
        # 使馆车牌处理
        if '使馆' in plate_category:
            # 使馆车牌格式: {embassy_code, serial}
            parsed_number = cast(EmbassyParsedPlateNumber, parsed_number)
            embassy_code = parsed_number['embassy_code']
            serial = parsed_number['serial']
            
            # 添加使馆代码
            for i, digit in enumerate(embassy_code):
                char_svg = font_dir / f"{digit}.svg"
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                
                if 'embassy_code' not in coord or i >= len(coord['embassy_code']):
                    logger.warning(f"使馆代码位置配置不足，索引{i}超出范围")
                    break
                    
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['embassy_code'][i])
                elements.append(char_element)
            
            # 添加序列号
            for i, digit in enumerate(serial):
                char_svg = font_dir / f"{digit}.svg"
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                
                if 'embassy_serial' not in coord or i >= len(coord['embassy_serial']):
                    logger.warning(f"使馆序列号位置配置不足，索引{i}超出范围")
                    break
                    
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['embassy_serial'][i])
                elements.append(char_element)
            
            # 添加"使"字符
            if '使' in parsed_number['plate_full_name']:
                char_svg = font_dir / "使.svg"
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['special_mark'])
                elements.append(char_element)
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                else:
                    logger.warning("使馆车牌后缀'使'字符位置未配置")
        
        # 领馆车牌处理
        elif '领馆' in plate_category and '号牌' in plate_category:
            # 领馆车牌格式: {province, embassy_code, serial}
            parsed_number = cast(ConsulateParsedPlateNumber, parsed_number)
            province = parsed_number['province']
            embassy_code = parsed_number['embassy_code']
            serial = parsed_number['serial']
            
            # 添加省份字符
            province_svg = font_dir / f"{province}.svg"
            if not province_svg.exists():
                raise ResourceNotFoundError(str(province_svg))
            
            if 'province' in coord:
                province_char = sg.fromfile(str(province_svg)).getroot()
                province_char.moveto(*coord['province'])
                elements.append(province_char)
            else:
                logger.warning("领馆车牌省份字符位置未配置")
            
            # 添加"领"字符
            if '领' in parsed_number['plate_full_name']:
                char_svg = font_dir / "领.svg"
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['special_mark'])
                elements.append(char_element)
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                
                else:
                    logger.warning("领馆车牌前缀'领'字符位置未配置")
            
            # 添加使馆代码
            for i, digit in enumerate(embassy_code):
                char_svg = font_dir / f"{digit}.svg"
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                
                if 'diplomatic' not in coord or i >= len(coord['diplomatic']):
                    logger.warning(f"领馆代码位置配置不足，索引{i}超出范围")
                    break
                    
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['diplomatic'][i])
                elements.append(char_element)
            
            # 添加序列号
            for i, digit in enumerate(serial):
                char_svg = font_dir / f"{digit}.svg"
                if not char_svg.exists():
                    raise ResourceNotFoundError(str(char_svg))
                
                if 'digits' not in coord or i >= len(coord['digits']):
                    logger.warning(f"领馆序列号位置配置不足，索引{i}超出范围")
                    break
                    
                char_element = set_path_color(sg.fromfile(str(char_svg)), font_color).getroot()
                char_element.moveto(*coord['digits'][i])
                elements.append(char_element)
        
        # 普通车牌处理
        elif plate_type == '普通':
            # 普通车牌格式: {province, org_code, serial, special_mark}
            parsed_number = cast(NormalParsedPlateNumber, parsed_number)
            province = parsed_number['province']
            org_code = parsed_number['org_code']
            serial = parsed_number['serial']
            special_mark = parsed_number.get('special_mark', None)
            
            # 添加省份字符
            province_svg = font_dir / f"{province}.svg"
            if not province_svg.exists():
                raise ResourceNotFoundError(str(province_svg))
            
            province_char = set_path_color(sg.fromfile(str(province_svg)), font_color).getroot()
            province_char.moveto(*coord['province'])
            elements.append(province_char)
            
            # 添加字母（发牌机关代号）
            letter_svg = font_dir / f"{org_code}.svg"
            if not letter_svg.exists():
                raise ResourceNotFoundError(str(letter_svg))
            
            letter_char = set_path_color(sg.fromfile(str(letter_svg)), font_color).getroot()
            letter_char.moveto(*coord['letter'])
            elements.append(letter_char)
            
            # 添加序列号
            for i, digit in enumerate(serial):
                digit_svg = font_dir / f"{digit}.svg"
                if not digit_svg.exists():
                    raise ResourceNotFoundError(str(digit_svg))
                
                # 确保索引在有效范围内
                if i >= len(coord['digits']):
                    logger.warning(f"字符位置配置不足，索引{i}超出范围")
                    break
                    
                digit_char = set_path_color(sg.fromfile(str(digit_svg)), font_color).getroot()
                digit_char.moveto(*coord['digits'][i])
                elements.append(digit_char)
            
            # 添加专用标记（如警、学等）
            if special_mark:
                mark_svg = font_dir / f"{special_mark}.svg"
                if not mark_svg.exists():
                    raise ResourceNotFoundError(str(mark_svg))
                
                if 'special_mark' in coord:
                    mark_char = set_path_color(sg.fromfile(str(mark_svg)), font_color).getroot()
                    mark_char.moveto(*coord['special_mark'])
                    elements.append(mark_char)
                else:
                    logger.warning(f"专用标记'{special_mark}'位置未配置")
        
        # 新能源车牌处理
        elif '新能源' in plate_category:
            # 新能源车牌格式: {province, org_code, serial}
            parsed_number = cast(NewEnergyParsedPlateNumber, parsed_number)
            province = parsed_number['province']
            org_code = parsed_number['org_code']
            serial = parsed_number['serial']
            
            # 添加省份字符
            province_svg = font_dir / f"{province}.svg"
            if not province_svg.exists():
                raise ResourceNotFoundError(str(province_svg))
            
            province_char = set_path_color(sg.fromfile(str(province_svg)), font_color).getroot()
            province_char.moveto(*coord['province'])
            elements.append(province_char)
            
            # 添加字母（发牌机关代号）
            letter_svg = font_dir / f"{org_code}.svg"
            if not letter_svg.exists():
                raise ResourceNotFoundError(str(letter_svg))
            
            letter_char = set_path_color(sg.fromfile(str(letter_svg)), font_color).getroot()
            letter_char.moveto(*coord['letter'])
            elements.append(letter_char)
            
            # 添加序列号（新能源车牌序列号可能有6位）
            for i, digit in enumerate(serial):
                digit_svg = font_dir / f"{digit}.svg"
                if not digit_svg.exists():
                    raise ResourceNotFoundError(str(digit_svg))
                
                # 确保索引在有效范围内
                position_key = 'new_energy_digits' if 'new_energy_digits' in coord else 'digits'
                if i >= len(coord[position_key]):
                    logger.warning(f"字符位置配置不足，索引{i}超出范围")
                    break
                    
                digit_char = set_path_color(sg.fromfile(str(digit_svg)), font_color).getroot()
                digit_char.moveto(*coord[position_key][i])
                elements.append(digit_char)
        
        # 其他未明确处理的车牌类型
        else:
            logger.warning(f"未实现的车牌类型处理: {plate_category}")
            raise ValueError(f"未实现的车牌类型处理: {plate_category}")
            
        return elements
    
    def generate(self, plate_type: PlateType, vehicle: VehicleType, number: str) -> sg.SVGFigure:
        """生成车牌SVG图像

        Args:
            plate_type (str): 车牌类型（'普通','使馆','领馆', '新能源'）
            vehicle (str): 车型（'汽车', '摩托车', '新能源', '低速车', '轻便摩托车'）
            number (str): 符合格式规范的车牌号码

        Returns:
            svgutils.transform.SVGFigure: 生成的车牌SVG对象

        Raises:
            InvalidPlateNumberError: 车牌号格式验证失败时抛出
            ResourceNotFoundError: 资源文件缺失时抛出
            ValueError: 配置错误或无效的车牌类型与车型组合
        """

        # 解析车牌号，返回类型化字典
        parsed_number = parse_plate_number(plate_type, vehicle, number)
        if not parsed_number:
            raise InvalidPlateNumberError(plate_type, number)
            
        try:
            # 1. 获取配置
            config, bg_file, font_dir = self._get_plate_config(parsed_number)
            
            # 2. 准备背景
            background = self._prepare_background(parsed_number["plate_full_name"],config, bg_file)
            
            # 3. 填充车牌字符
            elements = self._fill_plate_characters(plate_type, parsed_number, font_dir, config)
            
            # 合并所有元素
            background.append(elements)
            return background
            
        except FileNotFoundError as e:
            logger.critical(f"关键资源文件缺失: {e}")
            raise ResourceNotFoundError(str(e)) from e
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            raise
        except Exception as e:
            logger.exception(f"生成车牌时发生未知错误: {e}")
            raise