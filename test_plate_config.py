import pytest
from plate_config import PlateConfig, InvalidVehicleComboError
from pathlib import Path

# 测试get_plate_category方法
class TestGetPlateCategory:
    def test_valid_ordinary_vehicle_combinations(self):
        """测试普通车辆的有效组合"""
        assert PlateConfig.get_plate_category('普通', '汽车') == '普通'
        assert PlateConfig.get_plate_category('大型', '汽车') == '大型'
        assert PlateConfig.get_plate_category('普通', '摩托车') == '普通'
        assert PlateConfig.get_plate_category('大型', '摩托车') == '大型'
        assert PlateConfig.get_plate_category('普通', '低速车') == '普通'
        assert PlateConfig.get_plate_category('大型', '低速车') == '大型'
        assert PlateConfig.get_plate_category('普通', '轻便摩托车') == '普通'
    
    def test_valid_new_energy_combinations(self):
        """测试新能源车辆的有效组合"""
        assert PlateConfig.get_plate_category('普通', '新能源') == '小型新能源'
        assert PlateConfig.get_plate_category('大型', '新能源') == '大型新能源'
    
    def test_valid_diplomatic_combinations(self):
        """测试使领馆车辆的有效组合"""
        assert PlateConfig.get_plate_category('使馆', '汽车') == '使馆汽车'
        assert PlateConfig.get_plate_category('领馆', '汽车') == '领馆汽车'
        assert PlateConfig.get_plate_category('使馆', '摩托车') == '使馆摩托车'
        assert PlateConfig.get_plate_category('领馆', '摩托车') == '领馆摩托车'
    
    def test_invalid_plate_type(self):
        """测试无效的车牌类型"""
        with pytest.raises(ValueError, match='未识别的车牌类型'):
            PlateConfig.get_plate_category('未知', '汽车')
    
    def test_invalid_vehicle_type(self):
        """测试无效的车辆类型"""
        with pytest.raises(ValueError, match='未识别的车辆类型'):
            PlateConfig.get_plate_category('普通', '未知')
    
    def test_invalid_diplomatic_combinations(self):
        """测试使领馆车辆的无效组合"""
        invalid_vehicles = ['新能源', '低速车', '轻便摩托车']
        for vehicle in invalid_vehicles:
            with pytest.raises(InvalidVehicleComboError):
                PlateConfig.get_plate_category('使馆', vehicle)
            with pytest.raises(InvalidVehicleComboError):
                PlateConfig.get_plate_category('领馆', vehicle)

# 测试get_config_by_full_name方法
class TestGetConfigByFullName:
    def test_valid_plate_full_name(self, mocker):
        """测试有效的车牌全名"""
        # 模拟配置数据
        mock_config = PlateConfig(
            size=(440, 140),
            font_path=Path('resources/fonts/blue/font.ttf'),
            background_path=Path('resources/backgrounds/440×140.svg'),
            colors={'background': '#FFFFFF', 'text': '#000000'},
            char_positions={
                'province': (15, 25),
                'letter': (72, 25),
                'separator': (134, 70),
                'digits': [(151, 25), (208, 25), (265, 25), (322, 25), (379, 25)]
            }
        )
        
        # 模拟PLATE_CONFIG_MAP
        mock_map = {'小型汽车号牌': mock_config}
        mocker.patch('resources.plate_configs.PLATE_CONFIG_MAP', mock_map)
        
        # 测试配置获取
        config = PlateConfig.get_config_by_full_name('小型汽车号牌')
        assert isinstance(config, PlateConfig)
        assert config.size == (440, 140)
        assert isinstance(config.font_path, Path)
        assert isinstance(config.background_path, Path)
        assert isinstance(config.colors, dict)
        assert isinstance(config.char_positions, dict)
    
    def test_invalid_plate_full_name(self):
        """测试无效的车牌全名"""
        with pytest.raises(KeyError, match='未找到车牌类型'):
            PlateConfig.get_config_by_full_name('无效车牌类型')