import logging
from lxml import etree
from typing import Optional, Union, Tuple
from plate_types import PositionCoord
from pathlib import Path
from svgutils.transform import SVGFigure

logger = logging.getLogger(__name__)

def load_svg(svg_path: Union[str, Path]) -> SVGFigure:
    """从文件加载SVG并返回SVGFigure对象
    
    Args:
        svg_path: SVG文件路径，可以是字符串路径或Path对象
        
    Returns:
        SVGFigure: 加载的SVG图形对象
    """
    svg_path_str = str(svg_path)
    fig = SVGFigure()
    
    with open(svg_path_str, 'r', encoding='utf-8') as f:
        svg_file = etree.parse(f, parser=etree.XMLParser(huge_tree=True))
    fig.root = svg_file.getroot()
    return fig

def set_rect_color(svg_figure: SVGFigure, fill_color: str) -> SVGFigure:
    """修改背景矩形的颜色
    
    Args:
        svg_figure: SVG图形对象
        fill_color: 填充颜色，如'#FFFFFF'
        
    Returns:
        SVGFigure: 修改后的SVG图形对象
    """
    root = svg_figure.root
    # 添加SVG命名空间处理
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # 修改XPath表达式，添加命名空间前缀
    xpath_expr = "//svg:rect[@id='background']"
    target_rects = root.xpath(xpath_expr, namespaces=namespaces)
    
    # 如果没有找到id为background的元素，尝试使用旧的尺寸匹配方式作为备选
    if not target_rects:
        logger.warning("未找到id为background的矩形元素，尝试使用尺寸匹配")
        xpath_expr = "//svg:rect[contains(@mask, 'hole-mask')]"
        target_rects = root.xpath(xpath_expr, namespaces=namespaces)
        
    if not target_rects:
        logger.error("未找到背景矩形元素")
        raise ValueError("SVG模板中缺少目标矩形元素")
    
    for rect in target_rects:
        rect.set("fill", fill_color)
    
    return svg_figure

def set_border_and_separator_color(svg_figure: SVGFigure, color: str) -> SVGFigure:
    """修改边框和分隔符的颜色
    
    Args:
        svg_figure: SVG图形对象
        color: 填充颜色，如'#FFFFFF'
        
    Returns:
        SVGFigure: 修改后的SVG图形对象
    """
    root = svg_figure.root
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # 定位边框元素
    border = root.xpath("//svg:rect[@id='border']", namespaces=namespaces)
    if not border:
        logger.error("未找到边框元素")
        raise ValueError("SVG模板中缺少边框元素")
    border[0].set("stroke", color)
    
    # 定位分隔符元素
    separator = root.xpath("//svg:circle[@id='separator']", namespaces=namespaces)
    if not separator:
        logger.error("未找到分隔符元素")
        raise ValueError("SVG模板中缺少分隔符元素")
    separator[0].set("fill", color)
    
    return svg_figure

def set_separator_position(svg_figure: SVGFigure, position: PositionCoord) -> SVGFigure:
    """修改分隔符的位置
    
    Args:
        svg_figure: SVG图形对象
        position: 新的位置坐标，格式为(x, y)
        
    Returns:
        SVGFigure: 修改后的SVG图形对象
    """
    root = svg_figure.root
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # 使用id属性定位分隔符圆圈
    separator = root.xpath("//svg:circle[@id='separator']", namespaces=namespaces)
    
    if not separator:
        logger.error("未找到分隔符元素")
        raise ValueError("SVG模板中缺少分隔符元素")
    
    # 更新分隔符位置
    x, y = position
    separator[0].set("cx", str(x))
    separator[0].set("cy", str(y))
    
    return svg_figure

def set_path_color(svg_figure: SVGFigure, color: str) -> SVGFigure:
    """修改SVG中path元素的颜色
    
    Args:
        svg_figure: SVG图形对象
        color: 填充颜色，如'#FFFFFF'
        
    Returns:
        SVGFigure: 修改后的SVG图形对象
    """
    root = svg_figure.root
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # 定位path元素
    paths = root.xpath("//svg:path", namespaces=namespaces)
    if not paths:
        logger.error("未找到path元素")
        raise ValueError("SVG中缺少path元素")
    
    for path in paths:
        path.set("fill", color)
    
    return svg_figure