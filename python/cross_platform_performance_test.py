#!/usr/bin/env python3
"""
跨平台GDAL大规模线要素性能测试
支持Windows、macOS、Linux的统一测试框架
"""

import os
import sys
import time
import random
import math
import platform
import tempfile
import shutil
from pathlib import Path

# 尝试导入psutil，如果失败则使用基础系统信息
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: psutil未安装，将使用基础系统信息")

import gc
from osgeo import gdal, ogr, osr

# 明确启用异常处理
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

class CrossPlatformPerformanceTest:
    """跨平台性能测试类"""
    
    def __init__(self, custom_output_dir=None):
        # 跨平台路径处理
        self.platform = platform.system()
        self.setup_output_directory(custom_output_dir)
        
        # 根据平台调整测试参数
        self.adjust_test_parameters()
        
        # 收集系统信息
        self.system_info = self.collect_system_info()
        
        # 显示测试环境信息
        self.display_system_info()
    
    def setup_output_directory(self, custom_output_dir):
        """设置跨平台输出目录"""
        if custom_output_dir:
            self.output_dir = Path(custom_output_dir)
        else:
            # 跨平台的默认目录设置
            if self.platform == "Windows":
                # Windows: 使用用户文档目录
                base_dir = Path.home() / "Documents" / "GDAL_Tests"
            elif self.platform == "Darwin":  # macOS  
                # macOS: 使用用户目录
                base_dir = Path.home() / "Code" / "gdal" / "TryGDAL" / "python" / "test_output"
            else:  # Linux
                # Linux: 使用临时目录或用户目录
                base_dir = Path.home() / "gdal_tests"
            
            self.output_dir = base_dir / "cross_platform_test"
        
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"输出目录: {self.output_dir}")
    
    def adjust_test_parameters(self):
        """根据平台调整测试参数"""
        if self.platform == "Windows":
            # Windows: 相对保守的测试参数（考虑文件系统开销）
            self.test_sizes = [5000, 10000, 15000]
            self.points_per_line = 100
            self.batch_size = 500  # Windows NTFS较小的批处理
            self.transaction_size = 500
            
        elif self.platform == "Darwin":  # macOS
            # macOS: 中等测试参数（利用SSD优势）
            self.test_sizes = [10000, 20000, 30000]
            self.points_per_line = 100
            self.batch_size = 1000
            self.transaction_size = 1000
            
        else:  # Linux
            # Linux: 更激进的测试参数（服务器环境）
            self.test_sizes = [20000, 50000, 100000]
            self.points_per_line = 100
            self.batch_size = 2000
            self.transaction_size = 2000
        
        self.test_formats = ['Shapefile', 'GeoPackage']
    
    def collect_system_info(self):
        """收集跨平台系统信息"""
        info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'gdal_version': gdal.VersionInfo('RELEASE_NAME')
        }
        
        if HAS_PSUTIL:
            info.update({
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total': psutil.virtual_memory().total,
                'disk_free': self.get_disk_free_space()
            })
        else:
            # 基础系统信息
            info.update({
                'cpu_count': os.cpu_count() or 'Unknown',
                'cpu_count_logical': os.cpu_count() or 'Unknown',
                'memory_total': 'Unknown',
                'disk_free': 'Unknown'
            })
        
        # Windows特定信息
        if self.platform == "Windows":
            info['windows_version'] = platform.win32_ver()
            info['file_system'] = 'NTFS (assumed)'
        # macOS特定信息
        elif self.platform == "Darwin":
            info['macos_version'] = platform.mac_ver()
            info['file_system'] = 'APFS/HFS+ (assumed)'
        # Linux特定信息
        else:
            try:
                import distro
                info['linux_distro'] = distro.name(pretty=True)
            except ImportError:
                info['linux_distro'] = 'Unknown'
            info['file_system'] = 'ext4/xfs (assumed)'
        
        return info
    
    def get_disk_free_space(self):
        """获取磁盘可用空间（跨平台）"""
        if HAS_PSUTIL:
            try:
                return psutil.disk_usage(str(self.output_dir.parent)).free
            except:
                pass
        
        # 回退方法
        try:
            if self.platform == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.output_dir.parent)),
                    ctypes.pointer(free_bytes),
                    None, None
                )
                return free_bytes.value
            else:
                statvfs = os.statvfs(str(self.output_dir.parent))
                return statvfs.f_frsize * statvfs.f_bavail
        except:
            return None
    
    def display_system_info(self):
        """显示系统信息"""
        print("跨平台GDAL大规模线要素性能测试")
        print("=" * 60)
        print(f"操作系统: {self.system_info['platform']}")
        print(f"处理器: {self.system_info['processor']}")
        
        if HAS_PSUTIL and isinstance(self.system_info['cpu_count'], int):
            print(f"CPU核心: {self.system_info['cpu_count']} 物理 / {self.system_info['cpu_count_logical']} 逻辑")
        else:
            print(f"CPU核心: {self.system_info['cpu_count']}")
        
        if HAS_PSUTIL and isinstance(self.system_info['memory_total'], int):
            print(f"内存: {self.system_info['memory_total'] / (1024**3):.1f} GB")
        else:
            print(f"内存: {self.system_info['memory_total']}")
        
        if HAS_PSUTIL and isinstance(self.system_info['disk_free'], int):
            print(f"磁盘空间: {self.system_info['disk_free'] / (1024**3):.1f} GB")
        else:
            print(f"磁盘空间: {self.system_info['disk_free']}")
        
        print(f"Python: {self.system_info['python_version']}")
        print(f"GDAL: {self.system_info['gdal_version']}")
        
        # 平台特定信息
        if self.platform == "Windows":
            print(f"Windows版本: {self.system_info.get('windows_version', 'Unknown')}")
        elif self.platform == "Darwin":
            print(f"macOS版本: {self.system_info.get('macos_version', 'Unknown')}")
        else:
            print(f"Linux发行版: {self.system_info.get('linux_distro', 'Unknown')}")
        
        print(f"预估文件系统: {self.system_info.get('file_system', 'Unknown')}")
        print("-" * 60)
        
        # 显示测试参数
        print(f"测试参数 (为{self.platform}优化):")
        print(f"  数据量: {self.test_sizes}")
        print(f"  每线点数: {self.points_per_line}")
        print(f"  批处理大小: {self.batch_size}")
        print(f"  事务大小: {self.transaction_size}")
        print("-" * 60)
    
    def generate_complex_linestring(self, line_id, points_count=100):
        """生成复杂的线要素（跨平台兼容）"""
        # 使用通用的坐标范围（避免特定地区依赖）
        base_lon = 116.0 + (line_id % 1000) * 0.001
        base_lat = 39.4 + (line_id % 1000) * 0.001
        
        line = ogr.Geometry(ogr.wkbLineString)
        
        current_lon = base_lon
        current_lat = base_lat
        
        for i in range(points_count):
            if i == 0:
                line.AddPoint(current_lon, current_lat)
            else:
                angle_change = random.uniform(-math.pi/6, math.pi/6)
                distance = random.uniform(0.0005, 0.002)
                
                current_lon += distance * math.cos(angle_change)
                current_lat += distance * math.sin(angle_change)
                
                current_lon = max(116.0, min(117.0, current_lon))
                current_lat = max(39.4, min(40.6, current_lat))
                
                line.AddPoint(current_lon, current_lat)
        
        # 生成属性（使用ASCII字符以避免编码问题）
        road_types = ['Highway', 'MainRoad', 'SecondaryRoad', 'LocalRoad']
        materials = ['Asphalt', 'Concrete', 'Gravel', 'Dirt']
        
        attributes = {
            'road_id': line_id,
            'name': f'Road_{line_id}',
            'road_type': random.choice(road_types),
            'material': random.choice(materials),
            'width': round(random.uniform(3.0, 50.0), 1),
            'max_speed': random.choice([30, 40, 50, 60, 80, 100, 120]),
            'length_km': round(line.Length() * 111.0, 3),
            'lanes': random.randint(1, 8),
            'year_built': random.randint(1980, 2024),
            'last_maint': random.randint(2010, 2024),
            'traffic': random.randint(100, 50000)
        }
        
        return line, attributes
    
    def test_performance(self):
        """执行跨平台性能测试"""
        print("开始跨平台性能测试...")
        
        all_results = {}
        
        for size in self.test_sizes:
            print(f"\n{'='*50}")
            print(f"测试数据量: {size:,} 个线要素")
            print("="*50)
            
            # 检查资源（如果可用）
            if not self.check_resources(size):
                print(f"⚠️  资源可能不足，但继续测试...")
            
            # 生成测试数据
            print(f"生成 {size:,} 个线要素...")
            start_time = time.perf_counter()
            
            test_data = []
            for i in range(size):
                line, attributes = self.generate_complex_linestring(i, self.points_per_line)
                test_data.append((line, attributes))
                
                # 显示进度
                if (i + 1) % self.batch_size == 0:
                    print(f"  进度: {i+1:,}/{size:,}")
            
            data_gen_time = time.perf_counter() - start_time
            print(f"数据生成完成，耗时: {data_gen_time:.2f}秒")
            
            # 测试各种格式
            size_results = {}
            for format_name in self.test_formats:
                print(f"\n测试 {format_name} 格式...")
                
                try:
                    result = self.test_format_performance(format_name, test_data, size)
                    size_results[format_name] = result
                    self.print_result(format_name, result)
                    
                except Exception as e:
                    print(f"  ❌ {format_name} 测试失败: {e}")
                    import traceback
                    traceback.print_exc()
                    size_results[format_name] = None
            
            all_results[size] = {
                'data_generation_time': data_gen_time,
                'formats': size_results,
                'platform': self.platform
            }
            
            # 清理内存
            del test_data
            gc.collect()
            
            # 显示内存使用（如果可用）
            if HAS_PSUTIL:
                memory_usage = psutil.virtual_memory()
                print(f"\n当前内存使用: {memory_usage.percent:.1f}% ({memory_usage.used/(1024**3):.1f}GB)")
        
        # 生成跨平台分析
        self.analyze_cross_platform_results(all_results)
        
        return all_results
    
    def check_resources(self, size):
        """检查系统资源（跨平台）"""
        if not HAS_PSUTIL:
            return True  # 无法检查，假设足够
        
        try:
            # 估算内存需求
            estimated_memory = size * 1024 * 2
            available_memory = psutil.virtual_memory().available
            
            # 估算磁盘需求
            estimated_disk = size * 2048 * len(self.test_formats) * 2
            disk_free = self.get_disk_free_space()
            
            memory_ok = available_memory > estimated_memory
            disk_ok = disk_free is None or disk_free > estimated_disk
            
            if not memory_ok:
                print(f"  ⚠️  内存可能不足: 需要 {estimated_memory/(1024**3):.1f}GB, 可用 {available_memory/(1024**3):.1f}GB")
            
            if not disk_ok and disk_free is not None:
                print(f"  ⚠️  磁盘空间可能不足: 需要 {estimated_disk/(1024**3):.1f}GB, 可用 {disk_free/(1024**3):.1f}GB")
            
            return memory_ok and disk_ok
            
        except Exception as e:
            print(f"  ⚠️  资源检查失败: {e}")
            return True
    
    def test_format_performance(self, format_name, test_data, size):
        """测试格式性能（跨平台优化）"""
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        
        # 跨平台文件路径处理
        if format_name == 'Shapefile':
            file_path = str(self.output_dir / f"lines_{size}.shp")
        else:
            file_path = str(self.output_dir / f"lines_{size}.gpkg")
        
        results = {}
        
        # 写入测试
        start_memory = self.get_memory_usage()
        start_time = time.perf_counter()
        
        success = self.write_format_cross_platform(format_name, file_path, test_data, srs)
        
        write_time = time.perf_counter() - start_time
        end_memory = self.get_memory_usage()
        
        if not success:
            return {'error': 'Write failed'}
        
        file_size = self.get_file_size_cross_platform(format_name, file_path)
        
        results['write_time'] = write_time
        results['file_size'] = file_size
        results['write_throughput'] = len(test_data) / write_time
        results['memory_used'] = end_memory - start_memory if (end_memory and start_memory) else 0
        
        # 读取测试
        start_time = time.perf_counter()
        feature_count = self.read_file_cross_platform(file_path)
        read_time = time.perf_counter() - start_time
        
        results['read_time'] = read_time
        results['read_throughput'] = feature_count / read_time if read_time > 0 else 0
        results['feature_count'] = feature_count
        
        # 空间查询测试
        start_time = time.perf_counter()
        query_count = self.test_spatial_query_cross_platform(file_path)
        query_time = time.perf_counter() - start_time
        
        results['query_time'] = query_time
        results['query_count'] = query_count
        
        return results
    
    def get_memory_usage(self):
        """获取当前内存使用（跨平台）"""
        if HAS_PSUTIL:
            try:
                return psutil.virtual_memory().used
            except:
                pass
        return None
    
    def write_format_cross_platform(self, format_name, file_path, test_data, srs):
        """跨平台格式写入"""
        try:
            # 清理旧文件
            if format_name == 'Shapefile':
                base_name = os.path.splitext(file_path)[0]
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    related_file = base_name + ext
                    if os.path.exists(related_file):
                        try:
                            os.remove(related_file)
                        except PermissionError:
                            # Windows可能有文件锁定问题
                            time.sleep(0.1)
                            os.remove(related_file)
                
                driver = ogr.GetDriverByName("ESRI Shapefile")
            else:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except PermissionError:
                        time.sleep(0.1)
                        os.remove(file_path)
                driver = ogr.GetDriverByName("GPKG")
            
            if driver is None:
                raise Exception(f"无法获取{format_name}驱动")
            
            # 添加调试信息
            print(f"    创建数据源: {file_path}")
            datasource = driver.CreateDataSource(file_path)
            
            # 检查GDAL错误
            error_msg = gdal.GetLastErrorMsg()
            if error_msg:
                print(f"    GDAL警告/错误: {error_msg}")
            
            # 即使返回None，检查文件是否实际创建
            if datasource is None:
                if os.path.exists(file_path):
                    print(f"    数据源对象为None，但文件已创建，尝试重新打开")
                    datasource = ogr.Open(file_path, 1)  # 以写入模式打开
                
                if datasource is None:
                    raise Exception(f"无法创建数据源: {file_path}, GDAL错误: {error_msg}")
            
            layer = datasource.CreateLayer("roads", srs, ogr.wkbLineString)
            if layer is None:
                # 可能图层已存在，尝试获取
                layer = datasource.GetLayer(0)
                if layer is None:
                    raise Exception(f"无法创建或获取图层, GDAL错误: {gdal.GetLastErrorMsg()}")
            
            # 创建字段（使用简单字段名避免编码问题）
            fields = [
                ("road_id", ogr.OFTInteger),
                ("name", ogr.OFTString),
                ("road_type", ogr.OFTString),
                ("material", ogr.OFTString),
                ("width", ogr.OFTReal),
                ("max_speed", ogr.OFTInteger),
                ("length_km", ogr.OFTReal),
                ("lanes", ogr.OFTInteger),
                ("year_built", ogr.OFTInteger),
                ("last_maint", ogr.OFTInteger),
                ("traffic", ogr.OFTInteger)
            ]
            
            for field_name, field_type in fields:
                field_defn = ogr.FieldDefn(field_name, field_type)
                if field_type == ogr.OFTString:
                    field_defn.SetWidth(50)
                elif field_type == ogr.OFTReal:
                    field_defn.SetPrecision(2)
                layer.CreateField(field_defn)
            
            # 批量写入（使用平台优化的事务大小）
            layer.StartTransaction()
            transaction_count = 0
            
            for i, (geom, attributes) in enumerate(test_data):
                feature = ogr.Feature(layer.GetLayerDefn())
                
                for field_name, value in attributes.items():
                    if layer.GetLayerDefn().GetFieldIndex(field_name) >= 0:
                        feature.SetField(field_name, value)
                
                feature.SetGeometry(geom)
                layer.CreateFeature(feature)
                feature = None
                
                transaction_count += 1
                
                # 根据平台调整事务提交频率
                if transaction_count >= self.transaction_size:
                    layer.CommitTransaction()
                    layer.StartTransaction()
                    transaction_count = 0
            
            # 提交最后的事务
            if transaction_count > 0:
                layer.CommitTransaction()
            
            datasource = None
            return True
            
        except Exception as e:
            print(f"    写入失败: {e}")
            return False
    
    def read_file_cross_platform(self, file_path):
        """跨平台文件读取"""
        if not os.path.exists(file_path):
            return 0
        
        try:
            datasource = ogr.Open(file_path, 0)
            if not datasource:
                return 0
            
            layer = datasource.GetLayer(0)
            if not layer:
                return 0
            
            count = 0
            for feature in layer:
                # 模拟实际使用
                try:
                    _ = feature.GetField("name")
                    geom = feature.GetGeometryRef()
                    if geom:
                        _ = geom.Length()
                    count += 1
                except:
                    # 忽略个别要素错误
                    pass
            
            datasource = None
            return count
            
        except Exception as e:
            print(f"    读取失败: {e}")
            return 0
    
    def test_spatial_query_cross_platform(self, file_path):
        """跨平台空间查询测试"""
        if not os.path.exists(file_path):
            return 0
        
        try:
            datasource = ogr.Open(file_path, 0)
            if not datasource:
                return 0
            
            layer = datasource.GetLayer(0)
            if not layer:
                return 0
            
            # 创建查询区域
            query_geom = ogr.Geometry(ogr.wkbPolygon)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(116.3, 39.8)
            ring.AddPoint(116.5, 39.8)
            ring.AddPoint(116.5, 40.0)
            ring.AddPoint(116.3, 40.0)
            ring.AddPoint(116.3, 39.8)
            query_geom.AddGeometry(ring)
            
            layer.SetSpatialFilter(query_geom)
            count = 0
            for feature in layer:
                count += 1
            
            layer.SetSpatialFilter(None)
            datasource = None
            
            return count
            
        except Exception as e:
            print(f"    空间查询失败: {e}")
            return 0
    
    def get_file_size_cross_platform(self, format_name, file_path):
        """跨平台文件大小获取"""
        try:
            if format_name == 'Shapefile':
                base_name = os.path.splitext(file_path)[0]
                total_size = 0
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    related_file = base_name + ext
                    if os.path.exists(related_file):
                        total_size += os.path.getsize(related_file)
                return total_size
            else:
                return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except Exception as e:
            print(f"    获取文件大小失败: {e}")
            return 0
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 0:
            return "0 B"
        elif size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def print_result(self, format_name, result):
        """打印测试结果"""
        if 'error' in result:
            print(f"  ❌ {format_name} 失败")
            return
        
        print(f"  ✅ {format_name} 结果:")
        print(f"    写入: {result['write_time']:.2f}s ({result['write_throughput']:.0f} 要素/s)")
        print(f"    文件: {self.format_size(result['file_size'])}")
        print(f"    读取: {result['read_time']:.2f}s ({result['read_throughput']:.0f} 要素/s)")
        print(f"    查询: {result['query_time']:.3f}s (找到 {result['query_count']} 要素)")
        if result['memory_used']:
            print(f"    内存: {self.format_size(abs(result['memory_used']))}")
    
    def analyze_cross_platform_results(self, all_results):
        """跨平台结果分析"""
        print(f"\n" + "="*60)
        print(f"{self.platform} 平台性能分析总结")
        print("="*60)
        
        print(f"\n数据量缩放分析:")
        for size in self.test_sizes:
            if size in all_results and 'formats' in all_results[size]:
                formats = all_results[size]['formats']
                print(f"\n{size:,} 要素:")
                
                for format_name in self.test_formats:
                    if format_name in formats and formats[format_name]:
                        result = formats[format_name]
                        if 'error' not in result:
                            throughput = result['write_throughput']
                            file_size_mb = result['file_size'] / (1024 * 1024)
                            read_throughput = result['read_throughput']
                            print(f"  {format_name:12}: 写入 {throughput:6.0f} 要素/s, 读取 {read_throughput:6.0f} 要素/s, {file_size_mb:5.1f} MB")
        
        # 平台特定分析
        self.print_platform_specific_analysis()
        
        # 生成跨平台报告文件
        self.generate_cross_platform_report(all_results)
        
        # 询问是否清理测试数据
        self.offer_data_cleanup(all_results)
    
    def print_platform_specific_analysis(self):
        """打印平台特定分析"""
        print(f"\n{self.platform} 平台特性分析:")
        
        if self.platform == "Windows":
            print("  ✓ 适合桌面GIS开发和最终用户测试")
            print("  ✓ NTFS文件系统，适合大文件操作")
            print("  ⚠️ 文件锁定机制可能影响并发性能")
            print("  ⚠️ 路径长度限制需要注意")
            print("  💡 建议使用SSD以提升I/O性能")
            print("  💡 考虑WSL2获得更好的命令行性能")
            
        elif self.platform == "Darwin":  # macOS
            print("  ✓ 优秀的SSD性能和内存管理")
            print("  ✓ 适合开发环境和原型验证")
            print("  ⚠️ 服务器部署代表性有限")
            print("  ⚠️ Apple Silicon架构兼容性需验证")
            print("  💡 利用统一内存架构优势")
            print("  💡 适合作为开发和测试基准")
            
        else:  # Linux
            print("  ✓ 服务器和云环境的标准选择")
            print("  ✓ 优秀的多线程和I/O性能")
            print("  ✓ 可调优的系统参数")
            print("  ✓ 高性能计算的首选平台")
            print("  💡 建议调优I/O调度器")
            print("  💡 考虑使用大页面内存")
    
    def generate_cross_platform_report(self, all_results):
        """生成跨平台报告"""
        report_path = self.output_dir / f"performance_report_{self.platform.lower()}.md"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# {self.platform} 平台 GDAL 性能测试报告\n\n")
                f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 系统信息
                f.write("## 测试环境\n\n")
                for key, value in self.system_info.items():
                    f.write(f"- **{key}**: {value}\n")
                f.write("\n")
                
                # 测试结果
                f.write("## 测试结果\n\n")
                f.write("| 数据量 | 格式 | 写入时间(s) | 写入吞吐量(要素/s) | 文件大小(MB) | 读取时间(s) | 空间查询(s) |\n")
                f.write("|--------|------|-------------|-------------------|--------------|-------------|-------------|\n")
                
                for size, size_data in all_results.items():
                    if 'formats' in size_data:
                        for format_name in self.test_formats:
                            if format_name in size_data['formats'] and size_data['formats'][format_name]:
                                result = size_data['formats'][format_name]
                                if 'error' not in result:
                                    f.write(f"| {size:,} | {format_name} | {result['write_time']:.2f} | ")
                                    f.write(f"{result['write_throughput']:.0f} | {result['file_size']/(1024*1024):.1f} | ")
                                    f.write(f"{result['read_time']:.2f} | {result['query_time']:.3f} |\n")
                
                f.write(f"\n## 平台特定建议\n\n")
                # 这里可以添加更多平台特定的建议
                
            print(f"\n📊 {self.platform} 平台报告已生成: {report_path}")
            
        except Exception as e:
            print(f"⚠️  报告生成失败: {e}")
    
    def offer_data_cleanup(self, all_results):
        """询问用户是否清理测试数据"""
        print(f"\n" + "="*60)
        print("数据清理选项")
        print("="*60)
        
        # 统计生成的文件
        total_files = 0
        total_size = 0
        test_files = []
        
        for size in all_results.keys():
            if 'formats' in all_results[size]:
                for format_name in self.test_formats:
                    if format_name == 'Shapefile':
                        file_path = self.output_dir / f"lines_{size}.shp"
                        if file_path.exists():
                            test_files.append(self.get_shapefile_files(str(file_path)))
                            total_size += self.get_file_size_cross_platform(format_name, str(file_path))
                    else:  # GeoPackage
                        file_path = self.output_dir / f"lines_{size}.gpkg"
                        if file_path.exists():
                            test_files.append([str(file_path)])
                            total_size += self.get_file_size_cross_platform(format_name, str(file_path))
        
        # 扁平化文件列表
        all_files = []
        for file_group in test_files:
            all_files.extend(file_group)
        
        total_files = len(all_files)
        
        if total_files == 0:
            print("📁 没有发现测试数据文件，无需清理")
            return
        
        print(f"📊 测试数据统计:")
        print(f"  测试文件数量: {total_files} 个")
        print(f"  占用磁盘空间: {self.format_size(total_size)}")
        print(f"  存储位置: {self.output_dir}")
        
        print(f"\n📁 生成的文件类型:")
        shapefile_count = sum(1 for f in all_files if f.endswith(('.shp', '.shx', '.dbf', '.prj')))
        gpkg_count = sum(1 for f in all_files if f.endswith('.gpkg'))
        
        if shapefile_count > 0:
            print(f"  Shapefile相关文件: {shapefile_count} 个")
        if gpkg_count > 0:
            print(f"  GeoPackage文件: {gpkg_count} 个")
        
        print(f"\n🗂️  详细文件列表:")
        for file_path in sorted(all_files):
            try:
                size = os.path.getsize(file_path)
                print(f"  📄 {os.path.basename(file_path):25} {self.format_size(size):>10}")
            except OSError:
                print(f"  📄 {os.path.basename(file_path):25} {'(已删除)':>10}")
        
        # 清理选项
        print(f"\n🧹 清理选项:")
        print(f"  1. 保留所有数据 (继续分析)")
        print(f"  2. 仅清理测试数据文件 (保留报告)")
        print(f"  3. 清理所有文件 (包括报告)")
        print(f"  4. 清理整个测试目录")
        
        try:
            choice = input(f"\n请选择清理选项 [1-4] (默认: 1): ").strip()
            
            if choice == '' or choice == '1':
                print("✅ 保留所有数据，便于后续分析")
                return
            elif choice == '2':
                self.cleanup_test_data_only(all_files)
            elif choice == '3':
                self.cleanup_all_files()
            elif choice == '4':
                self.cleanup_entire_directory()
            else:
                print("⚠️  无效选择，保留所有数据")
                
        except KeyboardInterrupt:
            print("\n⚠️  清理操作被取消，保留所有数据")
        except Exception as e:
            print(f"⚠️  清理操作失败: {e}")
    
    def get_shapefile_files(self, shp_path):
        """获取Shapefile相关的所有文件"""
        base_name = os.path.splitext(shp_path)[0]
        shapefile_extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
        files = []
        
        for ext in shapefile_extensions:
            file_path = base_name + ext
            if os.path.exists(file_path):
                files.append(file_path)
        
        return files
    
    def cleanup_test_data_only(self, test_files):
        """仅清理测试数据文件，保留报告"""
        print(f"\n🧹 清理测试数据文件...")
        
        deleted_count = 0
        deleted_size = 0
        
        for file_path in test_files:
            try:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_size += size
                    print(f"  ✅ 已删除: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ❌ 删除失败: {os.path.basename(file_path)} - {e}")
        
        print(f"\n📊 清理结果:")
        print(f"  删除文件数量: {deleted_count} 个")
        print(f"  释放磁盘空间: {self.format_size(deleted_size)}")
        print(f"  保留报告文件以便后续分析")
        
        # 检查是否还有报告文件
        report_files = list(self.output_dir.glob("*.md"))
        if report_files:
            print(f"  📋 保留的报告: {len(report_files)} 个")
            for report in report_files:
                print(f"    📄 {report.name}")
    
    def cleanup_all_files(self):
        """清理所有文件，包括报告"""
        print(f"\n🧹 清理所有文件...")
        
        if not self.output_dir.exists():
            print("📁 测试目录不存在，无需清理")
            return
        
        deleted_count = 0
        deleted_size = 0
        
        # 删除目录中的所有文件
        for file_path in self.output_dir.iterdir():
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += size
                    print(f"  ✅ 已删除: {file_path.name}")
                except Exception as e:
                    print(f"  ❌ 删除失败: {file_path.name} - {e}")
        
        print(f"\n📊 清理结果:")
        print(f"  删除文件数量: {deleted_count} 个")
        print(f"  释放磁盘空间: {self.format_size(deleted_size)}")
        
        # 如果目录为空，询问是否删除目录
        if not any(self.output_dir.iterdir()):
            try:
                confirm = input(f"目录已为空，是否删除目录? [y/N]: ").strip().lower()
                if confirm == 'y':
                    self.output_dir.rmdir()
                    print(f"  ✅ 已删除目录: {self.output_dir}")
                else:
                    print(f"  📁 保留空目录: {self.output_dir}")
            except Exception as e:
                print(f"  ⚠️  目录删除失败: {e}")
    
    def cleanup_entire_directory(self):
        """清理整个测试目录"""
        print(f"\n🧹 清理整个测试目录...")
        
        if not self.output_dir.exists():
            print("📁 测试目录不存在，无需清理")
            return
        
        # 警告用户
        print(f"⚠️  警告: 这将删除整个目录及其所有内容!")
        print(f"📁 目录路径: {self.output_dir}")
        
        try:
            confirm = input(f"确认删除整个目录? 输入 'DELETE' 确认: ").strip()
            if confirm == 'DELETE':
                import shutil
                
                # 计算目录大小
                total_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(self.output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except OSError:
                            pass
                
                # 删除目录
                shutil.rmtree(self.output_dir)
                
                print(f"  ✅ 已删除目录: {self.output_dir}")
                print(f"  📊 清理统计:")
                print(f"    删除文件数量: {file_count} 个")
                print(f"    释放磁盘空间: {self.format_size(total_size)}")
                
            else:
                print(f"  ⚠️  清理操作已取消")
                
        except Exception as e:
            print(f"  ❌ 目录删除失败: {e}")

def main():
    """主函数"""
    print("跨平台GDAL性能测试工具")
    print("支持 Windows、macOS、Linux")
    print("=" * 50)
    
    # 检查psutil
    if not HAS_PSUTIL:
        print("\n建议安装 psutil 以获得更详细的系统监控:")
        print("  pip install psutil")
        print("  或 conda install psutil")
        print()
    
    try:
        # 可以通过命令行参数指定输出目录
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        
        tester = CrossPlatformPerformanceTest(output_dir)
        results = tester.test_performance()
        
        print(f"\n✅ {platform.system()} 平台测试完成!")
        print("建议在其他平台上运行相同测试以进行对比分析")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()