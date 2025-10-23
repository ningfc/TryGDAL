# TryGDAL - GDAL性能测试框架

一个全面的GDAL/OGR性能测试和评估框架，支持跨平台（Windows、macOS、Linux）的大规模地理数据处理性能测试。

## 项目概述

本项目从简单的GDAL API试验开始，发展成为一套完整的GDAL性能测试框架，用于测试和评估GDAL在不同平台、不同数据格式下的性能表现，特别针对大规模线要素数据的读写性能进行了深入测试。

## 主要特性

- 🌍 **跨平台支持**: Windows、macOS、Linux全平台兼容
- 📊 **多格式测试**: Shapefile、GeoPackage等主流GIS格式  
- 🎯 **智能适配**: 根据平台特性自动优化测试参数
- 📈 **性能监控**: 实时监控内存、磁盘、CPU使用情况
- 📋 **详细报告**: 自动生成平台特定的性能分析报告
- 🔧 **灵活配置**: 可自定义测试数据量、几何复杂度等参数

## 项目结构

```
TryGDAL/
├── python/                                    # Python测试脚本
│   ├── cross_platform_performance_test.py    # 🔥 跨平台主测试框架
│   ├── windows_gdal_optimizer.py             # Windows环境优化器
│   ├── test_shapefile_geometry.py            # Shapefile几何类型测试
│   ├── comprehensive_performance_test.py     # 综合性能测试
│   ├── large_scale_demo_test.py              # 大规模测试演示版
│   ├── quick_test.py                         # 快速验证GDAL安装和基本功能
│   ├── layer_types_test.py   # 完整的图层类型测试程序
│   └── test_output/          # 测试输出文件目录
└── cpp/             # C++版本的测试代码（待实现）
```

## Python环境设置

推荐使用conda环境，特别是CV（Computer Vision）环境：

```bash
# 激活conda CV环境
conda activate cv

# 安装GDAL（如果尚未安装）
conda install -c conda-forge gdal
```

## 使用方法

### 1. 快速验证

首先运行快速测试来验证GDAL是否正确安装：

```bash
cd python
python quick_test.py
```

### 2. 完整图层类型测试

运行完整的图层类型测试程序：

```bash
python layer_types_test.py
```

## 测试内容

### 图层类型验证

程序会测试以下几何图形类型：
- Point（点）
- LineString（线）
- Polygon（多边形）
- MultiPoint（多点）
- MultiLineString（多线）
- MultiPolygon（多多边形）
- GeometryCollection（几何集合）
- 3D几何类型（如果支持）

### 输出格式测试

程序会测试以下输出格式：
- ESRI Shapefile (.shp)
- GeoJSON (.geojson)
- GeoPackage (.gpkg)
- Memory (内存格式)

### 支持的驱动程序

程序会列出所有支持的OGR驱动程序，帮助了解GDAL的完整功能。

## 输出文件

测试完成后，会在 `python/test_output/` 目录下生成以下文件：
- `test_layers.shp` (及相关文件)
- `test_layers.geojson`
- `test_layers.gpkg`

## 常见问题

### GDAL兼容性警告

如果遇到以下警告：
```
FutureWarning: Neither osr.UseExceptions() nor osr.DontUseExceptions() has been explicitly called. In GDAL 4.0, exceptions will be enabled by default.
```

这已经在所有程序中修复。所有程序都在导入GDAL后明确调用了：
```python
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()
```

### Z坐标警告

可能会看到关于Z坐标的警告（特别是在GPKG格式中）：
```
Warning 1: Layer has been declared with non-Z geometry type Point, but it does contain geometries with Z.
```

这是正常的，因为我们的几何体包含Z坐标（高度），但图层声明为2D类型。这不影响功能。

### GDAL导入失败

如果遇到导入错误，请确保：
1. 已安装GDAL Python绑定
2. 环境变量设置正确
3. 使用正确的Python环境

安装命令：
```bash
# 使用conda（推荐）
conda install -c conda-forge gdal

# 或使用pip
pip install gdal
```

### 版本兼容性

不同版本的GDAL可能支持不同的功能和格式。程序会显示当前GDAL版本信息。

## 扩展计划

- [ ] 实现C++版本的测试程序
- [ ] 添加更多几何类型测试
- [ ] 测试空间参考系统
- [ ] 添加性能测试
- [ ] 测试不同的坐标变换

## 依赖项

- Python 3.6+
- GDAL Python绑定
- conda环境（推荐）