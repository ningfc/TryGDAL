#!/usr/bin/env python3
"""
Shapefile几何类型支持测试程序
专门测试Shapefile格式支持的几何类型，特别是多部分面
"""

import os
import sys
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def test_shapefile_geometry_support():
    """测试Shapefile支持的几何类型"""
    print("Shapefile几何类型支持测试")
    print("=" * 60)
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/shapefile_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    
    # 定义要测试的几何类型
    geometry_tests = [
        {
            'type': ogr.wkbPoint,
            'name': 'Point',
            'chinese': '点',
            'filename': 'points.shp',
            'create_func': create_test_point,
            'shapefile_support': True,
            'description': '单个点几何'
        },
        {
            'type': ogr.wkbMultiPoint,
            'name': 'MultiPoint',
            'chinese': '多点',
            'filename': 'multipoints.shp',
            'create_func': create_test_multipoint,
            'shapefile_support': True,
            'description': '多个点的集合'
        },
        {
            'type': ogr.wkbLineString,
            'name': 'LineString',
            'chinese': '线',
            'filename': 'lines.shp',
            'create_func': create_test_linestring,
            'shapefile_support': True,
            'description': '单条线几何'
        },
        {
            'type': ogr.wkbMultiLineString,
            'name': 'MultiLineString',
            'chinese': '多线',
            'filename': 'multilines.shp',
            'create_func': create_test_multilinestring,
            'shapefile_support': True,
            'description': '多条线的集合'
        },
        {
            'type': ogr.wkbPolygon,
            'name': 'Polygon',
            'chinese': '多边形',
            'filename': 'polygons.shp',
            'create_func': create_test_polygon,
            'shapefile_support': True,
            'description': '单个多边形（可包含洞）'
        },
        {
            'type': ogr.wkbMultiPolygon,
            'name': 'MultiPolygon',
            'chinese': '多部分面',
            'filename': 'multipolygons.shp',
            'create_func': create_test_multipolygon,
            'shapefile_support': True,
            'description': '多个多边形的集合（多部分面）'
        },
        {
            'type': ogr.wkbGeometryCollection,
            'name': 'GeometryCollection',
            'chinese': '几何集合',
            'filename': 'geomcollection.shp',
            'create_func': create_test_geometry_collection,
            'shapefile_support': False,  # Shapefile不支持混合几何类型
            'description': '混合几何类型集合（Shapefile不支持）'
        }
    ]
    
    # 获取Shapefile驱动
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if not driver:
        print("错误: 无法获取ESRI Shapefile驱动")
        return
    
    print(f"测试目录: {output_dir}")
    print("-" * 60)
    
    results = {}
    
    for geom_test in geometry_tests:
        geom_type = geom_test['type']
        geom_name = geom_test['name']
        chinese_name = geom_test['chinese']
        filename = geom_test['filename']
        create_func = geom_test['create_func']
        expected_support = geom_test['shapefile_support']
        description = geom_test['description']
        
        print(f"\n测试 {geom_name} ({chinese_name}):")
        print(f"  描述: {description}")
        print(f"  预期支持: {'是' if expected_support else '否'}")
        
        try:
            # 创建文件路径
            file_path = os.path.join(output_dir, filename)
            
            # 删除现有文件
            if os.path.exists(file_path):
                # 删除所有相关文件
                base_name = os.path.splitext(file_path)[0]
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    related_file = base_name + ext
                    if os.path.exists(related_file):
                        os.remove(related_file)
            
            # 创建数据源
            datasource = driver.CreateDataSource(file_path)
            if datasource is None:
                print(f"  ✗ 无法创建Shapefile数据源")
                results[geom_name] = False
                continue
            
            # 创建图层
            layer = datasource.CreateLayer("layer", srs, geom_type)
            if layer is None:
                print(f"  ✗ 无法创建 {geom_name} 图层")
                results[geom_name] = False
                datasource = None
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
            
            area_field = ogr.FieldDefn("area", ogr.OFTReal)
            area_field.SetPrecision(2)
            layer.CreateField(area_field)
            
            # 创建多个要素进行测试
            feature_count = 0
            test_data = create_func()
            
            for i, (geom, name, description_text) in enumerate(test_data):
                # 创建要素
                feature_defn = layer.GetLayerDefn()
                feature = ogr.Feature(feature_defn)
                feature.SetField("id", i + 1)
                feature.SetField("name", name)
                feature.SetField("geom_type", geom_name)
                
                # 计算面积（如果是面几何）
                if geom_type in [ogr.wkbPolygon, ogr.wkbMultiPolygon]:
                    area = geom.GetArea() if geom else 0.0
                    feature.SetField("area", area)
                else:
                    feature.SetField("area", 0.0)
                
                if geom is not None:
                    feature.SetGeometry(geom)
                
                # 添加要素
                result = layer.CreateFeature(feature)
                if result == 0:
                    feature_count += 1
                else:
                    print(f"    警告: 要素 {name} 创建失败")
                
                # 清理
                feature = None
            
            if feature_count > 0:
                print(f"  ✓ {geom_name} 支持成功，创建了 {feature_count} 个要素")
                print(f"  文件: {filename}")
                results[geom_name] = True
                
                # 验证文件大小
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"  文件大小: {file_size} bytes")
            else:
                print(f"  ✗ {geom_name} 无法创建要素")
                results[geom_name] = False
            
            # 关闭数据源
            datasource = None
            
        except Exception as e:
            print(f"  ✗ {geom_name} 测试异常: {e}")
            results[geom_name] = False
    
    # 输出结果摘要
    print("\n" + "=" * 60)
    print("Shapefile几何类型支持摘要")
    print("=" * 60)
    
    print(f"{'几何类型':18s} {'中文名':10s} {'预期':6s} {'实际':6s} {'状态':6s}")
    print("-" * 60)
    
    for geom_test in geometry_tests:
        geom_name = geom_test['name']
        chinese_name = geom_test['chinese']
        expected = geom_test['shapefile_support']
        actual = results.get(geom_name, False)
        
        expected_str = "支持" if expected else "不支持"
        actual_str = "✓" if actual else "✗"
        
        if expected == actual:
            status = "✓"
        else:
            status = "⚠️"
        
        print(f"{geom_name:18s} {chinese_name:10s} {expected_str:6s} {actual_str:6s} {status:6s}")
    
    print(f"\n测试文件保存在: {output_dir}")
    return results

def create_test_point():
    """创建测试点数据"""
    test_data = []
    
    # 北京市主要地标
    locations = [
        (116.3974, 39.9093, "天安门", "北京市中心，国家象征"),
        (116.4074, 39.9042, "故宫", "明清两代皇宫"),
        (116.3683, 39.9150, "西单", "繁华商业区"),
        (116.4167, 39.9167, "王府井", "著名商业街")
    ]
    
    for lon, lat, name, desc in locations:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        test_data.append((point, name, desc))
    
    return test_data

def create_test_multipoint():
    """创建测试多点数据"""
    test_data = []
    
    # 北京地铁站群
    station_groups = [
        {
            'name': '国贸站群',
            'desc': '国贸商圈地铁站',
            'stations': [(116.4619, 39.9078), (116.4639, 39.9088), (116.4599, 39.9068)]
        },
        {
            'name': '西单站群', 
            'desc': '西单商圈地铁站',
            'stations': [(116.3683, 39.9150), (116.3693, 39.9160), (116.3673, 39.9140)]
        }
    ]
    
    for group in station_groups:
        multipoint = ogr.Geometry(ogr.wkbMultiPoint)
        for lon, lat in group['stations']:
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(lon, lat)
            multipoint.AddGeometry(point)
        test_data.append((multipoint, group['name'], group['desc']))
    
    return test_data

def create_test_linestring():
    """创建测试线数据"""
    test_data = []
    
    # 北京主要道路
    roads = [
        {
            'name': '长安街',
            'desc': '北京最重要的东西向道路',
            'coords': [(116.3200, 39.9093), (116.3974, 39.9093), (116.4800, 39.9093)]
        },
        {
            'name': '二环路东段',
            'desc': '北京二环路东部',
            'coords': [(116.4270, 39.8800), (116.4470, 39.9093), (116.4270, 39.9400)]
        }
    ]
    
    for road in roads:
        line = ogr.Geometry(ogr.wkbLineString)
        for lon, lat in road['coords']:
            line.AddPoint(lon, lat)
        test_data.append((line, road['name'], road['desc']))
    
    return test_data

def create_test_multilinestring():
    """创建测试多线数据"""
    test_data = []
    
    # 复杂道路系统
    road_systems = [
        {
            'name': '三环路系统',
            'desc': '北京三环路及匝道',
            'lines': [
                [(116.3500, 39.8500), (116.4500, 39.8500), (116.5000, 39.9000)],  # 主路
                [(116.4500, 39.8500), (116.4600, 39.8600)]  # 匝道
            ]
        }
    ]
    
    for system in road_systems:
        multiline = ogr.Geometry(ogr.wkbMultiLineString)
        for line_coords in system['lines']:
            line = ogr.Geometry(ogr.wkbLineString)
            for lon, lat in line_coords:
                line.AddPoint(lon, lat)
            multiline.AddGeometry(line)
        test_data.append((multiline, system['name'], system['desc']))
    
    return test_data

def create_test_polygon():
    """创建测试多边形数据"""
    test_data = []
    
    # 北京市区域
    areas = [
        {
            'name': '天安门广场',
            'desc': '世界最大的城市广场',
            'outer': [(116.3914, 39.9031), (116.4014, 39.9031), (116.4014, 39.9131), (116.3914, 39.9131), (116.3914, 39.9031)],
            'holes': []  # 无洞
        },
        {
            'name': '故宫',
            'desc': '紫禁城，含内廷',
            'outer': [(116.3850, 39.9050), (116.4200, 39.9050), (116.4200, 39.9250), (116.3850, 39.9250), (116.3850, 39.9050)],
            'holes': [[(116.4000, 39.9100), (116.4100, 39.9100), (116.4100, 39.9200), (116.4000, 39.9200), (116.4000, 39.9100)]]  # 内廷
        }
    ]
    
    for area in areas:
        # 创建外环
        outer_ring = ogr.Geometry(ogr.wkbLinearRing)
        for lon, lat in area['outer']:
            outer_ring.AddPoint(lon, lat)
        
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(outer_ring)
        
        # 添加洞
        for hole_coords in area['holes']:
            hole_ring = ogr.Geometry(ogr.wkbLinearRing)
            for lon, lat in hole_coords:
                hole_ring.AddPoint(lon, lat)
            polygon.AddGeometry(hole_ring)
        
        test_data.append((polygon, area['name'], area['desc']))
    
    return test_data

def create_test_multipolygon():
    """创建测试多部分面数据"""
    test_data = []
    
    # 多部分区域（这是测试的重点）
    multi_areas = [
        {
            'name': '北京大学校区',
            'desc': '北京大学的多个校区（主校区+分校区）',
            'polygons': [
                # 燕园主校区
                {
                    'outer': [(116.2950, 39.9950), (116.3150, 39.9950), (116.3150, 40.0050), (116.2950, 40.0050), (116.2950, 39.9950)],
                    'holes': []
                },
                # 医学部校区
                {
                    'outer': [(116.3550, 39.9850), (116.3650, 39.9850), (116.3650, 39.9950), (116.3550, 39.9950), (116.3550, 39.9850)],
                    'holes': []
                }
            ]
        },
        {
            'name': '朝阳公园水系',
            'desc': '朝阳公园内的多个独立湖泊',
            'polygons': [
                # 主湖
                {
                    'outer': [(116.4800, 39.9400), (116.4900, 39.9400), (116.4900, 39.9500), (116.4800, 39.9500), (116.4800, 39.9400)],
                    'holes': []
                },
                # 小湖1
                {
                    'outer': [(116.4850, 39.9350), (116.4880, 39.9350), (116.4880, 39.9380), (116.4850, 39.9380), (116.4850, 39.9350)],
                    'holes': []
                },
                # 小湖2
                {
                    'outer': [(116.4920, 39.9420), (116.4950, 39.9420), (116.4950, 39.9450), (116.4920, 39.9450), (116.4920, 39.9420)],
                    'holes': []
                }
            ]
        }
    ]
    
    for multi_area in multi_areas:
        multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
        
        for poly_data in multi_area['polygons']:
            # 创建外环
            outer_ring = ogr.Geometry(ogr.wkbLinearRing)
            for lon, lat in poly_data['outer']:
                outer_ring.AddPoint(lon, lat)
            
            polygon = ogr.Geometry(ogr.wkbPolygon)
            polygon.AddGeometry(outer_ring)
            
            # 添加洞（如果有）
            for hole_coords in poly_data['holes']:
                hole_ring = ogr.Geometry(ogr.wkbLinearRing)
                for lon, lat in hole_coords:
                    hole_ring.AddPoint(lon, lat)
                polygon.AddGeometry(hole_ring)
            
            multipolygon.AddGeometry(polygon)
        
        test_data.append((multipolygon, multi_area['name'], multi_area['desc']))
    
    return test_data

def create_test_geometry_collection():
    """创建测试几何集合数据（Shapefile不支持）"""
    test_data = []
    
    # 混合几何集合
    collection = ogr.Geometry(ogr.wkbGeometryCollection)
    
    # 添加点
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(116.3974, 39.9093)
    collection.AddGeometry(point)
    
    # 添加线
    line = ogr.Geometry(ogr.wkbLineString)
    line.AddPoint(116.3974, 39.9093)
    line.AddPoint(116.4074, 39.9193)
    collection.AddGeometry(line)
    
    test_data.append((collection, "混合几何集合", "包含点和线的集合"))
    
    return test_data

def analyze_multipolygon_support():
    """专门分析多部分面支持情况"""
    print("\n" + "=" * 60)
    print("多部分面（MultiPolygon）专项分析")
    print("=" * 60)
    
    print("多部分面的应用场景：")
    print("1. 群岛：由多个独立岛屿组成的国家或地区")
    print("2. 多校区：大学的多个分散校区")
    print("3. 连锁店：同一品牌在不同位置的门店")
    print("4. 行政区：包含飞地的行政区域")
    print("5. 湖泊群：一个公园内的多个独立湖泊")
    
    print("\nShapefile对多部分面的支持：")
    print("✓ 完全支持 MultiPolygon 几何类型")
    print("✓ 可以在单个要素中存储多个独立的多边形")
    print("✓ 每个子多边形都可以有自己的洞（holes）")
    print("✓ 适合存储复杂的地理区域")
    
    print("\n优势：")
    print("- 保持逻辑上的完整性（一个实体 = 一个要素）")
    print("- 共享相同的属性信息")
    print("- 空间查询更高效")
    print("- 符合GIS数据建模规范")

if __name__ == "__main__":
    results = test_shapefile_geometry_support()
    analyze_multipolygon_support()
    
    print(f"\n{'='*60}")
    print("总结：")
    print("Shapefile 是一种成熟的GIS格式，支持所有基本几何类型")
    print("包括多部分面（MultiPolygon），非常适合存储复杂的地理数据")
    print("唯一不支持的是 GeometryCollection（混合几何集合）")
    print("这是因为 Shapefile 要求单个文件中的所有要素具有相同的几何类型")