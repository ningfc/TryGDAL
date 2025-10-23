#!/usr/bin/env python3
"""
大规模线要素性能测试 - 演示版本
适合当前macOS环境的小规模测试演示
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

class PerformanceTestDemo:
    """性能测试演示类"""
    
    def __init__(self):
        self.output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/demo_test"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 演示版本的测试大小（适合macOS开发环境）
        self.test_sizes = [10000, 20000, 30000]  # 1万、2万、3万要素
        self.points_per_line = 100
        self.test_formats = ['Shapefile', 'GeoPackage']
        
        print("大规模线要素性能测试 - 演示版本")
        print("=" * 60)
        print(f"当前平台: {platform.system()} {platform.machine()}")
        print(f"内存: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print(f"磁盘空间: {psutil.disk_usage(os.path.expanduser('~')).free / (1024**3):.1f} GB")
        print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
        print("-" * 60)
    
    def generate_complex_linestring(self, line_id, points_count=100):
        """生成复杂的线要素"""
        # 基于北京市范围生成
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
        
        # 生成属性
        road_types = ['高速公路', '主干道', '次干道', '支路']
        attributes = {
            'road_id': line_id,
            'name': f'Road_{line_id}',
            'road_type': random.choice(road_types),
            'width': round(random.uniform(3.0, 50.0), 1),
            'max_speed': random.choice([30, 40, 50, 60, 80, 100, 120]),
            'length_km': round(line.Length() * 111.0, 3),
            'lanes': random.randint(1, 8)
        }
        
        return line, attributes
    
    def test_performance(self):
        """执行性能测试"""
        print("开始演示测试...")
        
        all_results = {}
        
        for size in self.test_sizes:
            print(f"\n{'='*50}")
            print(f"测试数据量: {size:,} 个线要素")
            print("="*50)
            
            # 检查资源
            estimated_memory = size * 1024 * 2
            available_memory = psutil.virtual_memory().available
            
            if available_memory < estimated_memory:
                print(f"⚠️  内存可能不足，但继续测试...")
            
            # 生成测试数据
            print(f"生成 {size:,} 个线要素...")
            start_time = time.perf_counter()
            
            test_data = []
            for i in range(size):
                line, attributes = self.generate_complex_linestring(i, self.points_per_line)
                test_data.append((line, attributes))
                
                if (i + 1) % 5000 == 0:
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
                    size_results[format_name] = None
            
            all_results[size] = {
                'data_generation_time': data_gen_time,
                'formats': size_results
            }
            
            # 清理内存
            del test_data
            gc.collect()
            
            # 显示内存使用
            memory_usage = psutil.virtual_memory()
            print(f"\n当前内存使用: {memory_usage.percent:.1f}% ({memory_usage.used/(1024**3):.1f}GB)")
        
        # 生成对比分析
        self.analyze_results(all_results)
        
        return all_results
    
    def test_format_performance(self, format_name, test_data, size):
        """测试格式性能"""
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        
        if format_name == 'Shapefile':
            file_path = os.path.join(self.output_dir, f"lines_{size}.shp")
        else:
            file_path = os.path.join(self.output_dir, f"lines_{size}.gpkg")
        
        results = {}
        
        # 写入测试
        start_memory = psutil.virtual_memory().used
        start_time = time.perf_counter()
        
        success = self.write_format(format_name, file_path, test_data, srs)
        
        write_time = time.perf_counter() - start_time
        end_memory = psutil.virtual_memory().used
        
        if not success:
            return {'error': 'Write failed'}
        
        file_size = self.get_file_size(format_name, file_path)
        
        results['write_time'] = write_time
        results['file_size'] = file_size
        results['write_throughput'] = len(test_data) / write_time
        results['memory_used'] = end_memory - start_memory
        
        # 读取测试
        start_time = time.perf_counter()
        feature_count = self.read_file(file_path)
        read_time = time.perf_counter() - start_time
        
        results['read_time'] = read_time
        results['read_throughput'] = feature_count / read_time if read_time > 0 else 0
        results['feature_count'] = feature_count
        
        # 空间查询测试
        start_time = time.perf_counter()
        query_count = self.test_spatial_query(file_path)
        query_time = time.perf_counter() - start_time
        
        results['query_time'] = query_time
        results['query_count'] = query_count
        
        return results
    
    def write_format(self, format_name, file_path, test_data, srs):
        """写入格式"""
        try:
            # 清理旧文件
            if format_name == 'Shapefile':
                base_name = os.path.splitext(file_path)[0]
                for ext in ['.shp', '.shx', '.dbf', '.prj']:
                    related_file = base_name + ext
                    if os.path.exists(related_file):
                        os.remove(related_file)
                driver = ogr.GetDriverByName("ESRI Shapefile")
            else:
                if os.path.exists(file_path):
                    os.remove(file_path)
                driver = ogr.GetDriverByName("GPKG")
            
            datasource = driver.CreateDataSource(file_path)
            layer = datasource.CreateLayer("roads", srs, ogr.wkbLineString)
            
            # 创建字段
            fields = [
                ("road_id", ogr.OFTInteger),
                ("name", ogr.OFTString),
                ("road_type", ogr.OFTString),
                ("width", ogr.OFTReal),
                ("max_speed", ogr.OFTInteger),
                ("length_km", ogr.OFTReal),
                ("lanes", ogr.OFTInteger)
            ]
            
            for field_name, field_type in fields:
                field_defn = ogr.FieldDefn(field_name, field_type)
                if field_type == ogr.OFTString:
                    field_defn.SetWidth(50)
                layer.CreateField(field_defn)
            
            # 批量写入
            layer.StartTransaction()
            
            for i, (geom, attributes) in enumerate(test_data):
                feature = ogr.Feature(layer.GetLayerDefn())
                
                for field_name, value in attributes.items():
                    if layer.GetLayerDefn().GetFieldIndex(field_name) >= 0:
                        feature.SetField(field_name, value)
                
                feature.SetGeometry(geom)
                layer.CreateFeature(feature)
                feature = None
                
                # 每1000条提交一次事务
                if (i + 1) % 1000 == 0:
                    layer.CommitTransaction()
                    layer.StartTransaction()
            
            layer.CommitTransaction()
            datasource = None
            return True
            
        except Exception as e:
            print(f"    写入失败: {e}")
            return False
    
    def read_file(self, file_path):
        """读取文件"""
        if not os.path.exists(file_path):
            return 0
        
        datasource = ogr.Open(file_path, 0)
        if not datasource:
            return 0
        
        layer = datasource.GetLayer(0)
        if not layer:
            return 0
        
        count = 0
        for feature in layer:
            # 模拟实际使用
            _ = feature.GetField("name")
            geom = feature.GetGeometryRef()
            if geom:
                _ = geom.Length()
            count += 1
        
        datasource = None
        return count
    
    def test_spatial_query(self, file_path):
        """空间查询测试"""
        if not os.path.exists(file_path):
            return 0
        
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
        count = layer.GetFeatureCount()
        layer.SetSpatialFilter(None)
        
        datasource = None
        return count
    
    def get_file_size(self, format_name, file_path):
        """获取文件大小"""
        if format_name == 'Shapefile':
            base_name = os.path.splitext(file_path)[0]
            total_size = 0
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                related_file = base_name + ext
                if os.path.exists(related_file):
                    total_size += os.path.getsize(related_file)
            return total_size
        else:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    def format_size(self, size_bytes):
        """格式化大小"""
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def print_result(self, format_name, result):
        """打印结果"""
        if 'error' in result:
            print(f"  ❌ {format_name} 失败")
            return
        
        print(f"  ✅ {format_name} 结果:")
        print(f"    写入: {result['write_time']:.2f}s ({result['write_throughput']:.0f} 要素/s)")
        print(f"    文件: {self.format_size(result['file_size'])}")
        print(f"    读取: {result['read_time']:.2f}s ({result['read_throughput']:.0f} 要素/s)")
        print(f"    查询: {result['query_time']:.3f}s (找到 {result['query_count']} 要素)")
        print(f"    内存: {self.format_size(result['memory_used'])}")
    
    def analyze_results(self, all_results):
        """分析结果"""
        print(f"\n" + "="*60)
        print("性能分析总结")
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
                            print(f"  {format_name:12}: {throughput:6.0f} 要素/s, {file_size_mb:5.1f} MB")
        
        print(f"\n预测100万要素性能:")
        # 基于测试结果预测
        if len(all_results) >= 2:
            sizes = sorted(all_results.keys())
            for format_name in self.test_formats:
                results_list = []
                for size in sizes:
                    if (size in all_results and 
                        'formats' in all_results[size] and 
                        format_name in all_results[size]['formats'] and
                        all_results[size]['formats'][format_name] and
                        'error' not in all_results[size]['formats'][format_name]):
                        
                        result = all_results[size]['formats'][format_name]
                        results_list.append((size, result))
                
                if len(results_list) >= 2:
                    # 简单线性预测
                    avg_throughput = sum(r[1]['write_throughput'] for r in results_list) / len(results_list)
                    avg_size_per_feature = sum(r[1]['file_size'] / r[0] for r in results_list) / len(results_list)
                    
                    estimated_time = 1000000 / avg_throughput
                    estimated_size = (1000000 * avg_size_per_feature) / (1024 * 1024 * 1024)
                    
                    print(f"  {format_name:12}: 预计 {estimated_time/60:.1f} 分钟, ~{estimated_size:.1f} GB")
        
        print(f"\n建议:")
        print(f"  ✓ 当前macOS环境适合3万要素以下的测试")
        print(f"  ⚠️ 百万要素测试需要Linux服务器环境")
        print(f"  ⚠️ 建议使用分批处理策略处理大数据")
        print(f"  ⚠️ 考虑使用流式处理减少内存使用")

def main():
    """主函数"""
    print("⚠️  这是大规模测试的演示版本")
    print("适合在macOS开发环境中验证概念和方法")
    print("实际的百万要素测试建议在Linux服务器上进行\n")
    
    try:
        demo = PerformanceTestDemo()
        results = demo.test_performance()
        print(f"\n✅ 演示测试完成!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()