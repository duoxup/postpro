# postpro Roadmap

## 目标

把当前仓库重构成一个以 `postpro` 为核心的、可扩展的后处理框架：

- `postpro.core`
  提供 solver-agnostic 抽象
- `postpro.io`
  提供底层文件读取能力
- `postpro.backends.<solver>`
  提供具体仿真器支持
- 可视化和用户 API 建立在这些地基之上，而不是直接绑在某个旧 backend 脚本上

当前唯一在建 backend 是：

- `postpro.backends.genesis`

## 设计原则

- 不保留旧 `postgenesis` 兼容层
- 不保留 legacy 代码
- backend 分析层只处理结果对象，不直接吃文件名
- 文件名输入如果需要，应放在用户 API 层
- 单 case 图和 scan 图后续统一往 `paramstudy` 生态靠拢

## 当前里程碑

### 已完成

1. 包结构重建
- 旧 `postgenesis` 包已删除
- 当前源码集中在 `src/postpro/`

2. 通用 HDF5 读取层
- 已实现 `postpro.io.H5MapReader`
- 已移除对 `dstrux.H5Proxy` 的依赖

3. 通用数值基础
- 已实现 `rms_width` / `fwhm`
- 已移除对 `dstrux.Intensity1D` 的依赖

4. Genesis backend 拆分
- `reader.py`
- `metrics.py`
- `models.py`
- `stats.py`
- `scan.py`
- `batch.py`
- `adapters.py`
- `metric_registry.py`

5. MainResults 主链打通
- `MainResults`
- `GenesisResultAdapter`
- core `ResultSet`
- core `CaseRecord`
- core `Study`
- Genesis `MetricRegistry`
- `cluster_statistics(...)`

6. 字段语义明确化
- `MainResults.raw_keys`
- `MainResults.derived_keys`
- `MainResults.available_keys`

7. 基础测试
- 最小 Genesis 风格 `out.h5` 格式级 smoke test 已建立
- Genesis scan -> Study -> MetricRegistry 集成测试已建立

8. 单 case 绘图主链
- 已实现 `plot_series.py`
- 已实现 `plot_axes.py`
- 已实现 `plot_figures.py`
- 已实现 Genesis 用户 API：
  - `render_zoverview(...)`
  - `render_pulse_metrics(...)`
  - `render_slice_diagnostics(...)`
  - `render_spectrum(...)`

9. 单 case 元数据与缩放
- 已实现 Genesis 默认 `MainResults` plot metadata
- 已把单 case 图的标签、单位和自动缩放接到 `paramstudy`
- 当前支持用户通过额外 metadata 覆盖默认定义

10. Scan 用户层起步
- 已实现 `collect_scan_rows(...)`
- 已实现 `collect_scan_table(...)`
- 当前输出格式是适合 `paramstudy` 的一行一个 case 结果表

11. ASTRA backend 起步
- 已实现 `postpro.backends.astra`（模型 / adapter / metric registry / scan）
- 已实现 `postpro.api.astra.collect_scan_rows / collect_scan_table`
- 统计量来自 `partdist.compute_beam_diagnostics`（软依赖）
- scan manifest 与并行评估逻辑已提升为 genesis / astra 共享层

### 当前状态

当前仓库已经完成“地基阶段”的大部分工作。  
它已经不再是旧脚本集合，而是一套可以继续往用户 API 和可视化层推进的新骨架。

## 下一阶段

### 阶段 1：重建单 case 用户层

当前状态：
- `MainResults` 的单 case 数据提取、Axes-level、Figure-level 和用户 API 已全部打通
- 当前缺的不是基本出图能力，而是标签/单位/自动缩放体系

已完成内容：
- `plot_z_pulse_length(...)`
- `plot_z_energy(...)`
- `plot_z_particle_size(...)`
- `plot_z_field_size(...)`
- `plot_slice_current(...)`
- `plot_slice_bunching(...)`
- `plot_spectrum(...)`
- `zoverview(...)`
- `render_zoverview(...)`

剩余工作：
- 把这套单 case 图的标签、单位和自动缩放接到 `paramstudy`
- 根据实际使用反馈，微调 figure 组合方式和 API 参数

### 阶段 2：接入 paramstudy 元数据与自动缩放

当前状态：
- Genesis `MainResults` 单 case 图已经接入 `paramstudy`
- 默认 metadata 已覆盖全部 `MainResults` key
- 已知物理量已填入默认单位和部分 preferred unit

剩余工作：
- 继续补全不确定字段的物理单位
- 决定是否把同样的 metadata/缩放机制推广到后续 `FieldResults` / `ParticleResults`
- 后续 scan 图继续统一走 `paramstudy` 原生 API

### 阶段 3：重建 scan / multi-case 用户层

当前状态：
- Genesis scan 目录已经可以直接产出一行一个 case 的结果表
- 当前仍是最小版本，主要覆盖统计量收集，不涉及 scan 图封装

剩余工作：
- 继续扩充 scan metric 体系
- 决定是否提供更高层的 `paramstudy` 对接辅助
- 用真实服务器结果验证 scan 表结构和列命名

### 阶段 4：恢复最小工程包装

目标：
- 让项目重新具备可安装、可测试、可持续开发的基础工程能力

需要恢复：
- `pyproject.toml`
- 基础依赖声明
- 测试运行约定
- 可能的 lint/format 配置

### 阶段 5：扩展其他结果类型

目标：
- 在 `MainResults` 路线稳定后，再把同样的抽象推广到：
  - `FieldResults`
  - `ParticleResults`

当前不着急做，因为 `MainResults` 主链已经证明这套方向成立。

## 明确暂缓的事项

以下内容当前不优先：

- 恢复旧版 `zoverview` 的原始实现方式
- 恢复旧 `vizcomp` / `singlecase` / `cluster` 风格接口
- 为兼容旧调用习惯保留文件名输入统计函数
- 先做 `FieldResults` / `ParticleResults` 的完整 core 集成

## 现在可用的主路径

当前最重要、已经可工作的主路径是：

1. Genesis HDF5 文件
2. `MainResults`
3. `GenesisResultAdapter`
4. core `Study`
5. Genesis `MetricRegistry`
6. `Study.evaluate(...)`
7. `cluster_statistics(...)`

这是后续用户 API 和可视化层应当建立的基础。

## 参考文档

更详细的当前状态说明见：

- [current-status-2026-05-07.md](/home/duoxup/git_agent/postpro/docs/current-status-2026-05-07.md)
