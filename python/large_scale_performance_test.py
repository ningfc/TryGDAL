#!/usr/bin/env python3
"""
大规模线要素性能测试
测试从1万到100万线要素，每个要素包含100个点
改进的跨平台测试方案
"""

import os
import sys
import time
import random
import math
import platform
import psutil
import gc
from osgeo import gdal, ogr, osr

# 明确启用异常处理
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

class LargeScalePerformanceTest:
    """大规模性能测试类"""
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/large_scale_test"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 收集系统信息
        self.system_info = self.collect_system_info()
        
        # 测试配置
        self.test_sizes = list(range(10000, 1100000, 100000))  # 10万到100万，步长10万
        self.points_per_line = 100
        self.test_formats = ['Shapefile', 'GeoPackage']
        
        # 性能监控
        self.memory_usage = []
        self.cpu_usage = []
        
    def collect_system_info(self):
        """收集系统信息用于跨平台分析"""
        info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'disk_free': psutil.disk_usage(os.path.expanduser('~')).free,
            'gdal_version': gdal.VersionInfo('RELEASE_NAME')
        }
        return info
    
    def print_system_info(self):
        """打印系统信息"""
        print("系统信息:")
        print("=" * 50)
        print(f"操作系统: {self.system_info['platform']}")
        print(f"处理器: {self.system_info['processor']}")
        print(f"CPU核心: {self.system_info['cpu_count']} 物理 / {self.system_info['cpu_count_logical']} 逻辑")
        print(f"内存: {self.system_info['memory_total'] / (1024**3):.1f} GB")
        print(f"磁盘空间: {self.system_info['disk_free'] / (1024**3):.1f} GB")
        print(f"Python: {self.system_info['python_version']}")
        print(f"GDAL: {self.system_info['gdal_version']}")
        print("-" * 50)
    
    def generate_complex_linestring(self, line_id, points_count=100):
        """生成复杂的线要素（模拟真实道路网络）"""
        # 基于北京市范围生成复杂路网
        base_lon = 116.0 + (line_id % 1000) * 0.001  # 分散起点
        base_lat = 39.4 + (line_id % 1000) * 0.001
        
        line = ogr.Geometry(ogr.wkbLineString)
        
        current_lon = base_lon
        current_lat = base_lat
        
        # 生成具有真实特征的线段
        for i in range(points_count):
            # 模拟道路的弯曲和方向变化
            if i == 0:
                # 起点
                line.AddPoint(current_lon, current_lat)
            else:
                # 添加随机转向和距离
                angle_change = random.uniform(-math.pi/6, math.pi/6)  # 最大30度转向
                distance = random.uniform(0.0005, 0.002)  # 50-200米距离
                
                # 计算下一个点
                current_lon += distance * math.cos(angle_change)
                current_lat += distance * math.sin(angle_change)
                
                # 确保在合理范围内
                current_lon = max(116.0, min(117.0, current_lon))
                current_lat = max(39.4, min(40.6, current_lat))
                
                line.AddPoint(current_lon, current_lat)
        
        # 生成复杂属性（模拟真实道路信息）
        road_types = ['高速公路', '主干道', '次干道', '支路', '小区道路']
        road_materials = ['沥青', '水泥', '石子', '土路']
        
        attributes = {
            'road_id': line_id,
            'name': f'Road_{line_id}',
            'road_type': random.choice(road_types),
            'material': random.choice(road_materials),
            'width': round(random.uniform(3.0, 50.0), 1),
            'max_speed': random.choice([30, 40, 50, 60, 80, 100, 120]),
            'length_km': round(line.Length() * 111.0, 3),  # 粗略转换为公里
            'lanes': random.randint(1, 8),
            'construction_year': random.randint(1980, 2024),
            'last_maintenance': random.randint(2010, 2024),
            'traffic_flow': random.randint(100, 50000),
            'is_toll': random.choice([0, 1]),
            'surface_quality': round(random.uniform(1.0, 10.0), 1)
        }
        
        return line, attributes
    
    def test_large_scale_performance(self):
        """执行大规模性能测试"""
        print("大规模线要素性能测试")
        print("=" * 60)
        self.print_system_info()
        
        print(f"测试配置:")
        print(f"- 数据量范围: {self.test_sizes[0]:,} - {self.test_sizes[-1]:,} 个线要素")
        print(f"- 步长: {self.test_sizes[1] - self.test_sizes[0]:,} 个要素")
        print(f"- 每条线包含点数: {self.points_per_line}")
        print(f"- 测试格式: {', '.join(self.test_formats)}")
        print("-" * 60)
        
        all_results = {}
        
        for size in self.test_sizes:
            print(f"\n{'='*60}")
            print(f"测试数据量: {size:,} 个线要素")
            print("="*60)
            
            # 检查内存和磁盘空间
            if not self.check_resources(size):
                print(f"⚠️  资源不足，跳过 {size:,} 要素测试")
                continue
            
            try:
                # 生成测试数据
                print(f"生成 {size:,} 个复杂线要素...")
                start_time = time.perf_counter()
                test_data = self.generate_test_data_batch(size)
                data_gen_time = time.perf_counter() - start_time
                print(f"数据生成耗时: {data_gen_time:.2f}秒")
                
                # 测试各种格式
                size_results = {}
                for format_name in self.test_formats:
                    print(f"\n测试 {format_name} 格式...")
                    
                    try:
                        result = self.test_format_performance(format_name, test_data, size)
                        size_results[format_name] = result
                        
                        # 显示结果
                        self.print_test_result(format_name, result, size)
                        
                    except Exception as e:
                        print(f"  ✗ {format_name} 测试失败: {e}")
                        size_results[format_name] = None
                
                all_results[size] = {
                    'data_generation_time': data_gen_time,
                    'formats': size_results,
                    'system_stats': self.get_current_system_stats()
                }
                
                # 清理内存
                del test_data
                gc.collect()
                
            except Exception as e:
                print(f"  ✗ {size:,} 要素测试失败: {e}")
                all_results[size] = {'error': str(e)}
        
        # 生成报告
        self.generate_comprehensive_report(all_results)
        return all_results
    
    def generate_test_data_batch(self, size):
        """批量生成测试数据"""
        test_data = []
        batch_size = 1000  # 每批处理1000个
        
        for batch_start in range(0, size, batch_size):
            batch_end = min(batch_start + batch_size, size)
            batch_data = []
            
            for i in range(batch_start, batch_end):
                line, attributes = self.generate_complex_linestring(i, self.points_per_line)
                batch_data.append((line, attributes))
            
            test_data.extend(batch_data)
            
            # 显示进度
            if (batch_end) % 10000 == 0 or batch_end == size:
                progress = (batch_end / size) * 100
                print(f"  生成进度: {batch_end:,}/{size:,} ({progress:.1f}%)")
        
        return test_data
    
    def check_resources(self, size):
        """检查系统资源是否足够"""
        # 估算内存需求 (每个线要素约1KB)
        estimated_memory = size * 1024 * 2  # 双倍缓冲
        available_memory = psutil.virtual_memory().available
        
        # 估算磁盘需求 (保守估计每个要素2KB)
        estimated_disk = size * 2048 * len(self.test_formats) * 2  # 双格式双缓冲
        available_disk = psutil.disk_usage(self.output_dir).free
        
        memory_ok = available_memory > estimated_memory
        disk_ok = available_disk > estimated_disk
        
        if not memory_ok:
            print(f"  ⚠️  内存不足: 需要 {estimated_memory/(1024**3):.1f}GB, 可用 {available_memory/(1024**3):.1f}GB")
        
        if not disk_ok:
            print(f"  ⚠️  磁盘空间不足: 需要 {estimated_disk/(1024**3):.1f}GB, 可用 {available_disk/(1024**3):.1f}GB")
        
        return memory_ok and disk_ok
    
    def test_format_performance(self, format_name, test_data, size):
        """测试特定格式的性能"""
        # 创建坐标系统
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        
        # 文件路径
        if format_name == 'Shapefile':
            file_path = os.path.join(self.output_dir, f"lines_{size}.shp")
        else:  # GeoPackage
            file_path = os.path.join(self.output_dir, f"lines_{size}.gpkg")
        
        results = {}
        
        # 测试写入性能
        print(f"  测试 {format_name} 写入性能...")
        start_stats = self.get_current_system_stats()
        
        start_time = time.perf_counter()
        write_success = self.write_format_optimized(format_name, file_path, test_data, srs)
        write_time = time.perf_counter() - start_time
        
        end_stats = self.get_current_system_stats()
        
        if not write_success:
            return {'error': 'Write failed'}
        
        # 获取文件大小
        file_size = self.get_file_size(format_name, file_path)
        
        results['write_time'] = write_time
        results['file_size'] = file_size
        results['write_throughput'] = len(test_data) / write_time  # 要素/秒
        results['system_stats_diff'] = {
            'memory_used': end_stats['memory_used'] - start_stats['memory_used'],
            'cpu_percent': (end_stats['cpu_percent'] + start_stats['cpu_percent']) / 2
        }
        
        # 测试读取性能（采样测试以节省时间）
        if len(test_data) <= 100000:  # 只对小于等于10万的数据测试完整读取
            print(f"  测试 {format_name} 完整读取性能...")
            start_time = time.perf_counter()
            feature_count = self.read_file_complete(file_path)
            read_time = time.perf_counter() - start_time
            
            results['read_time'] = read_time
            results['read_throughput'] = feature_count / read_time if read_time > 0 else 0
            results['feature_count'] = feature_count
        else:
            # 大数据量只测试采样读取
            print(f"  测试 {format_name} 采样读取性能...")
            start_time = time.perf_counter()
            sample_count = self.read_file_sample(file_path, sample_size=1000)
            sample_read_time = time.perf_counter() - start_time
            
            results['sample_read_time'] = sample_read_time
            results['sample_throughput'] = sample_count / sample_read_time if sample_read_time > 0 else 0
            results['estimated_full_read_time'] = sample_read_time * (len(test_data) / 1000)
        
        # 测试空间查询性能
        print(f"  测试 {format_name} 空间查询性能...")
        start_time = time.perf_counter()
        query_result_count = self.test_spatial_query_optimized(file_path)
        query_time = time.perf_counter() - start_time
        
        results['query_time'] = query_time
        results['query_result_count'] = query_result_count
        
        return results
    
    def write_format_optimized(self, format_name, file_path, test_data, srs):
        """优化的格式写入"""
        try:
            # 删除现有文件
            if format_name == 'Shapefile':
                base_name = os.path.splitext(file_path)[0]
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    related_file = base_name + ext
                    if os.path.exists(related_file):
                        os.remove(related_file)
                
                driver = ogr.GetDriverByName("ESRI Shapefile")
            else:  # GeoPackage
                if os.path.exists(file_path):
                    os.remove(file_path)
                driver = ogr.GetDriverByName("GPKG")
            
            # 创建数据源和图层
            datasource = driver.CreateDataSource(file_path)
            layer = datasource.CreateLayer("roads", srs, ogr.wkbLineString)
            
            # 创建字段
            self.create_line_fields(layer)
            
            # 批量写入数据 (使用事务优化)
            batch_size = 1000
            layer.StartTransaction()
            
            try:
                for i, (geom, attributes) in enumerate(test_data):
                    feature = ogr.Feature(layer.GetLayerDefn())
                    
                    # 设置属性
                    for field_name, value in attributes.items():
                        if layer.GetLayerDefn().GetFieldIndex(field_name) >= 0:
                            feature.SetField(field_name, value)
                    
                    feature.SetGeometry(geom)
                    layer.CreateFeature(feature)
                    feature = None
                    
                    # 定期提交事务
                    if (i + 1) % batch_size == 0:
                        layer.CommitTransaction()
                        layer.StartTransaction()
                
                # 提交最后的事务
                layer.CommitTransaction()
                
            except Exception as e:
                layer.RollbackTransaction()
                raise e
            
            datasource = None
            return True
            
        except Exception as e:
            print(f"    写入失败: {e}")
            return False
    
    def create_line_fields(self, layer):
        """为线图层创建字段"""
        fields = [
            ("road_id", ogr.OFTInteger),
            ("name", ogr.OFTString, 50),
            ("road_type", ogr.OFTString, 20),
            ("material", ogr.OFTString, 15),
            ("width", ogr.OFTReal),
            ("max_speed", ogr.OFTInteger),
            ("length_km", ogr.OFTReal),
            ("lanes", ogr.OFTInteger),
            ("construction_year", ogr.OFTInteger),
            ("last_maintenance", ogr.OFTInteger),
            ("traffic_flow", ogr.OFTInteger),
            ("is_toll", ogr.OFTInteger),
            ("surface_quality", ogr.OFTReal)
        ]
        
        for field_info in fields:
            field_name, field_type = field_info[0], field_info[1]
            field_defn = ogr.FieldDefn(field_name, field_type)
            
            if len(field_info) > 2:  # 有长度限制
                field_defn.SetWidth(field_info[2])
            
            if field_type == ogr.OFTReal:
                field_defn.SetPrecision(2)
            
            layer.CreateField(field_defn)
    
    def read_file_complete(self, file_path):
        """完整读取文件"""
        if not os.path.exists(file_path):
            return 0
        
        datasource = ogr.Open(file_path, 0)
        if not datasource:
            return 0
        
        layer = datasource.GetLayer(0)
        if not layer:
            return 0
        
        feature_count = 0
        layer.ResetReading()
        
        for feature in layer:
            # 模拟实际使用中的数据访问
            _ = feature.GetField("name")
            _ = feature.GetField("road_type")
            geom = feature.GetGeometryRef()
            if geom:
                _ = geom.Length()
            feature_count += 1
        
        datasource = None
        return feature_count
    
    def read_file_sample(self, file_path, sample_size=1000):
        """采样读取文件"""
        if not os.path.exists(file_path):
            return 0
        
        datasource = ogr.Open(file_path, 0)
        if not datasource:
            return 0
        
        layer = datasource.GetLayer(0)
        if not layer:
            return 0
        
        total_features = layer.GetFeatureCount()
        if total_features <= sample_size:
            return self.read_file_complete(file_path)
        
        # 随机采样
        sample_indices = set(random.sample(range(total_features), sample_size))
        
        feature_count = 0
        layer.ResetReading()
        
        for i, feature in enumerate(layer):
            if i in sample_indices:
                # 模拟数据访问
                _ = feature.GetField("name")
                geom = feature.GetGeometryRef()
                if geom:
                    _ = geom.Length()
                feature_count += 1
                
                if feature_count >= sample_size:
                    break
        
        datasource = None
        return feature_count
    
    def test_spatial_query_optimized(self, file_path):
        """优化的空间查询测试"""
        if not os.path.exists(file_path):
            return 0
        
        datasource = ogr.Open(file_path, 0)
        if not datasource:
            return 0
        
        layer = datasource.GetLayer(0)
        if not layer:
            return 0
        
        # 创建查询区域 (北京市中心区域)
        query_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(116.3, 39.8)
        ring.AddPoint(116.5, 39.8)
        ring.AddPoint(116.5, 40.0)
        ring.AddPoint(116.3, 40.0)
        ring.AddPoint(116.3, 39.8)
        query_geom.AddGeometry(ring)
        
        # 执行空间过滤
        layer.SetSpatialFilter(query_geom)
        
        count = 0
        for feature in layer:
            count += 1
        
        layer.SetSpatialFilter(None)
        datasource = None
        
        return count
    
    def get_file_size(self, format_name, file_path):
        """获取文件大小"""
        if format_name == 'Shapefile':
            base_name = os.path.splitext(file_path)[0]
            total_size = 0
            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                related_file = base_name + ext
                if os.path.exists(related_file):
                    total_size += os.path.getsize(related_file)
            return total_size
        else:  # GeoPackage
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    def get_current_system_stats(self):
        """获取当前系统统计信息"""
        return {
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'disk_used': psutil.disk_usage(self.output_dir).used
        }
    
    def print_test_result(self, format_name, result, size):
        """打印测试结果"""
        if result is None or 'error' in result:
            print(f"  ✗ {format_name} 测试失败")
            return
        
        print(f"  ✓ {format_name} 测试结果:")
        print(f"    写入时间: {result['write_time']:.2f}秒")
        print(f"    写入吞吐量: {result['write_throughput']:.0f} 要素/秒")
        print(f"    文件大小: {self.format_size(result['file_size'])}")
        
        if 'read_time' in result:
            print(f"    读取时间: {result['read_time']:.2f}秒")
            print(f"    读取吞吐量: {result['read_throughput']:.0f} 要素/秒")
        elif 'sample_read_time' in result:
            print(f"    采样读取时间: {result['sample_read_time']:.3f}秒 (1000要素)")
            print(f"    估算完整读取时间: {result['estimated_full_read_time']:.2f}秒")
        
        if 'query_time' in result:
            print(f"    空间查询时间: {result['query_time']:.3f}秒")
            print(f"    查询结果数量: {result['query_result_count']}")
        
        print(f"    内存使用: {self.format_size(result['system_stats_diff']['memory_used'])}")
    
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
    
    def generate_comprehensive_report(self, all_results):
        """生成综合报告"""
        report_path = os.path.join(self.output_dir, "large_scale_performance_report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 大规模线要素性能测试报告\n\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 系统信息
            f.write("## 测试环境\n\n")
            for key, value in self.system_info.items():
                f.write(f"- {key}: {value}\n")
            f.write("\n")
            
            # 测试配置
            f.write("## 测试配置\n\n")
            f.write(f"- 数据量范围: {self.test_sizes[0]:,} - {self.test_sizes[-1]:,} 个线要素\n")
            f.write(f"- 每条线包含点数: {self.points_per_line}\n")
            f.write(f"- 测试格式: {', '.join(self.test_formats)}\n\n")
            
            # 性能数据表格
            f.write("## 性能测试结果\n\n")
            f.write("| 数据量 | 格式 | 写入时间(s) | 文件大小(MB) | 写入吞吐量(要素/s) | 读取性能 |\n")
            f.write("|--------|------|-------------|--------------|-------------------|----------|\n")
            
            for size, size_data in all_results.items():
                if 'error' in size_data:
                    continue
                
                for format_name in self.test_formats:
                    if format_name in size_data['formats'] and size_data['formats'][format_name]:
                        result = size_data['formats'][format_name]
                        if 'error' not in result:
                            file_size_mb = result['file_size'] / (1024 * 1024)
                            read_info = f"{result['read_time']:.2f}s" if 'read_time' in result else f"~{result.get('estimated_full_read_time', 0):.1f}s"
                            
                            f.write(f"| {size:,} | {format_name} | {result['write_time']:.2f} | ")
                            f.write(f"{file_size_mb:.1f} | {result['write_throughput']:.0f} | {read_info} |\n")
            
            f.write("\n## 测试结论\n\n")
            f.write("### 发现的性能特点\n\n")
            f.write("### 跨平台兼容性分析\n\n")
            f.write("### 改进建议\n\n")
        
        print(f"\n📊 详细报告已生成: {report_path}")

def run_large_scale_test():
    """运行大规模测试"""
    tester = LargeScalePerformanceTest()
    
    try:
        results = tester.test_large_scale_performance()
        print(f"\n✅ 大规模性能测试完成!")
        return results
        
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被用户中断")
        return None
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 检查依赖
    try:
        import psutil
    except ImportError:
        print("请安装 psutil: pip install psutil")
        sys.exit(1)
    
    print("⚠️  注意: 这是大规模测试，可能需要数小时完成并占用大量磁盘空间")
    print("建议在测试机或有足够资源的环境中运行")
    
    response = input("是否继续? (y/N): ")
    if response.lower() != 'y':
        print("测试取消")
        sys.exit(0)
    
    run_large_scale_test()