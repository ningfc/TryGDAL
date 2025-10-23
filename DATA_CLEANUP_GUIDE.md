# GDAL测试数据清理工具使用说明

## 概述

为了方便管理GDAL测试过程中产生的大量数据文件，项目提供了完整的数据清理功能，包括独立的清理工具和集成到各测试脚本的清理选项。

## 清理工具介绍

### 1. 独立清理工具 (`cleanup_test_data.py`)

**功能**: 交互式的完整清理工具，提供详细的文件扫描和多种清理选项

**使用方法**:
```bash
python cleanup_test_data.py
```

**特性**:
- 📊 详细的文件扫描和统计
- 🎯 多种清理模式选择
- 📁 按目录分类显示
- 🔍 文件大小智能显示
- ⚠️ 安全的删除确认

**清理选项**:
1. **仅清理数据文件** - 删除 .shp, .gpkg, .geojson 等数据文件，保留报告
2. **仅清理报告文件** - 删除 .md, .txt, .log 等报告文件，保留数据
3. **清理所有文件** - 删除所有测试相关文件
4. **选择性清理** - 按目录选择要清理的内容
5. **清理整个test_output目录** - 删除整个测试输出目录

### 2. 清理功能模块 (`test_data_cleaner.py`)

**功能**: 提供清理功能的Python模块，供其他脚本导入使用

**主要函数**:
```python
# 快速清理当前目录的数据文件
quick_cleanup_current_dir(auto_confirm=False)

# 完全清理当前目录（包括报告）
full_cleanup_current_dir(auto_confirm=False)

# 自定义清理
cleanup_gdal_test_data(base_dir, auto_confirm=False, include_reports=False)

# 清理整个输出目录
cleanup_test_output_directory(output_dir, auto_confirm=False)
```

### 3. 集成清理功能

**已集成清理功能的测试脚本**:
- `layer_types_test.py` - 图层类型测试
- `test_shapefile_geometry.py` - Shapefile几何类型测试
- `performance_test.py` - 性能对比测试
- `cross_platform_performance_test.py` - 跨平台性能测试
- `large_scale_demo_test.py` - 大规模测试演示
- `comprehensive_performance_test.py` - 综合性能测试

**使用方式**: 测试完成后会自动询问是否清理数据

## 支持的文件类型

### 数据文件
- **Shapefile**: `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`
- **GeoPackage**: `.gpkg`
- **GeoJSON**: `.geojson`
- **KML**: `.kml`, `.kmz`
- **GML**: `.gml`
- **临时文件**: `.tmp`, `.temp`

### 报告文件
- **Markdown**: `.md`
- **文本**: `.txt`
- **日志**: `.log`

## 使用示例

### 场景1: 测试完成后快速清理

```bash
# 运行任意测试脚本
python layer_types_test.py

# 测试完成后会提示:
# 🧹 测试完成！是否清理生成的测试数据？
# 清理测试数据文件? (y/n): y
```

### 场景2: 使用独立清理工具

```bash
python cleanup_test_data.py

# 输出示例:
# GDAL测试数据清理工具
# ==================================================
# 📊 测试数据扫描结果:
#   测试目录数量: 3 个
#   数据文件总大小: 347.4 MB
#   报告文件总大小: 15.2 KB
#   总占用空间: 347.4 MB
#
# 🧹 清理选项:
#   1. 仅清理数据文件 (保留报告)
#   2. 仅清理报告文件 (保留数据)
#   3. 清理所有文件
#   4. 选择性清理目录
#   5. 清理整个test_output目录
#   0. 不清理，退出
```

### 场景3: 在自定义脚本中使用

```python
from test_data_cleaner import quick_cleanup_current_dir, full_cleanup_current_dir

# 快速清理数据文件
if quick_cleanup_current_dir():
    print("清理完成")

# 完全清理（包括报告）
full_cleanup_current_dir(auto_confirm=True)  # 自动确认模式
```

### 场景4: 清理特定目录

```python
from test_data_cleaner import cleanup_test_output_directory
from pathlib import Path

output_dir = Path("test_output")
cleanup_test_output_directory(output_dir, auto_confirm=False)
```

## 安全特性

### 1. 确认机制
- 所有删除操作都需要用户确认
- 支持自动确认模式（适合脚本使用）
- 整个目录删除需要输入 "DELETE" 确认

### 2. 详细信息
- 显示将要删除的文件列表
- 计算并显示文件大小
- 显示清理结果统计

### 3. 错误处理
- 优雅处理文件权限问题
- 显示具体的错误信息
- 支持 Ctrl+C 中断操作

## 清理统计示例

```
📊 清理结果 (数据文件):
  删除文件数量: 119 个
  释放磁盘空间: 347.4 MB
  ✅ 清理完成
```

## 注意事项

1. **备份重要数据**: 清理前请确认不需要保留的测试数据
2. **权限问题**: 确保有删除文件的权限
3. **运行位置**: 建议在项目根目录运行清理工具
4. **自动模式**: 自动确认模式下不会再次询问，请谨慎使用

## 测试验证

项目包含 `test_cleanup_tool.py` 用于验证清理功能:

```bash
python test_cleanup_tool.py
```

该脚本会:
1. 创建测试文件
2. 验证清理功能
3. 清理测试产生的文件
4. 显示详细的测试结果

## 故障排除

### 问题1: 导入错误
**现象**: `ImportError: No module named 'test_data_cleaner'`
**解决**: 确保在正确的目录运行，或检查Python路径

### 问题2: 权限错误
**现象**: `PermissionError: [Errno 13] Permission denied`
**解决**: 检查文件权限，确保有删除权限

### 问题3: 文件被占用
**现象**: 删除失败，文件仍然存在
**解决**: 关闭可能占用文件的程序（如QGIS、ArcGIS等）

## 更新日志

- **2024-12-19**: 添加完整的数据清理功能
  - 独立清理工具
  - 清理功能模块
  - 集成到所有主要测试脚本
  - 完善的安全机制和用户体验