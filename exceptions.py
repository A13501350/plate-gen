class InvalidPlateNumberError(ValueError):
    """自定义车牌号格式错误异常"""
    def __init__(self, plate_type: str, number: str):
        self.plate_type = plate_type
        self.number = number
        super().__init__(f"Invalid plate number format for {plate_type}: {number}")


class ResourceNotFoundError(FileNotFoundError):
    """资源文件缺失异常"""
    def __init__(self, resource_path: str):
        super().__init__(f"Resource file not found: {resource_path}")


class InvalidVehicleComboError(ValueError):
    """无效的车牌类型与车型组合异常
    
    当用户提供的车牌类型与车辆类型组合不合法时抛出此异常。
    例如：摩托车不能使用大型汽车车牌。
    """
    def __init__(self, message: str, vehicle_type: str):
        self.vehicle_type = vehicle_type
        super().__init__(message)