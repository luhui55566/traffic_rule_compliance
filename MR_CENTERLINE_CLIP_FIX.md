# Fix: Centerline Clipping Bug in Local Map Processing

## 问题描述

**位置**: `src/map_node/localmap/xodrconvert/converter.py:1113-1118`

**症状**: 
- 未裁剪的centerline被错误保留（可能完全超出map_range）
- 导致车道中心线坐标超出300m范围（如-903m）
- 车道连接gap高达800+米（应该是<10m）
- 影响egolane选择和后续处理

**根本原因**:
```python
# Bug代码（第1113-1118行）
if clipped_centerline:
    centerline_points = clipped_centerline
    centerline_s_values = clipped_s_values

# 问题：当clipped_centerline为空列表时，条件为False
# centerline_points保持原值（未裁剪的centerline）
# 导致超出范围的车道被错误添加到local_map
```

**修复方案**:
```python
# 修复后（第1113-1118行）
centerline_points = clipped_centerline
centerline_s_values = clipped_s_values

# 效果：空列表也会被赋值
# 后续检查：if not centerline_points: return fail
# 超出范围的车道被正确过滤
```

## 测试结果

### 修复前（100帧测试）
- **平均gap**: 237.43m ❌
- **最大gap**: 828.46m ❌
- **gap>10m**: 30个连接 ❌

### 修复后（830帧全量测试）
- **平均gap**: 0.95m ✅ (↓99.6%)
- **最大gap**: 7.61m ✅ (↓99.1%)
- **gap>10m**: 0个 ✅ (↓100%)

## Gap分布（修复后）

```
0-1m:   11406 (85.9%) - 大部分连接完美
1-5m:     244 ( 1.8%) - 正常
5-10m:   1626 (12.2%) - road连接处（正常）
>10m:       0 ( 0.0%) - 无异常gap
```

## 技术细节

**修改文件**:
- `src/map_node/localmap/xodrconvert/converter.py` (3行修改)

**影响范围**:
- 车道中心线生成
- 车道过滤逻辑
- 局部地图构建

**性能影响**:
- 减少了无效的车道数量
- 提高了local map质量
- 不影响性能

## 验证工具

创建了测试脚本:
1. `check_lane_connections.py` - 批量检查车道连接gap
2. `visualize_gap_frames.py` - 可视化gap最大的帧

测试覆盖:
- 100帧采样测试 ✓
- 830帧全量测试 ✓

## 建议

**合并**: 矮 高优先级
- 修复了严重的地图数据质量问题
- 影响所有下游任务（路径规划、egolane选择等）
- 无副作用

## 可视化验证

已生成10张gap可视化图片:
- 所有gap在7.45-7.61m范围内
- 都出现在Road 1034 → 770连接处
- 属于正常的road-to-road间隙
