# 滑屏宏功能 — 设计文档

**日期**: 2026-06-01
**版本**: AutoGame 3.3.2

## 概述

在 JSON 宏系统中新增"滑屏"功能类型，通过 scrcpy 在手机投屏上执行触摸滑动。核心应用场景：QQ飞车瞬侧操作。

## 核心设计原则

**手指不抬起**：滑动复用方向键已有的触摸指针（pointer_id），全程只发 MOVE 事件，不发送 DOWN/UP。模拟真实手指在按住方向键的同时快速侧滑。

## JSON 配置格式

```json
{
    "备注": "左瞬侧",
    "功能类型": "滑屏",
    "触发键": "E",
    "关联方向键": "A",
    "滑动方向": "左",
    "滑动距离": "0.25",
    "滑动时长": "60",
    "位置偏移": "0.015",
    "时长偏移": "10"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 功能类型 | string | 是 | 固定值 `"滑屏"` |
| 触发键 | string | 是 | 触发滑动的按键 |
| 关联方向键 | string | 是 | 复用哪个方向键的触摸指针（如 A、D） |
| 滑动方向 | string | 是 | `"左"` 或 `"右"` |
| 滑动距离 | float | 是 | 归一化距离（0.0~1.0），相对于屏幕宽度 |
| 滑动时长 | float | 是 | 毫秒，瞬侧建议 50~100ms |
| 位置偏移 | float | 否 | 起点随机偏移范围，防检测，默认 0 |
| 时长偏移 | float | 否 | 时长随机波动范围，防检测，默认 0 |

## 执行流程

```
触发键按下 → macro._macro_trigger()
  → 匹配到"滑屏"功能
  → 新线程执行 macro._screen_swipe()
    → 校验参数
    → 校验按键映射已启用
    → key_mapping_executor.execute_screen_swipe()
      → 查找关联方向键的活跃 pointer_id
      → 应用随机位置偏移和时长偏移
      → 计算目标坐标（起点 + 方向向量 × 距离）
      → scrcpy_manager.execute_direction_swipe()
        → 提交协程到事件循环
        → 沿路径发送 MOVE 事件序列（不发送 UP）
        → 返回最终坐标
      → 更新按键映射中的指针位置
```

## 关键实现细节

### scrcpy_manager.execute_direction_swipe
- 同步方法，内部提交协程到事件循环并等待完成
- 每 ~5ms 发送一个 MOVE 事件，保证滑动流畅
- 超时时间 2 秒

### key_mapping_executor.execute_screen_swipe
- 从 `_down_state_keys` 获取关联方向键的 (`pointer_id`, `x`, `y`)
- 如果方向键未按下，返回错误
- 随机偏移在起点坐标和时长上叠加
- 滑动完成后更新存储的指针位置

### macro._screen_swipe
- 在独立线程中运行（由 `_macro_trigger` 启动）
- 不阻塞钩子监听器
- 需要 key_mapping_executor 已启用（即按键映射已应用）

## 改动文件

| 文件 | 改动 |
|------|------|
| `src/scrcpy_manager.py` | 新增 `execute_direction_swipe` 和 `_execute_direction_swipe_async` |
| `src/key_mapping_executor.py` | 新增 `execute_screen_swipe` |
| `src/macro.py` | 新增 `_screen_swipe`，注册到 `function_mapping_down` 和 `function_names` |

## 前置条件

- scrcpy 投屏已连接
- 按键映射已应用（包含 A/D 方向键配置）
- 关联方向键处于按下状态（按住 A 或 D 时触发的滑屏才能正确执行）
