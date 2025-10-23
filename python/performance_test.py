#!/usr/bin/env python3
"""
Shapefile vs GeoPackage 读写效率对比测试
测试不同数据量下两种格式的性能差异
"""

import os
import sys
import time
import random
import math
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def performance_test():
    """性能对比测试主函数"""
    print("Shapefile vs GeoPackage 性能对比测试")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/performance_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 测试不同的数据量
    test_sizes = [100, 500, 1000, 5000, 10000]
    
    # 测试不同的几何类型
    geometry_tests = [
        {
            'name': 'Point',
            'chinese': '点',
            'create_func': create_test_points,
            'complexity': 'low'
        },
        {
            'name': 'Polygon',
            'chinese': '多边形',
            'create_func': create_test_polygons,
            'complexity': 'high'
        }
    ]
    
    results = {}
    
    for geom_test in geometry_tests:
        print(f"\n{'='*60}")
        print(f"测试几何类型: {geom_test['name']} ({geom_test['chinese']})")
        print(f"复杂度: {geom_test['complexity']}")
        print("="*60)
        
        geom_results = {}
        
        for size in test_sizes:
            print(f"\n数据量: {size:,} 个要素")
            print("-" * 40)
            
            # 生成测试数据
            print("生成测试数据...")
            test_data = geom_test['create_func'](size)
            
            # 测试写入性能
            write_results = test_write_performance(output_dir, geom_test, test_data, size)
            
            # 测试读取性能
            read_results = test_read_performance(output_dir, geom_test, size)
            
            # 测试文件大小
            size_results = test_file_size(output_dir, geom_test, size)
            
            # 汇总结果
            geom_results[size] = {
                'write': write_results,
                'read': read_results,
                'size': size_results
            }
            
            # 显示本轮结果
            print_round_results(size, write_results, read_results, size_results)
        
        results[geom_test['name']] = geom_results
    
    # 生成总结报告
    generate_performance_report(results, output_dir)
    
    return results

def create_test_points(count):
    """生成测试点数据"""
    print(f"  生成 {count:,} 个随机点...")
    
    # 北京市范围 (116.0-117.0, 39.4-40.6)
    min_lon, max_lon = 116.0, 117.0
    min_lat, max_lat = 39.4, 40.6
    
    test_data = []
    
    for i in range(count):
        lon = random.uniform(min_lon, max_lon)
        lat = random.uniform(min_lat, max_lat)
        
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        
        # 生成属性数据
        attributes = {
            'id': i + 1,
            'name': f'Point_{i+1}',
            'category': random.choice(['A', 'B', 'C', 'D']),
            'value': random.uniform(0, 1000),
            'population': random.randint(10, 1000),
            'desc': f'Test point {i+1}'
        }
        
        test_data.append((point, attributes))
    
    return test_data

def create_test_polygons(count):
    """生成测试多边形数据"""
    print(f"  生成 {count:,} 个随机多边形...")
    
    # 北京市范围
    min_lon, max_lon = 116.0, 117.0  
    min_lat, max_lat = 39.4, 40.6
    
    test_data = []
    
    for i in range(count):
        # 生成随机中心点
        center_lon = random.uniform(min_lon + 0.01, max_lon - 0.01)
        center_lat = random.uniform(min_lat + 0.01, max_lat - 0.01)
        
        # 生成随机半径（创建正方形）
        radius = random.uniform(0.001, 0.005)
        
        # 创建正方形多边形
        coords = [
            (center_lon - radius, center_lat - radius),
            (center_lon + radius, center_lat - radius),
            (center_lon + radius, center_lat + radius),
            (center_lon - radius, center_lat + radius),
            (center_lon - radius, center_lat - radius)  # 闭合
        ]
        
        # 创建线性环
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for lon, lat in coords:
            ring.AddPoint(lon, lat)
        
        # 创建多边形
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(ring)
        
        # 生成属性数据
        area = polygon.GetArea()
        attributes = {
            'id': i + 1,
            'name': f'Polygon_{i+1}',
            'category': random.choice(['Urban', 'Rural', 'Industrial', 'Residential']),
            'value': area,
            'population': random.randint(100, 10000),
            'desc': f'Polygon {i+1}'
        }
        
        test_data.append((polygon, attributes))
    
    return test_data

def test_write_performance(output_dir, geom_test, test_data, count):
    """测试写入性能"""
    results = {}
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    geom_type = ogr.wkbPoint if geom_test['name'] == 'Point' else ogr.wkbPolygon
    
    # 测试 Shapefile 写入
    print("  测试 Shapefile 写入性能...")
    shp_filename = f"{geom_test['name'].lower()}_{count}.shp"
    shp_path = os.path.join(output_dir, shp_filename)
    
    start_time = time.time()
    write_shapefile(shp_path, test_data, srs, geom_type)
    shp_write_time = time.time() - start_time
    
    results['shapefile_write'] = shp_write_time
    
    # 测试 GeoPackage 写入
    print("  测试 GeoPackage 写入性能...")
    gpkg_filename = f"{geom_test['name'].lower()}_{count}.gpkg"
    gpkg_path = os.path.join(output_dir, gpkg_filename)
    
    start_time = time.time()
    write_geopackage(gpkg_path, test_data, srs, geom_type)
    gpkg_write_time = time.time() - start_time
    
    results['geopackage_write'] = gpkg_write_time
    
    return results

def test_read_performance(output_dir, geom_test, count):
    """测试读取性能"""
    results = {}
    
    # 测试 Shapefile 读取
    print("  测试 Shapefile 读取性能...")
    shp_filename = f"{geom_test['name'].lower()}_{count}.shp"
    shp_path = os.path.join(output_dir, shp_filename)
    
    start_time = time.time()
    shp_feature_count = read_file(shp_path)
    shp_read_time = time.time() - start_time
    
    results['shapefile_read'] = shp_read_time
    results['shapefile_features'] = shp_feature_count
    
    # 测试 GeoPackage 读取
    print("  测试 GeoPackage 读取性能...")
    gpkg_filename = f"{geom_test['name'].lower()}_{count}.gpkg"
    gpkg_path = os.path.join(output_dir, gpkg_filename)
    
    start_time = time.time()
    gpkg_feature_count = read_file(gpkg_path)
    gpkg_read_time = time.time() - start_time
    
    results['geopackage_read'] = gpkg_read_time
    results['geopackage_features'] = gpkg_feature_count
    
    return results

def test_file_size(output_dir, geom_test, count):
    """测试文件大小"""
    results = {}
    
    # Shapefile 文件大小（包含所有相关文件）
    shp_base = os.path.join(output_dir, f"{geom_test['name'].lower()}_{count}")
    shp_total_size = 0
    
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
        file_path = shp_base + ext
        if os.path.exists(file_path):
            shp_total_size += os.path.getsize(file_path)
    
    results['shapefile_size'] = shp_total_size
    
    # GeoPackage 文件大小
    gpkg_path = os.path.join(output_dir, f"{geom_test['name'].lower()}_{count}.gpkg")
    gpkg_size = os.path.getsize(gpkg_path) if os.path.exists(gpkg_path) else 0
    
    results['geopackage_size'] = gpkg_size
    
    return results

def write_shapefile(file_path, test_data, srs, geom_type):
    """写入Shapefile"""
    # 删除现有文件
    base_name = os.path.splitext(file_path)[0]
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
        related_file = base_name + ext
        if os.path.exists(related_file):
            os.remove(related_file)
    
    # 创建驱动和数据源
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.CreateDataSource(file_path)
    
    # 创建图层
    layer = datasource.CreateLayer("layer", srs, geom_type)
    
    # 添加字段
    create_fields(layer)
    
    # 添加要素
    for geom, attributes in test_data:
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        
        # 设置属性
        for field_name, value in attributes.items():
            feature.SetField(field_name, value)
        
        # 设置几何
        feature.SetGeometry(geom)
        
        # 创建要素
        layer.CreateFeature(feature)
        feature = None
    
    # 关闭数据源
    datasource = None

def write_geopackage(file_path, test_data, srs, geom_type):
    """写入GeoPackage"""
    # 删除现有文件
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 创建驱动和数据源
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.CreateDataSource(file_path)
    
    # 创建图层
    layer = datasource.CreateLayer("layer", srs, geom_type)
    
    # 添加字段
    create_fields(layer)
    
    # 添加要素
    for geom, attributes in test_data:
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        
        # 设置属性
        for field_name, value in attributes.items():
            feature.SetField(field_name, value)
        
        # 设置几何
        feature.SetGeometry(geom)
        
        # 创建要素
        layer.CreateFeature(feature)
        feature = None
    
    # 关闭数据源
    datasource = None

def create_fields(layer):
    """创建字段定义"""
    # ID字段
    id_field = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(id_field)
    
    # 名称字段
    name_field = ogr.FieldDefn("name", ogr.OFTString)
    name_field.SetWidth(50)
    layer.CreateField(name_field)
    
    # 类别字段
    category_field = ogr.FieldDefn("category", ogr.OFTString)
    category_field.SetWidth(20)
    layer.CreateField(category_field)
    
    # 数值字段（通用名称，点和多边形都用）
    value_field = ogr.FieldDefn("value", ogr.OFTReal)
    value_field.SetPrecision(6)
    layer.CreateField(value_field)
    
    # 整数字段
    pop_field = ogr.FieldDefn("population", ogr.OFTInteger)
    layer.CreateField(pop_field)
    
    # 长文本字段（缩短名称避免Shapefile限制）
    desc_field = ogr.FieldDefn("desc", ogr.OFTString)
    desc_field.SetWidth(100)  # 减小长度
    layer.CreateField(desc_field)

def read_file(file_path):
    """读取文件并计算要素数量"""
    if not os.path.exists(file_path):
        return 0
    
    datasource = ogr.Open(file_path, 0)
    if not datasource:
        return 0
    
    layer = datasource.GetLayer(0)
    if not layer:
        return 0
    
    feature_count = 0
    
    # 遍历所有要素（模拟实际使用场景）
    layer.ResetReading()
    for feature in layer:
        # 模拟访问属性和几何数据
        _ = feature.GetField("name")
        geom = feature.GetGeometryRef()
        if geom:
            _ = geom.GetArea() if geom.GetGeometryName() in ['POLYGON', 'MULTIPOLYGON'] else geom.GetX()
        feature_count += 1
    
    datasource = None
    return feature_count

def print_round_results(count, write_results, read_results, size_results):
    """打印单轮测试结果"""
    print(f"\n  结果汇总 ({count:,} 要素):")
    
    # 写入性能
    shp_write = write_results['shapefile_write']
    gpkg_write = write_results['geopackage_write']
    write_ratio = shp_write / gpkg_write if gpkg_write > 0 else 0
    
    print(f"    写入时间:")
    print(f"      Shapefile:   {shp_write:.3f}秒")
    print(f"      GeoPackage:  {gpkg_write:.3f}秒")
    print(f"      性能比:      {write_ratio:.2f}x (Shapefile/GeoPackage)")
    
    # 读取性能
    shp_read = read_results['shapefile_read']
    gpkg_read = read_results['geopackage_read']
    read_ratio = shp_read / gpkg_read if gpkg_read > 0 else 0
    
    print(f"    读取时间:")
    print(f"      Shapefile:   {shp_read:.3f}秒")
    print(f"      GeoPackage:  {gpkg_read:.3f}秒")
    print(f"      性能比:      {read_ratio:.2f}x (Shapefile/GeoPackage)")
    
    # 文件大小
    shp_size = size_results['shapefile_size']
    gpkg_size = size_results['geopackage_size']
    size_ratio = shp_size / gpkg_size if gpkg_size > 0 else 0
    
    print(f"    文件大小:")
    print(f"      Shapefile:   {format_file_size(shp_size)}")
    print(f"      GeoPackage:  {format_file_size(gpkg_size)}")
    print(f"      大小比:      {size_ratio:.2f}x (Shapefile/GeoPackage)")

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def generate_performance_report(results, output_dir):
    """生成性能测试报告"""
    report_path = os.path.join(output_dir, "performance_report.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Shapefile vs GeoPackage 性能对比报告\n\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}\n\n")
        
        for geom_type, geom_results in results.items():
            f.write(f"## {geom_type} 几何类型测试结果\n\n")
            
            # 创建表格
            f.write("| 要素数量 | 写入时间(秒) |  | 读取时间(秒) |  | 文件大小 |  |\n")
            f.write("|---------|-------------|--|-------------|--|----------|--|\n")
            f.write("|         | Shapefile | GeoPackage | Shapefile | GeoPackage | Shapefile | GeoPackage |\n")
            
            for count, data in geom_results.items():
                write_data = data['write']
                read_data = data['read']
                size_data = data['size']
                
                f.write(f"| {count:,} |")
                f.write(f" {write_data['shapefile_write']:.3f} |")
                f.write(f" {write_data['geopackage_write']:.3f} |")
                f.write(f" {read_data['shapefile_read']:.3f} |")
                f.write(f" {read_data['geopackage_read']:.3f} |")
                f.write(f" {format_file_size(size_data['shapefile_size'])} |")
                f.write(f" {format_file_size(size_data['geopackage_size'])} |\n")
            
            f.write("\n")
        
        # 添加总结
        f.write("## 总结\n\n")
        f.write("### 性能特点\n\n")
        f.write("1. **写入性能**: \n")
        f.write("2. **读取性能**: \n") 
        f.write("3. **文件大小**: \n")
        f.write("4. **适用场景**: \n\n")
    
    print(f"\n性能测试报告已生成: {report_path}")

def analyze_results(results):
    """分析测试结果并给出建议"""
    print("\n" + "="*60)
    print("性能分析总结")
    print("="*60)
    
    for geom_type, geom_results in results.items():
        print(f"\n{geom_type} 几何类型分析:")
        
        # 计算平均性能比率
        write_ratios = []
        read_ratios = []
        size_ratios = []
        
        for count, data in geom_results.items():
            write_data = data['write']
            read_data = data['read'] 
            size_data = data['size']
            
            if write_data['geopackage_write'] > 0:
                write_ratios.append(write_data['shapefile_write'] / write_data['geopackage_write'])
            
            if read_data['geopackage_read'] > 0:
                read_ratios.append(read_data['shapefile_read'] / read_data['geopackage_read'])
            
            if size_data['geopackage_size'] > 0:
                size_ratios.append(size_data['shapefile_size'] / size_data['geopackage_size'])
        
        if write_ratios:
            avg_write_ratio = sum(write_ratios) / len(write_ratios)
            print(f"  平均写入性能比 (Shapefile/GeoPackage): {avg_write_ratio:.2f}")
            
        if read_ratios:
            avg_read_ratio = sum(read_ratios) / len(read_ratios)
            print(f"  平均读取性能比 (Shapefile/GeoPackage): {avg_read_ratio:.2f}")
            
        if size_ratios:
            avg_size_ratio = sum(size_ratios) / len(size_ratios)
            print(f"  平均文件大小比 (Shapefile/GeoPackage): {avg_size_ratio:.2f}")
    
    print(f"\n推荐使用场景:")
    print(f"• 如果注重写入速度和文件兼容性 → 选择 Shapefile")
    print(f"• 如果注重文件大小和现代功能 → 选择 GeoPackage") 
    print(f"• 大数据量场景 → 根据具体测试结果选择")
    print(f"• Web应用 → 优先考虑 GeoPackage")

if __name__ == "__main__":
    try:
        results = performance_test()
        analyze_results(results)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()