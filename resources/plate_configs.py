# -*- coding: utf-8 -*-
"""
车牌配置模块

此模块包含各种车牌类型的配置信息，使用Python原生格式替代JSON格式。
每种车牌类型使用单独的变量名，避免使用逗号分隔多个名称作为键。
"""

from plate_config import PlateConfig
from pathlib import Path
from resources import char_positions

# 小型汽车号牌配置
SMALL_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/blue"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "#223F99",
        "text": "white"
    },
    char_positions=char_positions.小型汽车号牌
)

# 警用汽车号牌配置
POLICE_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/blue"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "white",
        "text": "black"
    },
    char_positions=char_positions.警用汽车号牌
)

# 大型汽车前号牌配置
LARGE_VEHICLE_FRONT = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/yellow"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "#FFC210",
        "text": "black"
    },
    char_positions=char_positions.大型汽车前号牌
)

# 教练汽车号牌配置
TRAINING_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/yellow"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "#FFC210",
        "text": "black"
    },
    char_positions=char_positions.教练汽车号牌
)

# 使馆汽车号牌配置
EMBASSY_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/blue"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "black",
        "text": "white"
    },
    char_positions=char_positions.使馆汽车号牌
)

# 领馆汽车号牌配置
CONSULATE_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/blue"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "black",
        "text": "white"
    },
    char_positions=char_positions.领馆汽车号牌
)

# 港澳入出境号牌配置
HK_MACAO_VEHICLE = PlateConfig(
    size=(440, 140),
    font_path=Path("fonts/blue"),
    background_path=Path("backgrounds/440×140.svg"),
    colors={
        "background": "black",
        "text": "white"
    },
    char_positions=char_positions.港澳入出境车号牌
)

# 小型新能源汽车号牌配置
SMALL_NEW_ENERGY_VEHICLE = PlateConfig(
    size=(480, 140),
    font_path=Path("fonts/green"),
    background_path=Path("backgrounds/480×140/Car.svg"),
    colors={
        "text": "black"
    },
    char_positions=char_positions.小型新能源汽车号牌
)

# 大型新能源汽车号牌配置
LARGE_NEW_ENERGY_VEHICLE = PlateConfig(
    size=(480, 140),
    font_path=Path("fonts/green"),
    background_path=Path("backgrounds/480×140/Truck.svg"),
    colors={
        "text": "black"
    },
    char_positions=char_positions.大型新能源汽车号牌
)

# 普通摩托车号牌配置
NORMAL_MOTORCYCLE = PlateConfig(
    size=(220, 140),
    font_path=Path("fonts/yellow"),
    background_path=Path("backgrounds/220×140.svg"),  
    colors={
        "background": "#FFC210",
        "text": "black" 
    },
    char_positions=char_positions.普通摩托车号牌
)

# 轻便摩托车号牌配置
LIGHTWEIGHT_MOTORCYCLE = PlateConfig(
    size=(220, 140),
    font_path=Path("fonts/yellow"),
    background_path=Path("backgrounds/220×140.svg"), 
    colors={
        "background": "#223F99",
        "text": "white"
    },
    char_positions=char_positions.轻便摩托车号牌
)

# 配置映射表，用于将车牌类型名称映射到对应的配置
PLATE_CONFIG_MAP = {
    "小型汽车号牌": SMALL_VEHICLE,
    "警用汽车号牌": POLICE_VEHICLE,
    "大型汽车前号牌": LARGE_VEHICLE_FRONT,
    "教练汽车号牌": TRAINING_VEHICLE,
    "使馆汽车号牌": EMBASSY_VEHICLE,
    "领馆汽车号牌": CONSULATE_VEHICLE,
    "港澳入出境车": HK_MACAO_VEHICLE,
    "小型新能源汽车号牌": SMALL_NEW_ENERGY_VEHICLE,
    "大型新能源汽车号牌": LARGE_NEW_ENERGY_VEHICLE,
    "普通摩托车号牌": NORMAL_MOTORCYCLE,
    "轻便摩托车号牌": LIGHTWEIGHT_MOTORCYCLE,
    "低速车号牌": None,
}

PLATE_SIZE_MAP = {
    "440x140": [
        SMALL_VEHICLE,
        POLICE_VEHICLE,
        LARGE_VEHICLE_FRONT,
        TRAINING_VEHICLE,
        EMBASSY_VEHICLE,
        CONSULATE_VEHICLE,
        HK_MACAO_VEHICLE
    ],
    "480x140": [
        SMALL_NEW_ENERGY_VEHICLE,
        LARGE_NEW_ENERGY_VEHICLE
    ],
    "220x140": [
        NORMAL_MOTORCYCLE,
        LIGHTWEIGHT_MOTORCYCLE
    ]
}