# postpro 当前进度整理（2026-05-07）

这份文档用于快速恢复当前开发上下文。仓库现在处于“重构地基已经搭好，但用户 API 和完整工程包装还未恢复”的阶段。

## 1. 当前目标

当前重构方向已经明确：

- 顶层包名从旧的 `postgenesis` 改为中性的 `postpro`
- Genesis 只是 `postpro.backends.genesis` 里的一个 backend
- 通用能力放在：
  - `postpro.core`
  - `postpro.io`
  - `postpro.numerics`
  - `postpro.utils`
- 旧的 Genesis 专用可视化链路、旧 metadata、兼容层、legacy 代码都已经删除
- 后续计划是：
  - 先把 `MainResults` 主链走通
  - 再视需要推广到 `FieldResults` / `ParticleResults`

## 2. 当前源码结构

现在 `src/postpro/` 主要包含以下模块：

```text
src/postpro/
  __init__.py
  backends/
    genesis/
      __init__.py
      adapters.py
      batch.py
      metric_registry.py
      metrics.py
      models.py
      reader.py
      scan.py
      stats.py
  core/
    __init__.py
    metric.py
    result.py
    study.py
    types.py
  io/
    __init__.py
    hdf5.py
  numerics/
    __init__.py
    c1d.py
    intensity.py
  utils/
    __init__.py
    dataframe.py
    mpl.py
    re.py
    text.py
```

## 3. 已完成的重构

### 3.1 包结构与命名

- 已删除旧包 `src/postgenesis/`
- 已删除 legacy 目录
- 已删除旧兼容层
- 现在只保留 `postpro`

### 3.2 通用 HDF5 读取层

文件：`src/postpro/io/hdf5.py`

已实现：

- `H5MapReader`
- 映射式 HDF5 访问
- 缓存
- 字符串解码
- 直接路径读取

这部分已经替代了旧代码中对 `dstrux.H5Proxy` 的依赖。

### 3.3 数值基础函数

文件：

- `src/postpro/numerics/c1d.py`
- `src/postpro/numerics/intensity.py`

已实现：

- `maximum_from_left`
- `rms_width`
- `fwhm`

这部分已经替代了旧代码中对 `dstrux.Intensity1D` 的依赖。

### 3.4 Genesis backend 拆分

旧的 `core.py / singlecase.py / cluster.py` 已经拆开：

- `reader.py`
  - 低层 Genesis HDF5 版本检查与 reader 基类
- `metrics.py`
  - 频谱计算、nearest lookup 等数值辅助
- `models.py`
  - `MainResults`
  - `FieldResults`
  - `ParticleResults`
- `stats.py`
  - 现在只保留“结果对象输入”的统计接口
- `scan.py`
  - scan 目录发现
  - case manifest 读取
  - `load_study(...)`
- `batch.py`
  - 批量统计入口
- `adapters.py`
  - Genesis model -> core `ResultSet` adapter
- `metric_registry.py`
  - Genesis backend 专用 metric registry

### 3.5 MainResults 的 raw / derived 字段区分

文件：`src/postpro/backends/genesis/models.py`

`MainResults` 现在明确区分：

- `raw_keys`
  - 来自 HDF5 mapping 的原始字段
- `derived_keys`
  - 代码派生字段
- `available_keys`
  - 两者并集

当前 `derived_keys` 包含：

- `file_basename`
- `lslice`
- `mpisize`
- `nslice`
- `nslice_eff`
- `peakpower`
- `seed_label`
- `slice_num`
- `t_from_s`
- `wavelength_spectra_int`
- `wavelength_spectra_wl`
- `zfwhm_fld`
- `zenergy`
- `zpower`
- `zsigmat_fld`

### 3.6 core 抽象第一版

文件：

- `src/postpro/core/result.py`
- `src/postpro/core/metric.py`
- `src/postpro/core/study.py`

已实现：

- `ResultSet` 协议
- `MappingResultSet`
- `Metric` 协议
- `MetricRegistry`
- `compute_many`
- `CaseRecord`
- `Study`
- `Study.evaluate(...)`
- `Study.materialize(...)`
- `CaseRecord.result_loader`

### 3.7 Genesis -> core 主链已经打通

当前已经可以走通这条链：

1. `scan.load_case_records(...)`
2. `scan.load_study(...)`
3. `Study.materialize()`
4. `GenesisResultAdapter`
5. `build_stat_metric_registry(...)`
6. `Study.evaluate(...)`
7. `batch.cluster_statistics(...)`

也就是说，Genesis scan 现在已经能接入 core `Study` 与 `MetricRegistry`，不再是旧式脚本调用。

## 4. 已删除的旧链路

这些已经移除，不再保留兼容：

- 旧 `postgenesis` 包
- 旧 `vizdfscan.py`
- 旧 `singlecase.py`
- 旧 `cluster.py`
- 旧 `comparison.py`
- 旧 Genesis metadata JSON 与对应 `metadata.py`
- 旧基于文件名输入的 `stat_one(...)` / `statistics_at_z(fname, ...)` 这类接口

当前原则是：

- backend 分析层只处理结果对象
- 文件名输入如果未来需要支持，应放在更高层用户 API

## 5. 当前 Genesis backend 对外入口

从 `postpro.backends.genesis` 当前可用的主要入口：

- 结果对象
  - `MainResults`
  - `FieldResults`
  - `ParticleResults`
- adapter
  - `GenesisResultAdapter`
  - `adapt_result(...)`
  - `load_main_result(...)`
- study / scan
  - `discover_case_directories(...)`
  - `load_case_records(...)`
  - `load_study(...)`
- batch
  - `cluster_statistics(...)`
- stats
  - `statistics_at_z(gmr, z)`
  - `statistics_at_max(gmr, ratio2max=...)`
  - `statistics_maxs(gmr)`
- metric registry
  - `build_stat_metric_registry(...)`

## 6. 当前测试状态

当前有两组正式测试：

- `tests/test_genesis_adapter_smoke.py`
- `tests/test_genesis_study_integration.py`

它们已经覆盖：

- 最小 Genesis 风格 `out.h5` 文件构造
- `MainResults` 读取
- `GenesisResultAdapter`
- raw / derived key 区分
- `load_case_records(...)`
- `load_study(...)`
- `Study.materialize(...)`
- `build_stat_metric_registry(...)`
- `cluster_statistics(...)`

最近一次验证命令：

```bash
python -m pytest tests/test_genesis_adapter_smoke.py tests/test_genesis_study_integration.py
```

通过结果：`4 passed`

## 7. 真实文件的单 case 可视化 smoke script

当前没有保留正式的 Genesis 单 case 可视化 API，但有一个手工 smoke script：

- `tests/manual_genesis_singlecase_viz.py`

它会读取：

- `~/simdata/pitz/S2E_ideal_machine/case1/g4.000.out.h5`

并生成几张检查图到：

- `outputs/genesis_case1_viz/`

当前生成过的图片：

- `outputs/genesis_case1_viz/z_overview.png`
- `outputs/genesis_case1_viz/pulse_metrics.png`
- `outputs/genesis_case1_viz/slice_profiles.png`
- `outputs/genesis_case1_viz/spectrum.png`

注意：

- 这不是正式 API
- 也没有接 `paramstudy` metadata / autoscale
- 只是验证当前 `MainResults` 链路在真实文件上能出图

## 8. 当前还没做的事

### 8.1 用户 API 还没有恢复

目前仓库还没有正式的高层用户 API。  
现阶段更多是 backend 和 core 地基。

未来需要新增一层明确的用户 API，例如：

- 从文件路径加载结果
- 生成单 case figure
- 生成 scan dataframe
- 对接 `paramstudy`

### 8.2 paramstudy 还没有真正接入

虽然已经明确未来 metadata / autoscale 要交给 `paramstudy`，但当前还没有真正整合：

- 没有用 `paramstudy` 的 metadata registry
- 没有用 `paramstudy` 的自动单位缩放
- 没有用 `paramstudy` 的 plotting API

### 8.3 单 case 可视化 API 还没有重建

旧 `zoverview` 等函数已经删除。  
未来更合理的做法是：

- 先做 Axes-level plotters
- 再做 Figure-level 组合图

推荐方向：

- `plot_z_pulse_length(ax, result, ...)`
- `plot_z_energy(ax, result, ...)`
- `plot_z_particle_size(ax, result, ...)`
- `plot_z_field_size(ax, result, ...)`
- 再组合成新 `zoverview(...)`

### 8.4 FieldResults / ParticleResults 还没有接入 core 主链

当前 core / adapter / Study / MetricRegistry 主线主要围绕 `MainResults` 展开。  
`FieldResults` 和 `ParticleResults` 还没有系统接入，这部分后续再做。

### 8.5 工程文件尚未恢复

由于之前为了彻底重构做过大清理，目前还缺少一些工程级文件：

- `pyproject.toml`
- `.gitignore`
- 更完整的测试配置

当前测试通过依赖的是：

- 测试文件里手动把 `src/` 加入 `sys.path`

这适合开发阶段，但不适合长期维护。

## 9. 建议的下一步

如果继续开发，建议按这个顺序：

1. 重建单 case 可视化 API
   - 不恢复旧大函数
   - 改做 Axes-level + Figure-level 组合

2. 把单 case 图接上 `paramstudy` 的 metadata / autoscale
   - 统一标签与单位策略

3. 恢复最小工程包装
   - 补 `pyproject.toml`
   - 补基础开发依赖

4. 再考虑 `FieldResults` / `ParticleResults`
   - 等 `MainResults` 路线稳定后推广

## 10. 当前最重要的判断

当前仓库已经不是旧工具箱了，而是一套新的骨架：

- 通用 HDF5 读取层：已就位
- core 抽象：第一版已就位
- Genesis backend：主链已打通
- 旧兼容与旧可视化：已基本清掉

也就是说，现在最适合进入的开发阶段是：

**开始建设新的用户层，而不是继续回补旧接口。**
