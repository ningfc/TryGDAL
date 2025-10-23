#!/usr/bin/env python3
"""
全面的Shapefile vs GeoPackage性能对比测试
包含点和多边形数据的完整测试
"""

import os
import sys
import time
import random
import math
from osgeo import gdal, ogr, osr

# 明确启用异常处理
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def comprehensive_performance_test():
    """全面性能对比测试"""
    print("Shapefile vs GeoPackage 全面性能对比测试")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/comprehensive_perf"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 测试配置
    test_configs = [
        {
            'name': 'Point',
            'chinese': '点',
            'sizes': [100, 500, 1000, 2000],
            'generator': generate_points
        },
        {
            'name': 'Polygon',
            'chinese': '多边形',
            'sizes': [50, 100, 200, 500],
            'generator': generate_polygons
        }
    ]
    
    all_results = {}
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"测试几何类型: {config['name']} ({config['chinese']})")
        print("="*60)
        
        geom_results = {}
        
        for size in config['sizes']:
            print(f"\n数据量: {size:,} 个要素")
            print("-" * 40)
            
            # 生成测试数据
            test_data = config['generator'](size)
            
            # 执行性能测试
            result = run_performance_test(output_dir, config['name'], test_data, size)
            geom_results[size] = result
            
            # 显示结果
            display_test_result(size, result)
        
        all_results[config['name']] = geom_results
    
    # 生成详细报告
    generate_detailed_report(all_results, output_dir)
    
    return all_results

def generate_points(count):
    """生成点数据"""
    print(f"  生成 {count:,} 个随机点...")
    
    # 北京市范围
    min_lon, max_lon = 116.0, 117.0
    min_lat, max_lat = 39.4, 40.6
    
    test_data = []
    categories = ['商业', '住宅', '工业', '交通', '教育']
    
    for i in range(count):
        lon = random.uniform(min_lon, max_lon)
        lat = random.uniform(min_lat, max_lat)
        
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        
        attributes = {
            'id': i + 1,
            'name': f'Point_{i+1}',
            'category': random.choice(categories),
            'value': round(random.uniform(0, 1000), 2),
            'status': random.choice(['Active', 'Inactive']),
            'level': random.randint(1, 10)
        }
        
        test_data.append((point, attributes))
    
    return test_data

def generate_polygons(count):
    """生成多边形数据"""
    print(f"  生成 {count:,} 个随机多边形...")
    
    # 北京市范围
    min_lon, max_lon = 116.0, 117.0
    min_lat, max_lat = 39.4, 40.6
    
    test_data = []
    land_uses = ['城市用地', '农业用地', '工业用地', '绿地', '水域']
    
    for i in range(count):
        # 生成随机中心点
        center_lon = random.uniform(min_lon + 0.01, max_lon - 0.01)
        center_lat = random.uniform(min_lat + 0.01, max_lat - 0.01)
        
        # 生成不规则多边形
        radius = random.uniform(0.001, 0.003)
        sides = random.randint(4, 8)
        
        coords = []
        for j in range(sides):
            angle = (2 * math.pi * j) / sides
            # 添加一些随机性使形状不规则
            r = radius * random.uniform(0.5, 1.5)
            x = center_lon + r * math.cos(angle)
            y = center_lat + r * math.sin(angle)
            coords.append((x, y))
        
        # 闭合多边形
        coords.append(coords[0])
        
        # 创建几何体
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for lon, lat in coords:
            ring.AddPoint(lon, lat)
        
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(ring)
        
        # 生成属性
        area = polygon.GetArea()
        perimeter = polygon.Boundary().Length()
        
        attributes = {
            'id': i + 1,
            'name': f'Polygon_{i+1}',
            'land_use': random.choice(land_uses),
            'area': round(area, 6),
            'perimeter': round(perimeter, 6),
            'population': random.randint(0, 5000),
            'year_built': random.randint(1980, 2023)
        }
        
        test_data.append((polygon, attributes))
    
    return test_data

def run_performance_test(output_dir, geom_name, test_data, size):
    """执行性能测试"""
    results = {}
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    geom_type = ogr.wkbPoint if geom_name == 'Point' else ogr.wkbPolygon
    
    # 测试 Shapefile
    print("  测试 Shapefile...")
    shp_path = os.path.join(output_dir, f"{geom_name.lower()}_{size}.shp")
    
    start_time = time.perf_counter()
    write_shapefile_optimized(shp_path, test_data, srs, geom_type)
    shp_write_time = time.perf_counter() - start_time
    
    start_time = time.perf_counter()
    shp_count = read_file_optimized(shp_path)
    shp_read_time = time.perf_counter() - start_time
    
    shp_size = get_total_file_size(shp_path)
    
    # 测试 GeoPackage
    print("  测试 GeoPackage...")
    gpkg_path = os.path.join(output_dir, f"{geom_name.lower()}_{size}.gpkg")
    
    start_time = time.perf_counter()
    write_geopackage_optimized(gpkg_path, test_data, srs, geom_type)
    gpkg_write_time = time.perf_counter() - start_time
    
    start_time = time.perf_counter()
    gpkg_count = read_file_optimized(gpkg_path)
    gpkg_read_time = time.perf_counter() - start_time
    
    gpkg_size = os.path.getsize(gpkg_path) if os.path.exists(gpkg_path) else 0
    
    # 测试查询性能
    print("  测试查询性能...")
    shp_query_time = test_spatial_query(shp_path)
    gpkg_query_time = test_spatial_query(gpkg_path)
    
    results = {
        'shapefile': {
            'write_time': shp_write_time,
            'read_time': shp_read_time,
            'query_time': shp_query_time,
            'file_size': shp_size,
            'feature_count': shp_count
        },
        'geopackage': {
            'write_time': gpkg_write_time,
            'read_time': gpkg_read_time,
            'query_time': gpkg_query_time,
            'file_size': gpkg_size,
            'feature_count': gpkg_count
        }
    }
    
    return results

def write_shapefile_optimized(file_path, test_data, srs, geom_type):
    """优化的Shapefile写入"""
    # 删除现有文件
    base_name = os.path.splitext(file_path)[0]
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
        related_file = base_name + ext
        if os.path.exists(related_file):
            os.remove(related_file)
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.CreateDataSource(file_path)
    layer = datasource.CreateLayer("layer", srs, geom_type)
    
    # 根据几何类型创建字段
    if geom_type == ogr.wkbPoint:
        create_point_fields(layer)
    else:
        create_polygon_fields(layer)
    
    # 批量写入数据
    layer.StartTransaction()
    try:
        for geom, attributes in test_data:
            feature = ogr.Feature(layer.GetLayerDefn())
            
            # 设置属性
            for field_name, value in attributes.items():
                if layer.GetLayerDefn().GetFieldIndex(field_name) >= 0:
                    feature.SetField(field_name, value)
            
            feature.SetGeometry(geom)
            layer.CreateFeature(feature)
            feature = None
        
        layer.CommitTransaction()
    except:
        layer.RollbackTransaction()
        raise
    
    datasource = None

def write_geopackage_optimized(file_path, test_data, srs, geom_type):
    """优化的GeoPackage写入"""
    if os.path.exists(file_path):
        os.remove(file_path)
    
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.CreateDataSource(file_path)
    layer = datasource.CreateLayer("layer", srs, geom_type)
    
    # 根据几何类型创建字段
    if geom_type == ogr.wkbPoint:
        create_point_fields(layer)
    else:
        create_polygon_fields(layer)
    
    # 批量写入数据
    layer.StartTransaction()
    try:
        for geom, attributes in test_data:
            feature = ogr.Feature(layer.GetLayerDefn())
            
            # 设置属性
            for field_name, value in attributes.items():
                if layer.GetLayerDefn().GetFieldIndex(field_name) >= 0:
                    feature.SetField(field_name, value)
            
            feature.SetGeometry(geom)
            layer.CreateFeature(feature)
            feature = None
        
        layer.CommitTransaction()
    except:
        layer.RollbackTransaction()
        raise
    
    datasource = None

def create_point_fields(layer):
    """为点图层创建字段"""
    fields = [
        ("id", ogr.OFTInteger),
        ("name", ogr.OFTString),
        ("category", ogr.OFTString),
        ("value", ogr.OFTReal),
        ("status", ogr.OFTString),
        ("level", ogr.OFTInteger)
    ]
    
    for field_name, field_type in fields:
        field_defn = ogr.FieldDefn(field_name, field_type)
        if field_type == ogr.OFTString:
            field_defn.SetWidth(50)
        elif field_type == ogr.OFTReal:
            field_defn.SetPrecision(2)
        layer.CreateField(field_defn)

def create_polygon_fields(layer):
    """为多边形图层创建字段"""
    fields = [
        ("id", ogr.OFTInteger),
        ("name", ogr.OFTString),
        ("land_use", ogr.OFTString),
        ("area", ogr.OFTReal),
        ("perimeter", ogr.OFTReal),
        ("population", ogr.OFTInteger),
        ("year_built", ogr.OFTInteger)
    ]
    
    for field_name, field_type in fields:
        field_defn = ogr.FieldDefn(field_name, field_type)
        if field_type == ogr.OFTString:
            field_defn.SetWidth(50)
        elif field_type == ogr.OFTReal:
            field_defn.SetPrecision(6)
        layer.CreateField(field_defn)

def read_file_optimized(file_path):
    """优化的文件读取"""
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
    
    # 快速计数
    for feature in layer:
        feature_count += 1
        # 模拟最小数据访问
        if feature_count % 100 == 0:
            _ = feature.GetField(0)  # 访问第一个字段
    
    datasource = None
    return feature_count

def test_spatial_query(file_path):
    """测试空间查询性能"""
    if not os.path.exists(file_path):
        return 0
    
    datasource = ogr.Open(file_path, 0)
    if not datasource:
        return 0
    
    layer = datasource.GetLayer(0)
    if not layer:
        return 0
    
    # 创建查询区域（北京市中心区域）
    query_geom = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(116.3, 39.8)
    ring.AddPoint(116.5, 39.8)
    ring.AddPoint(116.5, 40.0)
    ring.AddPoint(116.3, 40.0)
    ring.AddPoint(116.3, 39.8)
    query_geom.AddGeometry(ring)
    
    start_time = time.perf_counter()
    
    # 执行空间过滤
    layer.SetSpatialFilter(query_geom)
    
    count = 0
    for feature in layer:
        count += 1
    
    query_time = time.perf_counter() - start_time
    
    # 清除过滤器
    layer.SetSpatialFilter(None)
    datasource = None
    
    return query_time

def get_total_file_size(shp_path):
    """获取Shapefile总文件大小"""
    base_name = os.path.splitext(shp_path)[0]
    total_size = 0
    
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
        file_path = base_name + ext
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    return total_size

def display_test_result(size, result):
    """显示测试结果"""
    shp = result['shapefile']
    gpkg = result['geopackage']
    
    print(f"    写入: SHP {shp['write_time']:.3f}s | GPKG {gpkg['write_time']:.3f}s")
    print(f"    读取: SHP {shp['read_time']:.3f}s | GPKG {gpkg['read_time']:.3f}s")
    print(f"    查询: SHP {shp['query_time']:.3f}s | GPKG {gpkg['query_time']:.3f}s")
    print(f"    大小: SHP {format_size(shp['file_size'])} | GPKG {format_size(gpkg['file_size'])}")
    
    # 性能比率
    if gpkg['write_time'] > 0:
        print(f"    写入倍率: {shp['write_time']/gpkg['write_time']:.2f}x")
    if gpkg['file_size'] > 0:
        print(f"    大小倍率: {shp['file_size']/gpkg['file_size']:.2f}x")

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def generate_detailed_report(all_results, output_dir):
    """生成详细报告"""
    report_path = os.path.join(output_dir, "performance_analysis_report.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Shapefile vs GeoPackage 性能分析报告\n\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for geom_type, results in all_results.items():
            f.write(f"## {geom_type} 性能对比\n\n")
            f.write("| 数据量 | 写入时间(s) | | 读取时间(s) | | 查询时间(s) | | 文件大小 | |\n")
            f.write("|-------|------------|--|------------|--|------------|--|----------|--|\n")
            f.write("| | SHP | GPKG | SHP | GPKG | SHP | GPKG | SHP | GPKG |\n")
            
            for size, data in results.items():
                shp = data['shapefile']
                gpkg = data['geopackage']
                
                f.write(f"| {size} |")
                f.write(f" {shp['write_time']:.3f} | {gpkg['write_time']:.3f} |")
                f.write(f" {shp['read_time']:.3f} | {gpkg['read_time']:.3f} |")
                f.write(f" {shp['query_time']:.3f} | {gpkg['query_time']:.3f} |")
                f.write(f" {format_size(shp['file_size'])} | {format_size(gpkg['file_size'])} |\n")
            
            f.write("\n")
    
    print(f"\n详细报告已生成: {report_path}")

def offer_data_cleanup():
    """询问用户是否清理测试数据"""
    print(f"\n" + "="*50)
    print("数据清理选项")
    print("="*50)
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/comprehensive_perf"
    
    if not os.path.exists(output_dir):
        print("📁 测试目录不存在，无需清理")
        return
    
    # 统计测试文件
    test_files = []
    total_size = 0
    
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            test_files.append(file_path)
            total_size += os.path.getsize(file_path)
    
    if not test_files:
        print("📁 没有发现测试文件")
        return
    
    print(f"📊 测试数据统计:")
    print(f"  文件数量: {len(test_files)} 个")
    print(f"  占用空间: {format_size(total_size)}")
    
    print(f"\n📁 文件列表:")
    for file_path in sorted(test_files):
        file_name = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        print(f"  📄 {file_name:30} {format_size(size):>10}")
    
    try:
        choice = input(f"\n选择清理选项 [1=保留全部, 2=清理数据, 3=清理全部]: ").strip()
        
        if choice == '2':
            # 只清理测试数据，保留报告
            data_files = [f for f in test_files if not f.endswith('.md')]
            cleanup_files(data_files, "测试数据")
        elif choice == '3':
            # 清理所有文件
            cleanup_files(test_files, "所有文件")
        else:
            print("✅ 保留所有文件")
            
    except KeyboardInterrupt:
        print("\n⚠️  清理操作被取消")

def cleanup_files(file_list, description):
    """清理指定文件"""
    deleted_count = 0
    deleted_size = 0
    
    for file_path in file_list:
        try:
            size = os.path.getsize(file_path)
            os.remove(file_path)
            deleted_count += 1
            deleted_size += size
            print(f"  ✅ 已删除: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  ❌ 删除失败: {os.path.basename(file_path)} - {e}")
    
    print(f"\n📊 清理结果 ({description}):")
    print(f"  删除文件: {deleted_count} 个")
    print(f"  释放空间: {format_size(deleted_size)}")

if __name__ == "__main__":
    try:
        results = comprehensive_performance_test()
        print(f"\n✓ 全面性能测试完成！")
        
        # 询问是否清理数据
        offer_data_cleanup()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()