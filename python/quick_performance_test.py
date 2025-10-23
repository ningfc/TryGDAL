#!/usr/bin/env python3
"""
Shapefile vs GeoPackage 读写效率测试（简化版）
快速对比两种格式的性能差异
"""

import os
import sys
import time
import random
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def quick_performance_test():
    """快速性能对比测试"""
    print("Shapefile vs GeoPackage 快速性能测试")
    print("=" * 50)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/quick_perf_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 测试较小的数据量
    test_sizes = [100, 500, 1000]
    
    results = {}
    
    for size in test_sizes:
        print(f"\n{'='*50}")
        print(f"测试数据量: {size:,} 个点要素")
        print("="*50)
        
        # 生成测试数据
        print("生成测试数据...")
        test_data = generate_points(size)
        
        # 测试性能
        result = test_formats(output_dir, test_data, size)
        results[size] = result
        
        # 显示结果
        print_result(size, result)
    
    # 生成总结
    print_summary(results)
    
    return results

def generate_points(count):
    """生成测试点数据"""
    print(f"  生成 {count:,} 个随机点...")
    
    # 北京市范围
    min_lon, max_lon = 116.0, 117.0
    min_lat, max_lat = 39.4, 40.6
    
    test_data = []
    
    for i in range(count):
        lon = random.uniform(min_lon, max_lon)
        lat = random.uniform(min_lat, max_lat)
        
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        
        # 简化的属性数据
        attributes = {
            'id': i + 1,
            'name': f'Point_{i+1}',
            'category': random.choice(['A', 'B', 'C']),
            'value': round(random.uniform(0, 1000), 2)
        }
        
        test_data.append((point, attributes))
    
    return test_data

def test_formats(output_dir, test_data, size):
    """测试两种格式的性能"""
    results = {}
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    # 测试 Shapefile
    print("  测试 Shapefile...")
    shp_path = os.path.join(output_dir, f"points_{size}.shp")
    
    start_time = time.time()
    write_shapefile_simple(shp_path, test_data, srs)
    shp_write_time = time.time() - start_time
    
    start_time = time.time()
    shp_count = read_file_simple(shp_path)
    shp_read_time = time.time() - start_time
    
    shp_size = get_shapefile_size(shp_path)
    
    # 测试 GeoPackage
    print("  测试 GeoPackage...")
    gpkg_path = os.path.join(output_dir, f"points_{size}.gpkg")
    
    start_time = time.time()
    write_geopackage_simple(gpkg_path, test_data, srs)
    gpkg_write_time = time.time() - start_time
    
    start_time = time.time()
    gpkg_count = read_file_simple(gpkg_path)
    gpkg_read_time = time.time() - start_time
    
    gpkg_size = os.path.getsize(gpkg_path) if os.path.exists(gpkg_path) else 0
    
    results = {
        'shapefile': {
            'write_time': shp_write_time,
            'read_time': shp_read_time,
            'file_size': shp_size,
            'feature_count': shp_count
        },
        'geopackage': {
            'write_time': gpkg_write_time,
            'read_time': gpkg_read_time,
            'file_size': gpkg_size,
            'feature_count': gpkg_count
        }
    }
    
    return results

def write_shapefile_simple(file_path, test_data, srs):
    """写入Shapefile（简化版）"""
    # 删除现有文件
    base_name = os.path.splitext(file_path)[0]
    for ext in ['.shp', '.shx', '.dbf', '.prj']:
        related_file = base_name + ext
        if os.path.exists(related_file):
            os.remove(related_file)
    
    # 创建驱动和数据源
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.CreateDataSource(file_path)
    layer = datasource.CreateLayer("points", srs, ogr.wkbPoint)
    
    # 添加字段
    id_field = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(id_field)
    
    name_field = ogr.FieldDefn("name", ogr.OFTString)
    name_field.SetWidth(20)
    layer.CreateField(name_field)
    
    cat_field = ogr.FieldDefn("category", ogr.OFTString)
    cat_field.SetWidth(10)
    layer.CreateField(cat_field)
    
    val_field = ogr.FieldDefn("value", ogr.OFTReal)
    val_field.SetPrecision(2)
    layer.CreateField(val_field)
    
    # 添加要素
    for geom, attributes in test_data:
        feature = ogr.Feature(layer.GetLayerDefn())
        
        feature.SetField("id", attributes['id'])
        feature.SetField("name", attributes['name'])
        feature.SetField("category", attributes['category'])
        feature.SetField("value", attributes['value'])
        feature.SetGeometry(geom)
        
        layer.CreateFeature(feature)
        feature = None
    
    datasource = None

def write_geopackage_simple(file_path, test_data, srs):
    """写入GeoPackage（简化版）"""
    # 删除现有文件
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 创建驱动和数据源
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.CreateDataSource(file_path)
    layer = datasource.CreateLayer("points", srs, ogr.wkbPoint)
    
    # 添加字段
    id_field = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(id_field)
    
    name_field = ogr.FieldDefn("name", ogr.OFTString)
    name_field.SetWidth(20)
    layer.CreateField(name_field)
    
    cat_field = ogr.FieldDefn("category", ogr.OFTString)
    cat_field.SetWidth(10)
    layer.CreateField(cat_field)
    
    val_field = ogr.FieldDefn("value", ogr.OFTReal)
    val_field.SetPrecision(2)
    layer.CreateField(val_field)
    
    # 添加要素
    for geom, attributes in test_data:
        feature = ogr.Feature(layer.GetLayerDefn())
        
        feature.SetField("id", attributes['id'])
        feature.SetField("name", attributes['name'])
        feature.SetField("category", attributes['category'])
        feature.SetField("value", attributes['value'])
        feature.SetGeometry(geom)
        
        layer.CreateFeature(feature)
        feature = None
    
    datasource = None

def read_file_simple(file_path):
    """读取文件并返回要素数量"""
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
    
    # 遍历所有要素
    for feature in layer:
        # 模拟数据访问
        _ = feature.GetField("name")
        _ = feature.GetField("value")
        geom = feature.GetGeometryRef()
        if geom:
            _ = geom.GetX()
            _ = geom.GetY()
        feature_count += 1
    
    datasource = None
    return feature_count

def get_shapefile_size(shp_path):
    """获取Shapefile总大小"""
    base_name = os.path.splitext(shp_path)[0]
    total_size = 0
    
    for ext in ['.shp', '.shx', '.dbf', '.prj']:
        file_path = base_name + ext
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    return total_size

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def print_result(size, result):
    """打印单次测试结果"""
    shp = result['shapefile']
    gpkg = result['geopackage']
    
    print(f"\n  结果 ({size:,} 要素):")
    print(f"    写入时间: Shapefile {shp['write_time']:.3f}s | GeoPackage {gpkg['write_time']:.3f}s")
    print(f"    读取时间: Shapefile {shp['read_time']:.3f}s | GeoPackage {gpkg['read_time']:.3f}s")
    print(f"    文件大小: Shapefile {format_size(shp['file_size'])} | GeoPackage {format_size(gpkg['file_size'])}")
    print(f"    要素验证: Shapefile {shp['feature_count']} | GeoPackage {gpkg['feature_count']}")
    
    # 计算性能比率
    if gpkg['write_time'] > 0:
        write_ratio = shp['write_time'] / gpkg['write_time']
        print(f"    写入性能比: {write_ratio:.2f}x (Shapefile相对GeoPackage)")
    
    if gpkg['read_time'] > 0:
        read_ratio = shp['read_time'] / gpkg['read_time']
        print(f"    读取性能比: {read_ratio:.2f}x (Shapefile相对GeoPackage)")
    
    if gpkg['file_size'] > 0:
        size_ratio = shp['file_size'] / gpkg['file_size']
        print(f"    文件大小比: {size_ratio:.2f}x (Shapefile相对GeoPackage)")

def print_summary(results):
    """打印测试总结"""
    print(f"\n{'='*50}")
    print("性能测试总结")
    print("="*50)
    
    # 计算平均性能
    write_ratios = []
    read_ratios = []
    size_ratios = []
    
    for size, result in results.items():
        shp = result['shapefile']
        gpkg = result['geopackage']
        
        if gpkg['write_time'] > 0:
            write_ratios.append(shp['write_time'] / gpkg['write_time'])
        if gpkg['read_time'] > 0:
            read_ratios.append(shp['read_time'] / gpkg['read_time'])
        if gpkg['file_size'] > 0:
            size_ratios.append(shp['file_size'] / gpkg['file_size'])
    
    if write_ratios:
        avg_write = sum(write_ratios) / len(write_ratios)
        print(f"平均写入性能比: {avg_write:.2f}x (Shapefile相对GeoPackage)")
        
    if read_ratios:
        avg_read = sum(read_ratios) / len(read_ratios)
        print(f"平均读取性能比: {avg_read:.2f}x (Shapefile相对GeoPackage)")
        
    if size_ratios:
        avg_size = sum(size_ratios) / len(size_ratios)
        print(f"平均文件大小比: {avg_size:.2f}x (Shapefile相对GeoPackage)")
    
    print(f"\n建议:")
    
    if write_ratios and sum(write_ratios) / len(write_ratios) < 1:
        print("✓ 写入性能: Shapefile 更快")
    else:
        print("✓ 写入性能: GeoPackage 更快")
    
    if read_ratios and sum(read_ratios) / len(read_ratios) < 1:
        print("✓ 读取性能: Shapefile 更快")  
    else:
        print("✓ 读取性能: GeoPackage 更快")
    
    if size_ratios and sum(size_ratios) / len(size_ratios) < 1:
        print("✓ 文件大小: Shapefile 更小")
    else:
        print("✓ 文件大小: GeoPackage 更小")

if __name__ == "__main__":
    try:
        print("开始快速性能测试...")
        results = quick_performance_test()
        print(f"\n测试完成！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()