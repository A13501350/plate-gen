#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试车牌随机生成器

验证重写后的plate_randomizer.py是否能生成符合GA36-2018标准的车牌号码
"""

from plate_randomizer import PlateRandomizer
from plate_validator import validate_number

def test_plate(plate_type, validator_type, count=5):
    """测试指定类型的车牌生成与验证
    
    Args:
        plate_type: 生成器使用的车牌类型
        validator_type: 验证器使用的车牌类型
        count: 测试数量
    """
    plates = PlateRandomizer.generate(plate_type, count)
    print(f'\n{validator_type}测试:')
    
    success = 0
    for plate in plates:
        try:
            validate_number(validator_type, plate)
            print(f'✓ {plate} 验证通过')
            success += 1
        except Exception as e:
            print(f'✗ {plate} 验证失败: {e}')
    
    print(f'通过率: {success}/{count} ({success/count*100:.1f}%)')
    return success == count

def main():
    """主测试函数"""
    print('=' * 50)
    print('车牌随机生成器测试')
    print('=' * 50)
    
    # 测试蓝牌
    blue_success = test_plate('blue', '普通小型汽车')
    
    # 测试小型新能源
    small_green_success = test_plate('green_small', '小型新能源汽车')
    
    # 测试大型新能源
    large_green_success = test_plate('green_large', '大型新能源汽车')
    
    # 测试随机新能源
    random_green_success = test_plate('green', '小型新能源汽车', 10)
    
    # 总结
    print('\n' + '=' * 50)
    print('测试结果总结:')
    print('=' * 50)
    print(f'蓝牌测试: {"通过" if blue_success else "失败"}')
    print(f'小型新能源测试: {"通过" if small_green_success else "失败"}')
    print(f'大型新能源测试: {"通过" if large_green_success else "失败"}')
    print(f'随机新能源测试: {"通过" if random_green_success else "失败"}')
    
    if all([blue_success, small_green_success, large_green_success, random_green_success]):
        print('\n所有测试通过！车牌随机生成器符合GA36-2018标准。')
    else:
        print('\n测试失败！车牌随机生成器需要修复。')

if __name__ == '__main__':
    main()