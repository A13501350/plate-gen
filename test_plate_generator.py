#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试车牌生成器

验证PlateGenerator类是否能正确生成符合GA36-2018标准的车牌SVG图像
"""

import pytest
from pathlib import Path
import os
import svgutils.transform as sg
from core import PlateGenerator, ResourceNotFoundError
from exceptions import InvalidPlateNumberError
from plate_validator import parse_plate_number
from unittest.mock import patch, MagicMock

# 测试资源目录路径
TEST_RESOURCES_DIR = Path(__file__).parent / 'resources'


class TestPlateGeneratorInit:
    """测试PlateGenerator初始化功能"""
    
    def test_init_with_default_resources(self):
        """测试使用默认资源目录初始化"""
        generator = PlateGenerator()
        assert generator.resource_dir == Path(__file__).parent / 'resources'
        assert generator.resource_dir.exists()
    
    def test_init_with_custom_resources(self):
        """测试使用自定义资源目录初始化"""
        generator = PlateGenerator(TEST_RESOURCES_DIR)
        assert generator.resource_dir == TEST_RESOURCES_DIR
    
    def test_init_with_env_variable(self, monkeypatch):
        """测试使用环境变量指定资源目录"""
        test_path = str(TEST_RESOURCES_DIR)
        monkeypatch.setenv('PLATE_RESOURCES_DIR', test_path)
        generator = PlateGenerator()
        assert generator.resource_dir == Path(test_path)
    
    def test_init_with_nonexistent_resources(self):
        """测试使用不存在的资源目录初始化应抛出异常"""
        with pytest.raises(ResourceNotFoundError):
            PlateGenerator('nonexistent_dir')


class TestPlateGeneratorGenerate:
    """测试PlateGenerator生成功能"""
    
    @pytest.fixture
    def generator(self):
        """创建测试用的生成器实例"""
        return PlateGenerator()
    
    def test_generate_ordinary_car_plate(self, generator):
        """测试生成普通小型汽车车牌"""
        svg = generator.generate('普通', '汽车', '京A12345')
        assert isinstance(svg, sg.SVGFigure)
        # 验证SVG尺寸
        width, height = svg.get_size()
        assert float(width) > 0
        assert float(height) > 0
        
        # 验证颜色是否正确应用
        root = svg.root
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        
        # 检查背景颜色
        background = root.xpath("//svg:rect[@id='background']", namespaces=namespaces)
        assert background, "未找到背景元素"
        assert background[0].get("fill") == "#223F99", "背景颜色不正确"
        
        # 检查边框和分隔符颜色
        border = root.xpath("//svg:rect[@id='border']", namespaces=namespaces)
        assert border, "未找到边框元素"
        assert border[0].get("stroke") == "white", "边框颜色不正确"
        
        separator = root.xpath("//svg:circle[@id='separator']", namespaces=namespaces)
        assert separator, "未找到分隔符元素"
        assert separator[0].get("fill") == "white", "分隔符颜色不正确"
    
    def test_generate_ordinary_motorcycle_plate(self, generator):
        """测试生成普通摩托车车牌"""
        svg = generator.generate('普通', '摩托车', '京A1234')
        assert isinstance(svg, sg.SVGFigure)
        
        # 验证颜色是否正确应用
        root = svg.root
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        
        # 检查背景颜色
        background = root.xpath("//svg:rect[@id='background']", namespaces=namespaces)
        assert background, "未找到背景元素"
        assert background[0].get("fill") == "#FFC210", "背景颜色不正确"
        
        # 检查边框和分隔符颜色
        border = root.xpath("//svg:rect[@id='border']", namespaces=namespaces)
        assert border, "未找到边框元素"
        assert border[0].get("stroke") == "black", "边框颜色不正确"
    
    def test_generate_new_energy_plate(self, generator):
        """测试生成新能源车牌"""
        svg = generator.generate('普通', '新能源', '京AD12345')
        assert isinstance(svg, sg.SVGFigure)
        
    def test_generate_embassy_plate(self, generator):
        """测试生成使馆车牌"""
        svg = generator.generate('使馆', '汽车', '123456使')
        assert isinstance(svg, sg.SVGFigure)
        
        # 验证颜色是否正确应用
        root = svg.root
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        
        # 检查背景颜色 - 使馆车牌应该是黑色
        background = root.xpath("//svg:rect[@id='background']", namespaces=namespaces)
        assert background, "未找到背景元素"
        assert background[0].get("fill") == "black", "使馆车牌背景颜色不正确"
        
        # 检查边框和分隔符颜色 - 应该是白色
        border = root.xpath("//svg:rect[@id='border']", namespaces=namespaces)
        assert border, "未找到边框元素"
        assert border[0].get("stroke") == "white", "使馆车牌边框颜色不正确"
    
    def test_generate_consulate_plate(self, generator):
        """测试生成领馆车牌"""
        svg = generator.generate('领馆', '汽车', '粤12346领')
        assert isinstance(svg, sg.SVGFigure)
        
        # 验证颜色是否正确应用
        root = svg.root
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        
        # 检查背景颜色 - 领馆车牌应该是黑色
        background = root.xpath("//svg:rect[@id='background']", namespaces=namespaces)
        assert background, "未找到背景元素"
        assert background[0].get("fill") == "black", "领馆车牌背景颜色不正确"
        
        # 检查边框和分隔符颜色 - 应该是白色
        border = root.xpath("//svg:rect[@id='border']", namespaces=namespaces)
        assert border, "未找到边框元素"
        assert border[0].get("stroke") == "white", "领馆车牌边框颜色不正确"
    
    def test_invalid_plate_number(self, generator):
        """测试无效车牌号应抛出异常"""
        with pytest.raises(InvalidPlateNumberError):
            generator.generate('普通', '汽车', '京O1234')  # O是禁用字母
    
    def test_invalid_plate_type_vehicle_combo(self, generator):
        """测试无效的车牌类型与车型组合应抛出异常"""
        with pytest.raises(ValueError):
            generator.generate('使馆', '新能源', '123456使')


class TestPlateGeneratorInternalMethods:
    """测试PlateGenerator内部方法"""
    
    @pytest.fixture
    def generator(self):
        return PlateGenerator()
    
    def test_get_plate_config(self, generator):
        """测试获取车牌配置"""
        # 使用实际的parse_plate_number函数解析车牌号
        parsed_number = parse_plate_number('普通', '汽车', '京A12345')
        config, bg_file, font_dir = generator._get_plate_config(parsed_number)
        assert config is not None
        assert bg_file.exists()
        assert font_dir.exists()
    
    def test_prepare_background(self, generator):
        """测试准备背景"""
        # 使用实际的parse_plate_number函数解析车牌号
        parsed_number = parse_plate_number('普通', '汽车', '京A12345')
        config, bg_file, font_dir = generator._get_plate_config(parsed_number)
        
        # 测试普通车牌背景
        background = generator._prepare_background(parsed_number['plate_full_name'], config, bg_file)
        assert isinstance(background, sg.SVGFigure)
        
        # 测试新能源车牌背景
        parsed_new_energy = parse_plate_number('普通', '新能源', '京AD12345')
        config_ne, bg_file_ne, _ = generator._get_plate_config(parsed_new_energy)
        background_ne = generator._prepare_background(parsed_new_energy['plate_full_name'], config_ne, bg_file_ne)
        assert isinstance(background_ne, sg.SVGFigure)
    
    def test_fill_plate_characters(self, generator):
        """测试填充车牌字符"""
        # 使用实际的parse_plate_number函数解析车牌号
        parsed_number = parse_plate_number('普通', '汽车', '京A12345')
        
        # 获取配置信息
        config, bg_file, font_dir = generator._get_plate_config(parsed_number)
        
        # 测试填充字符
        elements = generator._fill_plate_characters('普通', parsed_number, font_dir, config)
        assert isinstance(elements, list)
        assert len(elements) > 0
    
    def test_resource_not_found(self, generator):
        """测试资源文件缺失异常"""
        with patch('pathlib.Path.exists', return_value=False):
            parsed_number = {
                'plate_full_name': '小型汽车号牌',
                'province': '京',
                'org_code': 'A',
                'serial': '12345',
                'original_number': '京A12345'
            }
            with pytest.raises(ResourceNotFoundError):
                generator._get_plate_config(parsed_number)


if __name__ == '__main__':
    pytest.main(['-v', 'test_plate_generator.py'])