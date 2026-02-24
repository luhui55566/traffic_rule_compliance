# OpenDRIVE支持实施计划

## 1. 概述

本文档详细说明了在现有map_node系统中增加OpenDRIVE格式地图支持的实施步骤。

## 2. 实施阶段

### Phase 1: 基础架构搭建 (Week 1)

#### 1.1 创建抽象基类和工厂模式

**任务**:
- 创建 [`BaseMapLoader`](src/map_node/maploader/base_loader.py) 抽象基类
- 创建 [`MapLoaderFactory`](src/map_node/maploader/factory.py) 工厂类
- 重构现有 [`OSMMapLoader`](src/map_node/maploader/osm_loader.py) 继承基类

**文件创建**:
```
src/map_node/maploader/
├── base_loader.py       # 新增：抽象基类
├── factory.py           # 新增：工厂类
├── osm_loader.py        # 重构：OSM加载器
```

**验收标准**:
- [ ] BaseMapLoader定义了所有加载器的通用接口
- [ ] MapLoaderFactory能够根据文件扩展名创建对应的加载器
- [ ] OSMMapLoader成功继承BaseMapLoader并保持原有功能
- [ ] 现有OSM地图加载功能不受影响

#### 1.2 创建统一加载接口

**任务**:
- 重构 [`MapLoader`](src/map_node/maploader/loader.py) 类作为统一接口
- 更新 [`__init__.py`](src/map_node/maploader/__init__.py) 导出新的接口

**验收标准**:
- [ ] MapLoader能够自动识别地图格式
- [ ] MapLoader提供统一的加载接口
- [ ] 向后兼容现有代码

---

### Phase 2: OpenDRIVE加载器实现 (Week 2)

#### 2.1 安装和配置OpenDRIVE解析引擎

**任务**:
- 安装libOpenDRIVE
- 配置开发环境

**libOpenDRIVE安装**:
```bash
# pip直接安装
pip install libOpenDRIVE
```

**验收标准**:
- [ ] libOpenDRIVE成功安装
- [ ] Python可以导入libOpenDRIVE模块

#### 2.2 实现XODRMapLoader基础框架

**任务**:
- 创建 [`XODRMapLoader`](src/map_node/maploader/xodr_loader.py) 类
- 实现基础数据结构

**文件创建**:
```
src/map_node/maploader/
└── xodr_loader.py       # 新增：OpenDRIVE加载器
```

**验收标准**:
- [ ] XODRMapLoader使用esmini解析OpenDRIVE
- [ ] OpenDriveData数据结构定义完整

#### 2.3 实现esmini解析支持

**任务**:
- 实现 `load_map()` 方法
- 实现 `_extract_opendrive_data()` 方法
- 实现几何提取方法

**验收标准**:
- [ ] 能够成功加载OpenDRIVE文件
- [ ] 能够提取道路、车道、交叉口数据
- [ ] 能够提取车道中心线和边界坐标

#### 2.4 实现Lanelet2格式转换

**任务**:
- 实现 `convert_to_lanelet2()` 方法
- 实现车道类型映射
- 实现MapInfo生成

**验收标准**:
- [ ] OpenDRIVE数据成功转换为Lanelet2格式
- [ ] 车道类型映射正确
- [ ] MapInfo包含正确的元数据

---

### Phase 3: 集成和测试 (Week 3)

#### 3.1 单元测试

**任务**:
- 编写XODRMapLoader单元测试
- 编写工厂模式单元测试
- 编写转换逻辑单元测试

**测试文件**:
```
tests/
├── test_xodr_loader.py      # 新增：OpenDRIVE加载器测试
├── test_factory.py           # 新增：工厂模式测试
└── test_converter.py        # 新增：转换逻辑测试
```

**测试用例**:
```python
# test_xodr_loader.py
def test_load_opendrive():
    """测试使用libOpenDRIVE加载OpenDRIVE"""
    loader = XODRMapLoader()
    result = loader.load_map("test.xodr")
    assert result is True

def test_convert_to_lanelet2():
    """测试转换为Lanelet2格式"""
    loader = XODRMapLoader()
    loader.load_map("test.xodr")
    result = loader.convert_to_lanelet2()
    assert result is True
    assert loader.is_loaded() is True
```

**验收标准**:
- [ ] 所有单元测试通过
- [ ] 代码覆盖率达到80%以上

#### 3.2 集成测试

**任务**:
- 编写端到端集成测试
- 测试与LocalMapConstructor的集成
- 测试与MapAPI的集成

**测试用例**:
```python
# test_integration.py
def test_opendrive_to_local_map():
    """测试从OpenDRIVE到局部地图的完整流程"""
    # 加载OpenDRIVE地图
    map_loader = MapLoader()
    map_loader.load_map("test.xodr")
    
    # 构建局部地图
    map_api = MapAPI(map_loader.get_map_data())
    constructor = LocalMapConstructor(map_api, ego_pose, range=200)
    local_map = constructor.construct_local_map()
    
    # 验证局部地图
    assert local_map is not None
    assert len(local_map.lanes) > 0

def test_osm_and_xodr_compatibility():
    """测试OSM和OpenDRIVE的兼容性"""
    # 加载OSM地图
    osm_loader = MapLoader()
    osm_loader.load_map("test.osm")
    osm_api = MapAPI(osm_loader.get_map_data())
    osm_constructor = LocalMapConstructor(osm_api, ego_pose, range=200)
    osm_local_map = osm_constructor.construct_local_map()
    
    # 加载OpenDRIVE地图
    xodr_loader = MapLoader()
    xodr_loader.load_map("test.xodr")
    xodr_api = MapAPI(xodr_loader.get_map_data())
    xodr_constructor = LocalMapConstructor(xodr_api, ego_pose, range=200)
    xodr_local_map = xodr_constructor.construct_local_map()
    
    # 验证两种格式产生相同的数据结构
    assert type(osm_local_map) == type(xodr_local_map)
```

**验收标准**:
- [ ] 所有集成测试通过
- [ ] OSM和OpenDRIVE加载的地图产生相同的数据结构
- [ ] 局部地图接口保持不变

#### 3.3 性能测试

**任务**:
- 测试OpenDRIVE地图加载性能
- 测试转换性能
- 对比OSM和OpenDRIVE的性能

**性能指标**:
- OpenDRIVE地图加载时间 < 5秒
- 转换为Lanelet2时间 < 3秒
- 内存占用合理

**验收标准**:
- [ ] 性能测试通过
- [ ] 性能指标满足要求

---

### Phase 4: 文档和优化 (Week 4)

#### 4.1 API文档

**任务**:
- 更新模块README
- 编写API文档
- 添加使用示例

**文档文件**:
```
src/map_node/maploader/
└── README.md              # 更新：模块文档
docs/
└── opendrive_guide.md     # 新增：OpenDRIVE使用指南
```

**验收标准**:
- [ ] API文档完整
- [ ] 使用示例清晰
- [ ] 文档与代码同步

#### 4.2 配置文件

**任务**:
- 创建地图配置文件
- 添加OpenDRIVE相关配置

**配置文件**:
```yaml
# configs/map_config.yaml
map:
  default_type: osm
  supported_formats:
    - osm
    - opendrive
  
  opendrive:
    engine: auto
    geometry:
      center_line_samples: 10
      boundary_samples: 10
```

**验收标准**:
- [ ] 配置文件完整
- [ ] 配置项说明清晰

#### 4.3 代码审查和优化

**任务**:
- 代码审查
- 性能优化
- Bug修复

**验收标准**:
- [ ] 代码审查通过
- [ ] 性能优化完成
- [ ] 已知Bug修复

---

## 3. 文件清单

### 新增文件

```
src/map_node/maploader/
├── base_loader.py       # 抽象基类
├── factory.py           # 工厂类
├── xodr_loader.py       # OpenDRIVE加载器
└── README.md            # 模块文档（更新）

tests/
├── test_xodr_loader.py  # OpenDRIVE加载器测试
├── test_factory.py      # 工厂模式测试
└── test_converter.py    # 转换逻辑测试

configs/
└── map_config.yaml      # 地图配置文件

docs/
└── opendrive_guide.md   # OpenDRIVE使用指南
```

### 修改文件

```
src/map_node/maploader/
├── __init__.py          # 更新导出接口
├── loader.py            # 重构为统一接口
└── loader_local.py      # 重命名为osm_loader.py或保留
```

---

## 4. 接口变更

### 新增接口

```python
# BaseMapLoader
class BaseMapLoader(ABC):
    @abstractmethod
    def load_map(self, file_path: str, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def convert_to_lanelet2(self) -> bool:
        pass

# MapLoaderFactory
class MapLoaderFactory:
    @staticmethod
    def create_loader(file_path: str) -> BaseMapLoader:
        pass

# XODRMapLoader
class XODRMapLoader(BaseMapLoader):
    def __init__(self, engine: OpenDriveEngine = OpenDriveEngine.AUTO):
        pass
```

### 修改接口

```python
# MapLoader - 重构为统一接口
class MapLoader:
    def load_map(self, file_path: str, **kwargs) -> bool:
        # 自动识别格式并加载
        pass
```

### 不变接口

```python
# LocalMapConstructor - 保持不变
class LocalMapConstructor:
    def construct_local_map(self, ego_pose: Pose = None) -> LocalMap:
        pass

# MapAPI - 保持不变
class MapAPI:
    def get_lanelets_in_bbox(self, bbox: BoundingBox) -> List[Lanelet]:
        pass
```

---

## 5. 测试数据

### 测试地图文件

需要准备以下测试地图文件：

```
configs/maps/
├── test_osm.osm         # OSM格式测试地图
├── test_opendrive.xodr  # OpenDRIVE格式测试地图
└── Town10HD.xodr        # 现有OpenDRIVE地图
```

---

## 6. 风险和缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| esmini安装困难 | 高 | 中 | 提供详细安装指南，备选carla-opendrive |
| 转换精度损失 | 中 | 低 | 添加坐标转换验证和校正 |
| 性能问题 | 中 | 低 | 实现缓存机制和增量加载 |
| 接口兼容性 | 低 | 低 | 严格遵循现有接口定义 |
| 测试数据不足 | 中 | 中 | 生成测试地图或使用公开数据集 |

---

## 7. 时间表

| 阶段 | 任务 | 时间 | 负责人 |
|------|------|------|--------|
| Phase 1 | 基础架构搭建 | Week 1 | - |
| Phase 2 | OpenDRIVE加载器实现 | Week 2 | - |
| Phase 3 | 集成和测试 | Week 3 | - |
| Phase 4 | 文档和优化 | Week 4 | - |

---

## 8. 验收标准

### 功能验收

- [ ] 支持加载OpenDRIVE格式地图
- [ ] 支持esmini和carla-opendrive两种解析引擎
- [ ] OpenDRIVE数据正确转换为Lanelet2格式
- [ ] 局部地图输出接口保持不变
- [ ] 现有OSM地图加载功能不受影响

### 质量验收

- [ ] 单元测试覆盖率 >= 80%
- [ ] 所有测试用例通过
- [ ] 代码审查通过
- [ ] 性能指标满足要求

### 文档验收

- [ ] API文档完整
- [ ] 使用示例清晰
- [ ] 配置文件完整
- [ ] README更新

---

## 9. 后续优化

### 短期优化

- 添加更多OpenDRIVE特性支持（如交通信号、标志）
- 优化转换性能
- 添加可视化工具

### 长期优化

- 支持更多地图格式
- 实现地图缓存机制
- 支持增量加载
