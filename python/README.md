# GDAL跨平台大规模性能测试

本项目提供了一个全面的GDAL性能测试框架，支持Windows、macOS和Linux平台，用于测试1万到100万线要素的读写性能。

## 支持的平台

| 平台 | 状态 | 特点 | 建议用途 |
|------|------|------|----------|
| **Windows** | ✅ 完全支持 | 桌面GIS标准平台 | 最终用户体验测试 |
| **macOS** | ✅ 完全支持 | 开发环境优化 | 原型开发和验证 |
| **Linux** | ✅ 完全支持 | 服务器环境标准 | 生产部署基准测试 |

## 功能特点

- 🔄 **跨平台兼容**: 自动适配不同操作系统的特性
- 📊 **性能监控**: 实时监控内存、磁盘使用情况
- 🎯 **智能优化**: 根据平台特性自动调整测试参数
- 📈 **多格式支持**: 测试Shapefile和GeoPackage性能对比
- 📋 **详细报告**: 生成平台特定的性能分析报告
- 🛡️ **错误处理**: 完善的异常处理和恢复机制

## 环境要求

### 通用要求
```bash
Python 3.7+
GDAL Python绑定 (osgeo)
```

### 可选依赖（推荐安装）
```bash
psutil  # 系统监控，强烈推荐
```

## 平台特定安装指南

### Windows安装

#### 方法1: 使用OSGeo4W (推荐)
```cmd
# 下载OSGeo4W安装器
# https://trac.osgeo.org/osgeo4w/

# 在OSGeo4W Shell中运行:
pip install psutil
```

#### 方法2: 使用Conda
```cmd
conda install -c conda-forge gdal psutil
```

#### 方法3: 使用pip (需要预先安装GDAL)
```cmd
pip install gdal psutil
```

### macOS安装

#### 使用Conda (推荐)
```bash
conda create -n gdal_test python=3.9
conda activate gdal_test
conda install -c conda-forge gdal psutil
```

#### 使用Homebrew
```bash
brew install gdal
pip install psutil
```

### Linux安装

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev python3-gdal
pip3 install psutil
```

#### CentOS/RHEL/Fedora
```bash
sudo yum install gdal gdal-devel gdal-python3
# 或 sudo dnf install gdal gdal-devel python3-gdal
pip3 install psutil
```

#### 从源码编译 (高性能)
```bash
# 参考GDAL官方文档编译优化版本
# https://gdal.org/development/cmake.html
```

## 使用方法

### 基础使用

#### 1. 克隆或下载项目文件

#### 2. 选择运行方式

**通用方式 (所有平台):**
```bash
python cross_platform_performance_test.py
```

**指定输出目录:**
```bash
python cross_platform_performance_test.py /path/to/output
```

### Windows特定使用

#### 方法1: 批处理脚本 (最简单)
```cmd
# 双击运行
run_gdal_test.bat
```

#### 方法2: PowerShell脚本
```powershell
# 以管理员权限运行PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\run_gdal_test.ps1
```

#### 方法3: 优化配置后运行
```cmd
# 先运行优化配置
python windows_gdal_optimizer.py

# 然后运行测试
python cross_platform_performance_test.py
```

### macOS特定使用

```bash
# 确保使用正确的Python环境
conda activate gdal_test  # 如果使用conda

# 运行测试
python cross_platform_performance_test.py
```

### Linux特定使用

```bash
# 对于大规模测试，建议先调优系统
echo deadline > /sys/block/sda/queue/scheduler  # 调优I/O调度器
echo 1 > /proc/sys/vm/drop_caches              # 清理缓存

# 运行测试
python cross_platform_performance_test.py
```

## 测试参数说明

### 平台自适应参数

| 平台 | 测试数据量 | 批处理大小 | 事务大小 | 优化重点 |
|------|------------|------------|----------|----------|
| Windows | 5K, 10K, 15K | 500 | 500 | NTFS优化 |
| macOS | 10K, 20K, 30K | 1000 | 1000 | SSD性能 |
| Linux | 20K, 50K, 100K | 2000 | 2000 | 服务器性能 |

### 手动调整参数

可以通过修改代码中的以下参数来自定义测试:

```python
# 在 CrossPlatformPerformanceTest.__init__() 中
self.test_sizes = [10000, 50000, 100000]  # 测试数据量
self.points_per_line = 100                # 每条线的点数
self.batch_size = 1000                    # 批处理大小
self.transaction_size = 1000              # 事务大小
```

## 输出文件说明

### 测试结果文件

测试会在输出目录中生成以下文件:

```
output_directory/
├── lines_10000.shp          # Shapefile格式测试数据
├── lines_10000.gpkg         # GeoPackage格式测试数据
├── performance_report_windows.md   # Windows平台报告
├── performance_report_darwin.md    # macOS平台报告
└── performance_report_linux.md     # Linux平台报告
```

### 报告内容

每个报告包含:
- 系统环境信息
- 详细性能指标表格
- 平台特定分析
- 优化建议

## 性能基准参考

### 典型性能表现

| 数据量 | 平台 | 格式 | 写入速度 | 读取速度 | 文件大小 |
|--------|------|------|----------|----------|----------|
| 10K线要素 | Windows | Shapefile | ~8K 要素/s | ~30K 要素/s | ~18MB |
| 10K线要素 | Windows | GeoPackage | ~7K 要素/s | ~35K 要素/s | ~40MB |
| 10K线要素 | macOS | Shapefile | ~12K 要素/s | ~48K 要素/s | ~17MB |
| 10K线要素 | macOS | GeoPackage | ~11K 要素/s | ~49K 要素/s | ~40MB |
| 10K线要素 | Linux | Shapefile | ~15K 要素/s | ~60K 要素/s | ~17MB |
| 10K线要素 | Linux | GeoPackage | ~13K 要素/s | ~65K 要素/s | ~40MB |

*注: 性能会因硬件配置而异*

## 故障排除

### 常见问题

#### 1. GDAL导入失败
```python
ImportError: No module named 'osgeo'
```

**解决方案:**
- Windows: 使用OSGeo4W或重新安装GDAL
- macOS: `conda install -c conda-forge gdal`
- Linux: `sudo apt-get install python3-gdal`

#### 2. 权限错误 (Windows)
```
PermissionError: [Errno 13] Permission denied
```

**解决方案:**
- 以管理员权限运行
- 选择有写权限的输出目录
- 关闭防病毒软件实时扫描

#### 3. 内存不足
```
MemoryError: Unable to allocate memory
```

**解决方案:**
- 减少测试数据量
- 增加虚拟内存
- 使用64位Python

#### 4. 路径长度限制 (Windows)
```
OSError: [Errno 22] Invalid argument
```

**解决方案:**
- 启用Windows长路径支持
- 使用较短的输出目录路径
- 移动到根目录运行

### 性能优化建议

#### Windows优化
1. 使用SSD存储
2. 增加虚拟内存到物理内存的2倍
3. 将测试目录添加到防病毒排除列表
4. 使用高性能电源模式

#### macOS优化
1. 充分利用统一内存架构
2. 使用原生编译的GDAL版本
3. 关闭不必要的后台应用
4. 使用Activity Monitor监控资源

#### Linux优化
1. 调优I/O调度器: `echo deadline > /sys/block/sda/queue/scheduler`
2. 启用大页面: `echo always > /sys/kernel/mm/transparent_hugepage/enabled`
3. 增加文件描述符限制: `ulimit -n 65536`
4. 使用高性能文件系统如XFS

## 扩展和定制

### 添加新的测试格式

```python
# 在test_formats列表中添加
self.test_formats = ['Shapefile', 'GeoPackage', 'GeoJSON', 'FlatGeobuf']

# 在write_format_cross_platform方法中添加处理逻辑
elif format_name == 'GeoJSON':
    driver = ogr.GetDriverByName("GeoJSON")
```

### 自定义几何类型测试

```python
def generate_polygon_features(self, count):
    """生成面要素测试数据"""
    # 实现面要素生成逻辑
    pass

def generate_point_features(self, count):
    """生成点要素测试数据"""
    # 实现点要素生成逻辑
    pass
```

### 添加并发测试

```python
import threading
import multiprocessing

def concurrent_write_test(self):
    """并发写入测试"""
    # 实现多进程/多线程写入测试
    pass
```

## 贡献和反馈

### 报告问题
如果遇到问题，请提供以下信息:
1. 操作系统版本
2. Python版本
3. GDAL版本
4. 错误信息和堆栈跟踪
5. 测试参数

### 性能数据分享
欢迎分享不同平台的性能测试结果，帮助建立更完善的性能基准数据库。

## 许可证

本项目基于 MIT 许可证开源。

## 参考资料

- [GDAL官方文档](https://gdal.org/)
- [OGR Python API](https://gdal.org/python/)
- [跨平台Python开发最佳实践](https://docs.python.org/3/library/os.html)
- [GIS数据格式性能比较](https://github.com/OSGeo/gdal)

---

**版本**: 1.0.0  
**更新时间**: 2024年10月24日  
**维护者**: GDAL测试团队