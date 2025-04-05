import argparse
from core import PlateGenerator, ResourceNotFoundError
import logging
import sys
from plate_validator import InvalidPlateNumberError
from plate_randomizer import PlateRandomizer

def main():
    parser = argparse.ArgumentParser(description='车牌生成工具')
    parser.add_argument('--type', choices=['普通', '大型', '使馆', '领馆'], 
                       required=True, help='车牌类型')
    parser.add_argument('--vehicle', choices=['汽车', '摩托车', '新能源', '低速车', '轻便摩托车'], 
                       required=True, help='适用车型')
    parser.add_argument('--number', help='车牌号码，不指定则随机生成')
    parser.add_argument('--output', default='outputs/output.svg', help='输出文件路径')
    parser.add_argument('--resources', help='资源目录路径，默认为程序目录下的resources文件夹')
    parser.add_argument('--count', default=5, type=int, help='生成车牌数量')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.ERROR)
    
    try:
        generator = PlateGenerator(args.resources)
        
        if args.number:
            svg = generator.generate(args.type, args.vehicle, args.number)
            svg.save(args.output)
            print(f'车牌已生成: {args.output}')
        else:
            randomizer = PlateRandomizer()
            numbers = randomizer.generate(args.type, args.count)
            for number in numbers:
                svg = generator.generate(args.type, args.vehicle, number)
                svg.save(args.output)
                print(f'车牌已生成: {args.output}')
            
    except InvalidPlateNumberError as e:
        logging.error(f'无效车牌号: {e}')
    except ResourceNotFoundError as e:
        logging.error(f'资源文件缺失: {e}')
        sys.exit(1)
    except Exception as e:
        logging.error(f'生成失败: {e}')

if __name__ == '__main__':
    main()