# plate-gen

生成符合 GA 36-2018 的中国机动车号牌 SVG 图像。既可作为命令行工具使用，也可作为 Python 库集成到论文配图、测试数据生成等流程中。

## 安装

```bash
pip install -e ".[dev]"
```

要求 Python 3.10+，运行时依赖 `svgutils` 与 `lxml`。

## 命令行

```bash
# 查看全部号牌种类（标识、显示名、尺寸、版式、是否支持随机）
plate-gen --list-categories

# 生成指定号码（默认写入 outputs/京A12345.svg）
plate-gen --category 小型汽车号牌 --number 京A12345

# 也可以用 ASCII 标识
plate-gen --category small_vehicle --number 京A12345

# 随机生成 3 个号码，每个文件以各自号码命名（默认写入 outputs/）
plate-gen --category 普通摩托车号牌 --count 3

# 显式指定具体文件名（单张时按该名称写入）
plate-gen --category 小型汽车号牌 --number 京A12345 --output outputs/plate.svg

# 大型汽车后号牌
plate-gen --category 大型汽车号牌 --position rear --number 京A12345 --output outputs/rear.svg

# 等价于 python -m plate_gen
python -m plate_gen --category large_new_energy --number 京A12345D
```

参数说明：

| 参数 | 说明 |
|---|---|
| `--category` | 号牌种类：中文全名或 ASCII 标识；除 `--list-categories` 外必填 |
| `--list-categories` | 列出全部种类，不需要其他参数 |
| `--number` | 指定号码；省略时按该种类规则随机生成 |
| `--output` | 输出路径：默认 `outputs`（目录），目录内按号码命名；路径末段带扩展名时视为具体文件 |
| `--resources` | 自定义资源目录 |
| `--count` | 随机生成数量，默认 5；指定 `--number` 时忽略 |
| `--position` | 大型汽车号牌的前/后版式：`front`（默认）/ `rear`；其余种类传 `rear` 返回退出码 2 |
| `--debug` | 输出调试日志 |

### 输出命名

- **目录语义**（默认 `outputs`、已存在的目录、或路径末段没有扩展名）：文件名取号码本身，扩展名 `.svg`。指定号码时如 `--number 京A12345` → `outputs/京A12345.svg`；批量随机时每个文件以各自号码命名。
- **字符规范化**：只做最小必要替换。间隔号 `·` 与 Windows 保留字符（`< > : " / \ | ? *`）替换为 `-`；合法号码不含 `-`，因此可由文件名还原号码，不引入哈希或纯序号。
- **同名冲突**：目标文件已存在，或同一批次出现重复号码时，追加确定性的 `-2`、`-3` 后缀，不覆盖已有文件。
- **文件语义**（路径末段带扩展名且不是目录）：单张时按该名称写入并尊重用户命名（已有同名文件会被覆盖）；批量时取其父目录，文件仍按号码命名。

资源目录优先级：环境变量 `PLATE_RESOURCES_DIR` > `--resources` > 包内 `resources/`。

退出码：`0` 成功；`1` 资源缺失或未预期错误；`2` 号码/种类/版式不合法。

### 旧参数迁移

旧的 `--type` + `--vehicle` 双轴已删除，按号码中的专用标记或车型直接选择种类：

| 旧 `--type` / `--vehicle` / 标记 | 新 `--category` |
|---|---|
| 普通 / 汽车 / 无标记 | `小型汽车号牌` |
| 普通 / 汽车 / 警 | `警用汽车号牌` |
| 普通 / 汽车 / 学 | `教练汽车号牌` |
| 普通 / 汽车 / 港 或 澳 | `港澳入出境车号牌` |
| 大型 / 汽车 / 无标记 / front | `大型汽车号牌`（`--position front`） |
| 大型 / 汽车 / 无标记 / rear | `大型汽车号牌`（`--position rear`） |
| 大型 / 汽车 / 挂 | `挂车号牌` |
| 普通 / 摩托车 / 无标记 | `普通摩托车号牌` |
| 普通 / 摩托车 / 警 | `警用摩托车号牌` |
| 普通 / 摩托车 / 学 | `教练摩托车号牌` |
| 普通 / 轻便摩托车 / 无标记 | `轻便摩托车号牌` |
| 普通 / 低速车 / 无标记 | `低速车号牌` |
| 普通 / 新能源 | `小型新能源汽车号牌` |
| 大型 / 新能源 | `大型新能源汽车号牌` |
| 使馆 / 汽车 | `使馆汽车号牌` |
| 使馆 / 摩托车 | `使馆摩托车号牌` |
| 领馆 / 汽车 | `领馆汽车号牌` |
| 领馆 / 摩托车 | `领馆摩托车号牌` |

旧模型中其余 9 个 `(type, vehicle)` 空格不再存在；号码不合规时由 `InvalidPlateNumberError` 报告。

## Python API

```python
from plate_gen import (
    PlateCategory,
    PlateGenerator,
    PlateRandomizer,
    get_plate_spec,
    parse_plate_number,
    random_numbers,
)

generator = PlateGenerator()
generator.render_to_file(PlateCategory.SMALL_VEHICLE, "京A12345", "outputs/plate.svg")

# 大型汽车后号牌：版式由规格表决定（默认 front）
generator.render_to_file(
    PlateCategory.LARGE_VEHICLE, "京A12345", "outputs/rear.svg", position="rear"
)

parsed = parse_plate_number(PlateCategory.CONSULATE_VEHICLE, "京1234B领")
print(parsed.category.value, parsed.embassy_code, parsed.serial)

numbers = random_numbers(PlateCategory.SMALL_NEW_ENERGY, 10)

spec = get_plate_spec("小型汽车号牌")
print(spec.variants["default"].size)
```

随机生成器可注入随机源以复现结果：

```python
import random
from plate_gen import PlateCategory, PlateRandomizer

randomizer = PlateRandomizer(random.Random(42))
print(randomizer.generate(PlateCategory.SMALL_VEHICLE, 3))
```

公共 API 还包括 `PlateSpec`、`VariantSpec`、`NumberFormat`、`FieldRule`、`Placement`、`get_plate_spec`、`iter_plate_specs`、`PlatePosition` 与异常类。

## 支持的号牌

| 号牌种类 | 标识 | 尺寸 | 配色 |
|---|---|---|---|
| 小型汽车号牌 | `small_vehicle` | 440×140 | 蓝底白字 |
| 大型汽车号牌（前/后） | `large_vehicle` | 440×140 / 440×220 | 黄底黑字，后牌两行 |
| 警用汽车号牌（前/后） | `police_vehicle` | 440×140 | 白底黑字，红“警” |
| 教练汽车号牌 | `training_vehicle` | 440×140 | 黄底黑字 |
| 港澳入出境车号牌 | `hk_macao_vehicle` | 440×140 | 黑底白字 |
| 普通摩托车号牌 | `normal_motorcycle` | 220×140 | 黄底黑字 |
| 警用摩托车号牌 | `police_motorcycle` | 220×140 | 白底黑字，红“警” |
| 教练摩托车号牌 | `training_motorcycle` | 220×140 | 黄底黑字 |
| 轻便摩托车号牌 | `light_motorcycle` | 220×140 | 蓝底白字 |
| 低速车号牌 | `low_speed_vehicle` | 300×165 | 黄底黑字 |
| 挂车号牌 | `trailer` | 440×220 | 黄底黑字 |
| 使馆汽车号牌 | `embassy_vehicle` | 440×140 | 黑底白字 |
| 使馆摩托车号牌 | `embassy_motorcycle` | 220×140 | 黑底白字 |
| 领馆汽车号牌 | `consulate_vehicle` | 440×140 | 黑底白字 |
| 领馆摩托车号牌 | `consulate_motorcycle` | 220×140 | 黑底白字 |
| 小型新能源汽车号牌 | `small_new_energy` | 480×140 | 渐变绿底黑字 |
| 大型新能源汽车号牌（前） | `large_new_energy` | 480×140 | 渐变绿底黑字 |
| 大型新能源汽车号牌（后） | `large_new_energy` | 480×140 | 黄绿底黑字（左黄右绿） |

号码规则全部是数据：每种号牌在规格里声明字段与逐位置字符类，校验和随机生成共用同一份模板。规则依据 GA 36-2018 表 3（序号位数）、表 4（4/5 位序号的 16 种字母位置组合）、表 5/表 6（新能源 6 位序号），实现见 [numbering.py](src/plate_gen/numbering.py)。

- 表 3 的“4 位或 5 位”是**按号牌类型分列的序号位数**，不是同一块号牌可在 4 位与 5 位之间自由选择：小型/大型汽车、普通/轻便摩托、低速车这类无专用汉字的号牌序号固定 5 位；警/学/挂/港/澳这类带专用汉字的号牌被汉字占去一格，序号固定 4 位。5.9.2 的标题虽为“4 位或 5 位序号使用规则”，正文只规定表 4 的字母位置组合与回收号牌重新启用，并不允许单块号牌留空。
- 字位总数由式样图固定（440×140、440×220、220×140、300×165 为 7 格，480×140 新能源为 8 格），序号长度不是自由选项，而是“总格数 − 固定字段 − 专用汉字占格”的结果：规格用 `VariantSpec.slots` 与 `mark_slots` 声明，`serial_slots` 由此推导，`PlateSpec` 构造时校验与号码规则一致（见 `serial_length_for_slots`）。
- 因此**无标记种类必须填满全部序号格**：如 `京A12345`、大型汽车后牌 `京A12345`、摩托 `京A12345`。裸 4 位（如 `京A1234`）在真实号牌上不出现，校验器按编码规则明确拒绝，随机生成也不会产生留空号码；带标记种类则固定为 `京A1234警` 这类 4 位，专用汉字占末格。
- 使馆汽车/摩托车序号为 3 位数字，领馆汽车/摩托车为 2 位（首位数字、末位可为字母，不用 O、I）。
- 使馆、领馆号牌的 3 位驻华外交机构编号不在标准附录 A 的发牌机关代号表内，因此 `randomizable=False`，需要 `--number` 指定号码。
- 省份简称按 5.7/表 2，发牌机关代号按 5.8（A~Z 顺序启用，序号不使用 I、O）。

### 字号、字面框与底板

GA 36-2018 在式样图（图 1~图 19）的尺寸链中给出字节尺寸，6.7.2 规定字符尺寸误差 ±1%。规格表按“摆放”声明 `Placement.box`（字面框宽×高），多行号牌的不同行使用不同字面框：

| 版式 | 字面框 |
|---|---|
| 440×140 | 字高 90、字宽 45，纵向上边距 25、字符间距 12；警用前/后号牌同一版式，发牌机关起于 94、警起于 379、间隔符圆心 77（图 1~图 5） |
| 440×220 后号牌 | 首行 80×60（y=15），序号行 65×110（y=90），序号间距 15（图 6） |
| 480×140 新能源 | 省简称 45×90，发牌机关与序号 43×90，序号间距 9（图 7/图 8） |
| 220×140 摩托 | 首行 50×50 与 50×50（y=10，x=45、125，整体居中），序号行 30×60（y=70），间距 10（图 9/图 11/图 12） |
| 220×140 使馆摩托 | 两行数字 35×48（y=11.5 / 69.5），使 45×90 位于 x=160、上边距 32（图 10） |
| 300×165 低速车 | 首行 55×45（y=10），序号行 45×90（y=65），间距 12（图 19） |

间隔符圆点按版式单独声明半径（`BackgroundSpec.separator_radius`）：警用汽车前牌 7 mm、后牌 8 mm，警用摩托 7 mm，其余 5 mm（图 4、图 5、图 12 尺寸链；5.11 只规定同色同冲压，未给直径）。

生成器把描摹字形按墨迹边界框归一化到声明的字面框：字高对齐字面高度，超宽字形横向压缩，窄字形居中。因此各颜色字形可以混排。

- `fonts/yellow` 缺少 `澳`、`港`、`警`、`领`、`使`、`学` 六个字形，规格中显式声明回退到 `fonts/blue`；这是**设计内的同形回退**：四套字体由同一人按同一套字形描摹，仅颜色不同。实测（归一化到 45×90 em 框后叠合）：blue↔green 72 个同名字形中位 IoU 1.000（多数路径完全相同）；blue↔yellow 66 个同名字形中位 IoU 0.790、质心偏移中位 0.86 mm（最大 4.30 mm），最差为 桂 0.498、沪 0.500、粤 0.528，平移对齐后中位 0.814、最差 沪 0.585。即数字与字母在描摹误差量级内，复杂汉字有可见差异。补齐 yellow 仍建议用同源裁剪图按原 Potrace 流程补描，不使用其他字体替代。
- 大型新能源汽车后号牌底板 `backgrounds/480×140/Track.svg` 由同目录 `Car.svg`（渐变绿底）派生：左侧 0–28.33%（136 mm）为黄底 `#fec210`，右侧保留渐变绿终色。标准图 8 在 PDF 中为灰度印刷，读不出分界；136 mm 取自公安部交管局官方样式图按牌宽标定实测，并与乌鲁木齐/郑州/荆州公交实拍文字（黄底仅覆盖省简称与发牌机关、分界落在圆形标识处）互证，属外部证据而非标准条款。
- 专题矩阵与核对记录见 [plate_spec_matrix.md](doc/plate_spec_matrix.md)，其中列出每项的标准条款、已修正项与推断项。

## 目录结构

```text
src/plate_gen/
├── __init__.py          # 公共 API
├── __main__.py          # python -m plate_gen
├── cli.py               # argparse 入口
├── category.py          # PlateCategory 枚举（唯一分类维度）
├── numbering.py         # 号码字段、逐位置模板、GA36 展开
├── spec.py              # PlateSpec / VariantSpec 等声明式规格模型
├── generator.py         # 按规格摆放字符
├── validator.py         # 按规格解析与校验
├── randomizer.py        # 按规格随机号码
├── constants.py         # 省份、字母与 16 条序号规则
├── types.py             # PlatePosition / ParsedPlate
├── exceptions.py        # 异常体系
├── _svg.py              # SVG 底层操作
├── data/plate_specs.py  # 17 种类、20 版式的规格表
└── resources/           # 底板模板与字形（随包分发）
```

## 开发与测试

```bash
pytest
```

测试按号牌种类重写：覆盖全部 17 种类与前后版式、非法号码、规格完整性（字段/坐标/资源/字形覆盖）、随机器与 CLI，并在几何层面断言字形字高对齐各自声明的字面框、不越界、同一行内相邻字符不重叠。

> 数据说明：外廓尺寸、颜色、字符尺寸与坐标以 GA 36-2018 表 1、第 5 章式样图（图 1~图 19）与 6.7.2 为准，逐项出处见 [plate_spec_matrix.md](doc/plate_spec_matrix.md)；大型新能源汽车后号牌底板的派生来源与推断比例见上文“字号、字面框与底板”。

## 授权

本项目采用 MIT 许可，完全开源，详见 [LICENSE](LICENSE)。代码可自由使用、修改、分发与商用，保留版权声明与许可文本即可。仓库内的 GA 36-2018 标准文档仅作实现依据引用，其著作权归原发布机构所有。
