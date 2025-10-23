#!/usr/bin/env python3
"""
GDAL完整几何类型测试程序
测试GDAL支持的所有几何类型的创建
"""

import os
import sys
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def create_comprehensive_geometry_test():
    """创建综合几何类型测试"""
    print("GDAL完整几何类型测试")
    print("=" * 60)
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    
    # 定义所有要测试的几何类型
    geometry_tests = [
        {
            'type': ogr.wkbPoint,
            'name': 'Point',
            'chinese': '点',
            'create_func': create_point,
            'description': '单个点几何'
        },
        {
            'type': ogr.wkbLineString,
            'name': 'LineString',
            'chinese': '线',
            'create_func': create_linestring,
            'description': '线性几何'
        },
        {
            'type': ogr.wkbPolygon,
            'name': 'Polygon',
            'chinese': '多边形',
            'create_func': create_polygon,
            'description': '多边形几何'
        },
        {
            'type': ogr.wkbMultiPoint,
            'name': 'MultiPoint',
            'chinese': '多点',
            'create_func': create_multipoint,
            'description': '多个点的集合'
        },
        {
            'type': ogr.wkbMultiLineString,
            'name': 'MultiLineString',
            'chinese': '多线',
            'create_func': create_multilinestring,
            'description': '多条线的集合'
        },
        {
            'type': ogr.wkbMultiPolygon,
            'name': 'MultiPolygon',
            'chinese': '多多边形',
            'create_func': create_multipolygon,
            'description': '多个多边形的集合'
        },
        {
            'type': ogr.wkbGeometryCollection,
            'name': 'GeometryCollection',
            'chinese': '几何集合',
            'create_func': create_geometry_collection,
            'description': '混合几何类型集合'
        }
    ]
    
    # 测试每种格式
    output_formats = [
        ("Memory", "", "内存格式"),
        ("GeoJSON", "geometry_types.geojson", "GeoJSON格式"),
        ("GPKG", "geometry_types.gpkg", "GeoPackage格式"),
    ]
    
    results = {}
    
    for format_name, filename, format_desc in output_formats:
        print(f"\n测试 {format_name} ({format_desc}):")
        results[format_name] = test_format_with_geometries(
            format_name, filename, output_dir, srs, geometry_tests
        )
    
    # 输出结果摘要
    print("\n" + "=" * 60)
    print("几何类型支持情况摘要")
    print("=" * 60)
    
    # 创建表格显示
    print(f"{'几何类型':15s} {'中文名':8s} {'Memory':8s} {'GeoJSON':8s} {'GPKG':8s}")
    print("-" * 60)
    
    for geom_test in geometry_tests:
        geom_name = geom_test['name']
        chinese_name = geom_test['chinese']
        
        memory_status = "✓" if results.get("Memory", {}).get(geom_name, False) else "✗"
        geojson_status = "✓" if results.get("GeoJSON", {}).get(geom_name, False) else "✗"
        gpkg_status = "✓" if results.get("GPKG", {}).get(geom_name, False) else "✗"
        
        print(f"{geom_name:15s} {chinese_name:8s} {memory_status:8s} {geojson_status:8s} {gpkg_status:8s}")
    
    print(f"\n测试文件保存在: {output_dir}")

def test_format_with_geometries(format_name, filename, output_dir, srs, geometry_tests):
    """测试特定格式支持的几何类型"""
    results = {}
    
    try:
        # 获取驱动
        driver = ogr.GetDriverByName(format_name)
        if driver is None:
            print(f"  ✗ 无法获取 {format_name} 驱动")
            return results
        
        # 创建数据源
        if format_name == "Memory":
            datasource = driver.CreateDataSource("")
        else:
            file_path = os.path.join(output_dir, filename)
            # 删除现有文件
            if os.path.exists(file_path):
                os.remove(file_path)
            datasource = driver.CreateDataSource(file_path)
        
        if datasource is None:
            print(f"  ✗ 无法创建 {format_name} 数据源")
            return results
        
        # 测试每种几何类型
        for geom_test in geometry_tests:
            geom_type = geom_test['type']
            geom_name = geom_test['name']
            chinese_name = geom_test['chinese']
            create_func = geom_test['create_func']
            
            try:
                # 创建图层
                layer_name = f"layer_{geom_name.lower()}"
                layer = datasource.CreateLayer(layer_name, srs, geom_type)
                
                if layer is None:
                    print(f"    ✗ {geom_name} ({chinese_name}) 图层创建失败")
                    results[geom_name] = False
                    continue
                
                # 添加属性字段
                id_field = ogr.FieldDefn("id", ogr.OFTInteger)
                layer.CreateField(id_field)
                
                name_field = ogr.FieldDefn("name", ogr.OFTString)
                name_field.SetWidth(50)
                layer.CreateField(name_field)
                
                type_field = ogr.FieldDefn("geom_type", ogr.OFTString)
                type_field.SetWidth(30)
                layer.CreateField(type_field)
                
                # 创建要素
                feature_defn = layer.GetLayerDefn()
                feature = ogr.Feature(feature_defn)
                feature.SetField("id", 1)
                feature.SetField("name", f"测试{chinese_name}")
                feature.SetField("geom_type", geom_name)
                
                # 创建几何体
                geom = create_func()
                if geom is not None:
                    feature.SetGeometry(geom)
                
                # 添加要素
                result = layer.CreateFeature(feature)
                if result == 0:
                    print(f"    ✓ {geom_name} ({chinese_name}) 创建成功")
                    results[geom_name] = True
                else:
                    print(f"    ✗ {geom_name} ({chinese_name}) 要素创建失败")
                    results[geom_name] = False
                
                # 清理
                feature = None
                
            except Exception as e:
                print(f"    ✗ {geom_name} ({chinese_name}) 异常: {e}")
                results[geom_name] = False
        
        # 关闭数据源
        datasource = None
        
    except Exception as e:
        print(f"  ✗ {format_name} 格式测试失败: {e}")
    
    return results

# 几何体创建函数
def create_point():
    """创建点几何"""
    geom = ogr.Geometry(ogr.wkbPoint)
    geom.AddPoint(116.3974, 39.9093)  # 北京天安门
    return geom

def create_linestring():
    """创建线几何"""
    geom = ogr.Geometry(ogr.wkbLineString)
    # 北京到上海的路线
    geom.AddPoint(116.3974, 39.9093)  # 北京
    geom.AddPoint(117.5, 37.5)        # 天津
    geom.AddPoint(119.0, 35.0)        # 济南
    geom.AddPoint(121.4737, 31.2304)  # 上海
    return geom

def create_polygon():
    """创建多边形几何"""
    # 创建外环
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(116.0, 39.5)  # 左下
    ring.AddPoint(117.0, 39.5)  # 右下
    ring.AddPoint(117.0, 40.5)  # 右上
    ring.AddPoint(116.0, 40.5)  # 左上
    ring.AddPoint(116.0, 39.5)  # 闭合
    
    # 创建多边形
    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(ring)
    
    # 添加内环（洞）
    hole = ogr.Geometry(ogr.wkbLinearRing)
    hole.AddPoint(116.3, 39.8)
    hole.AddPoint(116.7, 39.8)
    hole.AddPoint(116.7, 40.2)
    hole.AddPoint(116.3, 40.2)
    hole.AddPoint(116.3, 39.8)
    geom.AddGeometry(hole)
    
    return geom

def create_multipoint():
    """创建多点几何"""
    geom = ogr.Geometry(ogr.wkbMultiPoint)
    
    # 添加多个城市点
    cities = [
        (116.3974, 39.9093),  # 北京
        (121.4737, 31.2304),  # 上海
        (113.3333, 23.1333),  # 广州
        (104.0667, 30.5667),  # 成都
    ]
    
    for lon, lat in cities:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        geom.AddGeometry(point)
    
    return geom

def create_multilinestring():
    """创建多线几何"""
    geom = ogr.Geometry(ogr.wkbMultiLineString)
    
    # 第一条线：北京-天津
    line1 = ogr.Geometry(ogr.wkbLineString)
    line1.AddPoint(116.3974, 39.9093)  # 北京
    line1.AddPoint(117.2, 39.1)        # 天津
    geom.AddGeometry(line1)
    
    # 第二条线：上海-苏州
    line2 = ogr.Geometry(ogr.wkbLineString)
    line2.AddPoint(121.4737, 31.2304)  # 上海
    line2.AddPoint(120.6, 31.3)        # 苏州
    geom.AddGeometry(line2)
    
    return geom

def create_multipolygon():
    """创建多多边形几何"""
    geom = ogr.Geometry(ogr.wkbMultiPolygon)
    
    # 第一个多边形（北京区域）
    ring1 = ogr.Geometry(ogr.wkbLinearRing)
    ring1.AddPoint(116.0, 39.5)
    ring1.AddPoint(117.0, 39.5)
    ring1.AddPoint(117.0, 40.5)
    ring1.AddPoint(116.0, 40.5)
    ring1.AddPoint(116.0, 39.5)
    
    poly1 = ogr.Geometry(ogr.wkbPolygon)
    poly1.AddGeometry(ring1)
    geom.AddGeometry(poly1)
    
    # 第二个多边形（上海区域）
    ring2 = ogr.Geometry(ogr.wkbLinearRing)
    ring2.AddPoint(121.0, 31.0)
    ring2.AddPoint(122.0, 31.0)
    ring2.AddPoint(122.0, 32.0)
    ring2.AddPoint(121.0, 32.0)
    ring2.AddPoint(121.0, 31.0)
    
    poly2 = ogr.Geometry(ogr.wkbPolygon)
    poly2.AddGeometry(ring2)
    geom.AddGeometry(poly2)
    
    return geom

def create_geometry_collection():
    """创建几何集合"""
    geom = ogr.Geometry(ogr.wkbGeometryCollection)
    
    # 添加一个点
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(116.3974, 39.9093)
    geom.AddGeometry(point)
    
    # 添加一条线
    line = ogr.Geometry(ogr.wkbLineString)
    line.AddPoint(117.0, 40.0)
    line.AddPoint(118.0, 41.0)
    geom.AddGeometry(line)
    
    # 添加一个多边形
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(119.0, 39.0)
    ring.AddPoint(120.0, 39.0)
    ring.AddPoint(120.0, 40.0)
    ring.AddPoint(119.0, 40.0)
    ring.AddPoint(119.0, 39.0)
    
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    geom.AddGeometry(polygon)
    
    return geom

if __name__ == "__main__":
    create_comprehensive_geometry_test()