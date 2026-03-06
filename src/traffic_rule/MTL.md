# MTL 方法升级提案

> 基于论文《自动驾驶系统交通规则符合性仿真验证方法》的架构优化建议
> 
> 创建时间：2026-03-06
> 状态：待实施

---

## 一、论文 MTL 方法核心

### 1.1 数字化两阶段方法

```
自然语言交通规则
    ↓ 规范化（参数量化）
    ↓ 逻辑化（MTL 编码）
命题 + 逻辑算子（∧ ∨ ¬ →） + 时序算子（□ ◇ U X_p U_p）
    ↓ 形式化验证
可验证的逻辑表达式
```

### 1.2 MTL 框架改进

论文新增 2 个描述过去时间的时序算子：

| 算子 | 名称 | 含义 |
|------|------|------|
| X_p | 上一时刻（Past） | 当前时刻的上一时刻命题为真 |
| U_p | 反向直到（Reverse Until） | 从当前时刻往回，a 直到 b 为真 |
| □ | 全局（Always） | 在所有时刻都为真 |
| ◇ | 最终（Eventually） | 某时刻为真 |
| U | 直到（Until） | a 直到 b 为真 |

### 1.3 命题分类体系

| 类别 | 说明 | 示例 |
|------|------|------|
| 道路类 | 描述道路类型、车道类型 | onRoadType(Highway), onLaneType(Emergency) |
| 基础设施类 | 描述交通设施 | hasTrafficLight(), hasSpeedLimit(120) |
| 临时操作类 | 描述临时操作 | isOvertaking(), isTurning() |
| 目标状态动作类 | 描述车辆状态/动作 | stProperSpeed(Ego), stEmergency(Ego) |
| 环境条件类 | 描述环境条件 | envVisibilityLevel(3), isRaining() |

### 1.4 MTL 规则示例

**高速公路限速规则**：
```
onRoadType(Highway) ∧ envVisibilityLevel(3) ∧ ¬stEmergency(Ego)
    → stProperSpeed(Ego, Longitudinal)
```

其中 `stProperSpeed(Ego, Longitudinal)` 表示纵向速度在 [60, 120] km/h 范围内。

---

## 二、当前架构

### 2.1 架构设计

```
EnvironmentModel
    ↓ 场景识别（SceneIdentifier，查表）
    ↓ 规则过滤（RuleManager，第一级过滤）
TrafficRule.check(env_model)
    ↓ should_check()（第二级过滤）
    ↓ 硬编码检查逻辑
Violation
```

### 2.2 核心组件

- **ViolationDetector**：模块唯一入口
- **SceneIdentifier**：场景识别器
- **RuleManager**：规则管理器（场景-规则映射）
- **TrafficRule**：规则基类
- **StatefulTrafficRule**：有状态规则基类

---

## 三、差异分析

| 维度 | 论文 MTL 方法 | 当前架构 | 差距 |
|------|--------------|----------|------|
| **规则表示** | 命题 + 逻辑算子 + 时序算子 | 硬编码 Python 代码 | ❌ 无形式化表示 |
| **时序逻辑** | X_p, U_p, □, ◇ 等时序算子 | StatefulTrafficRule 历史记录 | ⚠️ 有状态但无形式化算子 |
| **命题体系** | 5类原子命题（道路/设施/操作/状态/环境） | 无命题概念 | ❌ 缺少命题抽象 |
| **规范化** | 模糊语义 → 参数量化 | 配置文件中部分量化 | ⚠️ 部分支持 |
| **可验证性** | 形式化验证（模型检测） | 运行时检查 | ❌ 无法形式化验证 |

---

## 四、升级方案

### 4.1 方案 A：渐进式增强（推荐）

在现有架构上**增加 MTL 层**，不破坏现有代码：

```
┌─────────────────────────────────────────────────────────────┐
│                    traffic_rule 模块                        │
├─────────────────────────────────────────────────────────────┤
│  现有层：ViolationDetector → SceneIdentifier → RuleManager  │
├─────────────────────────────────────────────────────────────┤
│  新增层：                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Proposition │  │  MTLEngine  │  │ TemporalOperators   │  │
│  │  (命题层)   │→ │ (MTL引擎)   │← │ (时序算子)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         ↓                ↓                     ↓            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            MTLRule (继承 TrafficRule)               │   │
│  │  rule_expr: "onRoadType(Highway) → stProperSpeed"  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 新增模块设计

#### 4.2.1 proposition.py - 命题定义

```python
class Proposition:
    """原子命题"""
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category  # ROAD/INFRA/OPERATION/STATE/ENV
    
    def evaluate(self, env_model: EnvironmentModel) -> bool:
        """评估命题真假"""
        pass

# 预定义命题库
PROPOSITIONS = {
    # 道路类
    "onRoadType": Proposition("onRoadType", "ROAD"),
    "onLaneType": Proposition("onLaneType", "ROAD"),
    
    # 基础设施类
    "hasTrafficLight": Proposition("hasTrafficLight", "INFRA"),
    "hasSpeedLimit": Proposition("hasSpeedLimit", "INFRA"),
    
    # 状态类
    "stProperSpeed": Proposition("stProperSpeed", "STATE"),
    "stEmergency": Proposition("stEmergency", "STATE"),
    
    # 环境类
    "envVisibilityLevel": Proposition("envVisibilityLevel", "ENV"),
}
```

#### 4.2.2 temporal_operators.py - 时序算子

```python
class TemporalOperator:
    """时序算子基类"""
    pass

class Always(TemporalOperator):
    """□ 全局算子：在所有时刻都为真"""
    def evaluate(self, history: List[bool]) -> bool:
        return all(history)

class Eventually(TemporalOperator):
    """◇ 最终算子：某时刻为真"""
    def evaluate(self, history: List[bool]) -> bool:
        return any(history)

class Until(TemporalOperator):
    """U 直到算子：a 直到 b 为真"""
    def evaluate(self, a_history: List[bool], b_history: List[bool]) -> bool:
        pass

class Previous(TemporalOperator):
    """X_p 上一时刻算子（论文新增）"""
    def evaluate(self, history: List[bool]) -> bool:
        return history[-2] if len(history) >= 2 else False

class ReverseUntil(TemporalOperator):
    """U_p 反向直到算子（论文新增）"""
    def evaluate(self, a_history: List[bool], b_history: List[bool]) -> bool:
        pass
```

#### 4.2.3 mtl_engine.py - MTL 引擎

```python
class MTLEngine:
    """MTL 规则引擎"""
    
    def __init__(self):
        self.propositions = PROPOSITIONS
        self.operators = {
            '□': Always(),
            '◇': Eventually(),
            'U': Until(),
            'X_p': Previous(),
            'U_p': ReverseUntil(),
        }
    
    def evaluate(self, rule_expr: str, env_model: EnvironmentModel, 
                 history: List[EnvironmentModel]) -> bool:
        """
        评估 MTL 规则表达式
        
        Args:
            rule_expr: MTL 表达式
            env_model: 当前环境模型
            history: 历史环境模型（用于时序算子）
        
        Returns:
            bool: 规则是否满足
        """
        pass
```

#### 4.2.4 mtl_rule.py - MTL 规则类

```python
class MTLRule(StatefulTrafficRule):
    """基于 MTL 的规则"""
    
    def __init__(self, rule_expr: str, params: dict = None):
        super().__init__()
        self.mtl_engine = MTLEngine()
        self.rule_expr = rule_expr
        self.params = params or {}
    
    def check(self, env_model: EnvironmentModel) -> Optional[Violation]:
        # 获取历史
        history = self._get_env_history()
        
        # 评估 MTL 规则
        if not self.mtl_engine.evaluate(self.rule_expr, env_model, history):
            return Violation(
                rule_id=self.id,
                rule_name=self.name,
                description=f"违反 MTL 规则: {self.rule_expr}",
                timestamp=env_model.timestamp
            )
        return None
```

---

### 4.3 方案 B：完全重构

按照论文方法**重新设计**，参考论文的分级分类体系：

```
┌──────────────────────────────────────────────────────────────┐
│                    交通规则数字化系统                         │
├──────────────────────────────────────────────────────────────┤
│  1. 规范化层 (Normalization)                                 │
│     ├─ 模糊语义参数化（"提前" → 5s）                         │
│     └─ 场景参数配置                                          │
├──────────────────────────────────────────────────────────────┤
│  2. 逻辑化层 (Logicization)                                  │
│     ├─ 命题库（5类原子命题）                                 │
│     ├─ 逻辑算子（∧ ∨ ¬ →）                                  │
│     ├─ 时序算子（□ ◇ U X_p U_p）                           │
│     └─ 规则编码器                                            │
├──────────────────────────────────────────────────────────────┤
│  3. 验证层 (Verification)                                    │
│     ├─ 模型检测器                                            │
│     ├─ 轨迹验证器                                            │
│     └─ 违规报告生成                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 五、实施计划（方案 A）

| 阶段 | 内容 | 工作量 | 依赖 |
|------|------|--------|------|
| 1 | 新增 `proposition.py` 命题层 | 1-2 天 | - |
| 2 | 新增 `temporal_operators.py` 时序算子 | 2-3 天 | 阶段1 |
| 3 | 新增 `mtl_engine.py` MTL 引擎 | 3-5 天 | 阶段1,2 |
| 4 | 新增 `MTLRule` 基类 | 1 天 | 阶段3 |
| 5 | 迁移 1-2 个规则到 MTL 形式 | 1-2 天 | 阶段4 |
| 6 | 验证和测试 | 2-3 天 | 阶段5 |

**总计**：约 2 周

---

## 六、建议

### 6.1 推荐方案 A（渐进式增强）

**原因**：
1. **现有架构已经不错** - 两级过滤、状态管理设计合理
2. **低风险** - 不破坏现有代码，增量添加
3. **渐进采用** - 可以先实现核心时序算子，逐步迁移规则

### 6.2 实施优先级

1. **高优先级**：时序算子（X_p, U_p）- 支持时间段判定
2. **中优先级**：命题抽象 - 统一规则表示
3. **低优先级**：MTL 引擎 - 完整形式化验证

### 6.3 立即可改进的点

1. **超速判定改为时间段** - 利用现有 StatefulTrafficRule
2. **连续变道检测** - 已有实现，可作为时序逻辑参考
3. **命题参数配置化** - 将硬编码参数移到配置文件

---

## 七、参考

- 论文：《自动驾驶系统交通规则符合性仿真验证方法》，王长君等，2022
- 当前架构：`/src/traffic_rule/ARCHITECTURE.md`
