import pytest
from plate_validator import parse_plate_number
from plate_config import PlateConfig, InvalidVehicleComboError
from exceptions import InvalidPlateNumberError

# 普通车牌测试
def test_ordinary_plate():
    # 基本格式测试
    result = parse_plate_number('普通', '汽车', '京A1234')
    assert result['province'] == '京'
    assert result['org_code'] == 'A'
    assert result['serial'] == '1234'
    
    result = parse_plate_number('普通', '汽车', '沪B5678警')
    assert result['province'] == '沪'
    assert result['org_code'] == 'B'
    assert result['serial'] == '5678'
    assert result['special_mark'] == '警'
    
    # 字母位置组合规则测试
    result = parse_plate_number('普通', '汽车', '京A12B4')  # 第4位字母
    assert result['serial'] == '12B4'
    
    result = parse_plate_number('普通', '汽车', '京A1B34')  # 第3位字母
    assert result['serial'] == '1B34'
    
    result = parse_plate_number('普通', '汽车', '京AB234')  # 第1-2位字母
    assert result['serial'] == 'B234'
    
    result = parse_plate_number('普通', '汽车', '京A1234D')  # 第5位字母
    assert result['serial'] == '1234D'
    
    # 专用号牌测试
    result = parse_plate_number('普通', '汽车', '京A1234警')
    assert result['special_mark'] == '警'
    
    result = parse_plate_number('普通', '汽车', '京A1234学')
    assert result['special_mark'] == '学'
    
    # 无效案例测试
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '京OA123')  # 包含禁用字母O
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '京AI123')  # 包含禁用字母I
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '京A12345X')  # 长度超限
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '京A123')  # 长度不足

# 新能源车牌测试
def test_new_energy_plate():
    # 小型新能源车牌测试
    result = parse_plate_number('普通', '新能源', '京AD12345')  # 纯电动车，首位D
    assert result['province'] == '京'
    assert result['org_code'] == 'A'
    assert result['serial'] == 'D12345'
    
    result = parse_plate_number('普通', '新能源', '京AF12345')  # 非纯电动车，首位F
    assert result['province'] == '京'
    assert result['org_code'] == 'A'
    assert result['serial'] == 'F12345'
    
    result = parse_plate_number('普通', '新能源', '京DA12345')  # 首位+次位字母组合
    assert result['province'] == '京'
    assert result['org_code'] == 'D'
    assert result['serial'] == 'A12345'
    
    # 大型新能源车牌测试
    result = parse_plate_number('大型', '新能源', '京A12345D')  # 纯电动车，末位D
    assert result['province'] == '京'
    assert result['org_code'] == 'A'
    assert result['serial'] == '12345D'
    
    result = parse_plate_number('大型', '新能源', '京A12345F')  # 非纯电动车，末位F
    assert result['province'] == '京'
    assert result['org_code'] == 'A'
    assert result['serial'] == '12345F'
    
    # 无效案例测试
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '新能源', '京A123456')  # 序号格式错误
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '新能源', '京AO12345')  # 包含禁用字母
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('大型', '新能源', '京A12345Z')  # 末位字母不符合规范
        
    # 车型组合测试
    with pytest.raises(ValueError):
        parse_plate_number('普通', '汽车', '京AD12345')  # 无效的车型组合

# 使馆车牌测试
def test_embassy_plate():
    result = parse_plate_number('使馆', '汽车', '123456使')
    assert result['embassy_code'] == '123'
    assert result['serial'] == '456'
    
    result = parse_plate_number('使馆', '摩托车', '123456使')
    assert result['embassy_code'] == '123'
    assert result['serial'] == '456'
    
    # 无效案例测试
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('使馆', '汽车', '12345使')  # 序号长度错误
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('使馆', '汽车', 'ABC456使')  # 非数字代码

# 领馆车牌测试
def test_consulate_plate():
    # 领馆汽车：省+代码+序号+领
    result = parse_plate_number('领馆', '汽车', '京1234B领')
    assert result['province'] == '京'
    assert result['embassy_code'] == '123'
    assert result['serial'] == '4B'
    
    # 领馆摩托车：省+领+代码+序号
    result = parse_plate_number('领馆', '摩托车', '沪领1239D')
    assert result['province'] == '沪'
    assert result['embassy_code'] == '123'
    assert result['serial'] == '9D'
    
    # 无效案例测试
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('领馆', '汽车', '京领12AB')  # 代码长度错误
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('领馆', '汽车', '京领ABC12')  # 非数字代码

# 参数化测试：普通车牌序号组合规则
@pytest.mark.parametrize("serial,valid", [
    ('1234', True),     # 规则1：全数字
    ('A234', True),     # 规则2：第1位字母
    ('AB34', True),     # 规则3：第1-2位字母
    ('1B34', True),     # 规则4：第2位字母
    ('12C4', True),     # 规则5：第3位字母
    ('123D', True),     # 规则6：第4位字母
    ('1234D', True),    # 规则7：第5位字母（仅5位序号）
    ('A234D', True),    # 规则8：第1、5位字母
    ('123CD', True),    # 规则9：第4-5位字母
    ('A2C4', True),     # 规则10：第1、3位字母
    ('1BC4', True),     # 规则11：第2-3位字母
    ('A23D', True),     # 规则12：第1、4位字母
    ('1B3D', True),     # 规则13：第2、4位字母
    ('1C23D', True),     # 规则14：第2、5位字母
    ('34BC', True),     # 规则15：第3、4位字母
    ('12B6D', True),     # 规则16：第3、5位字母
    ('ABCD', False),    # 无效：全字母
    ('1234O', False),   # 无效：禁用字母O
    ('1234I', False),   # 无效：禁用字母I
])
def test_serial_patterns(serial, valid):
    plate_number = f'京A{serial}'
    if valid:
        result = parse_plate_number('普通', '汽车', plate_number)
        assert result['serial'] == serial
    else:
        with pytest.raises(InvalidPlateNumberError):
            parse_plate_number('普通', '汽车', plate_number)

# 异常类型测试
def test_invalid_types():
    with pytest.raises(ValueError):
        parse_plate_number('未知类型', '汽车', '京A1234')  # 无效的车牌类型
    with pytest.raises(ValueError):
        parse_plate_number('普通', '未知车型', '京A1234')  # 无效的车型
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '')  # 空车牌号
    with pytest.raises(InvalidPlateNumberError):
        parse_plate_number('普通', '汽车', '京A1234X测试')  # 错误的专用标识