#!/usr/bin/env python3
"""
GDAL图层类型测试程序（修正版）
验证GDAL中可以创建的不同图层类型
"""

import os
import sys
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def check_gdal_version():
    """检查GDAL版本信息"""
    print(f"GDAL Version: {gdal.VersionInfo()}")
    print(f"GDAL Release Name: {gdal.VersionInfo('RELEASE_NAME')}")
    print("-" * 50)

def get_supported_drivers():
    """获取主要的OGR驱动程序"""
    print("主要的OGR驱动程序:")
    
    important_drivers = [
        "Memory", "ESRI Shapefile", "GeoJSON", "GPKG", 
        "CSV", "KML", "GML", "SQLite"
    ]
    
    available_drivers = []
    driver_count = ogr.GetDriverCount()
    
    for i in range(driver_count):
        driver = ogr.GetDriver(i)
        driver_name = driver.GetName()
        if driver_name in important_drivers:
            available_drivers.append(driver_name)
            print(f"  ✓ {driver_name}")
    
    print(f"\n检查到 {len(available_drivers)}/{len(important_drivers)} 个重要驱动")
    print(f"总共支持 {driver_count} 种驱动程序")
    print("-" * 50)
    return available_drivers

def test_geometry_types():
    """测试不同的几何图形类型"""
    print("支持的几何图形类型:")
    
    geometry_types = [
        (ogr.wkbPoint, "Point", "点"),
        (ogr.wkbLineString, "LineString", "线"),
        (ogr.wkbPolygon, "Polygon", "多边形"),
        (ogr.wkbMultiPoint, "MultiPoint", "多点"),
        (ogr.wkbMultiLineString, "MultiLineString", "多线"),
        (ogr.wkbMultiPolygon, "MultiPolygon", "多多边形"),
    ]
    
    for geom_type, name, chinese_name in geometry_types:
        print(f"  {geom_type:2d}: {name:15s} ({chinese_name})")
    
    print("-" * 50)
    return geometry_types

def create_test_geometry(geom_type):
    """根据几何类型创建测试几何体"""
    if geom_type == ogr.wkbPoint:
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(116.3974, 39.9093)  # 北京坐标
        return geom
    
    elif geom_type == ogr.wkbLineString:
        geom = ogr.Geometry(ogr.wkbLineString)
        geom.AddPoint(116.3974, 39.9093)  # 北京
        geom.AddPoint(121.4737, 31.2304)  # 上海
        return geom
    
    elif geom_type == ogr.wkbPolygon:
        # 创建一个矩形
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(116.0, 39.5)
        ring.AddPoint(117.0, 39.5)
        ring.AddPoint(117.0, 40.5)
        ring.AddPoint(116.0, 40.5)
        ring.AddPoint(116.0, 39.5)  # 闭合
        
        geom = ogr.Geometry(ogr.wkbPolygon)
        geom.AddGeometry(ring)
        return geom
    
    elif geom_type == ogr.wkbMultiPoint:
        geom = ogr.Geometry(ogr.wkbMultiPoint)
        
        point1 = ogr.Geometry(ogr.wkbPoint)
        point1.AddPoint(116.3974, 39.9093)
        geom.AddGeometry(point1)
        
        point2 = ogr.Geometry(ogr.wkbPoint)
        point2.AddPoint(121.4737, 31.2304)
        geom.AddGeometry(point2)
        
        return geom
    
    elif geom_type == ogr.wkbMultiLineString:
        geom = ogr.Geometry(ogr.wkbMultiLineString)
        
        line1 = ogr.Geometry(ogr.wkbLineString)
        line1.AddPoint(116.0, 39.0)
        line1.AddPoint(117.0, 40.0)
        geom.AddGeometry(line1)
        
        line2 = ogr.Geometry(ogr.wkbLineString)
        line2.AddPoint(121.0, 31.0)
        line2.AddPoint(122.0, 32.0)
        geom.AddGeometry(line2)
        
        return geom
    
    elif geom_type == ogr.wkbMultiPolygon:
        geom = ogr.Geometry(ogr.wkbMultiPolygon)
        
        # 创建第一个多边形
        ring1 = ogr.Geometry(ogr.wkbLinearRing)
        ring1.AddPoint(116.0, 39.0)
        ring1.AddPoint(117.0, 39.0)
        ring1.AddPoint(117.0, 40.0)
        ring1.AddPoint(116.0, 40.0)
        ring1.AddPoint(116.0, 39.0)
        
        poly1 = ogr.Geometry(ogr.wkbPolygon)
        poly1.AddGeometry(ring1)
        geom.AddGeometry(poly1)
        
        return geom
    
    return None

def test_memory_driver():
    """测试内存驱动"""
    print("\n测试内存驱动:")
    
    try:
        # 创建坐标系统
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # WGS84
        
        # 获取驱动
        driver = ogr.GetDriverByName("Memory")
        if driver is None:
            print("  ✗ 无法获取Memory驱动")
            return False
        
        # 创建数据源（使用空字符串）
        datasource = driver.CreateDataSource("")
        if datasource is None:
            print("  ✗ 无法创建Memory数据源")
            return False
        
        print("  ✓ Memory数据源创建成功")
        
        # 测试基本几何类型
        basic_types = [
            (ogr.wkbPoint, "Point", "点"),
            (ogr.wkbLineString, "LineString", "线"),
            (ogr.wkbPolygon, "Polygon", "多边形"),
            (ogr.wkbMultiPoint, "MultiPoint", "多点"),
        ]
        
        success_count = 0
        
        for geom_type, geom_name, chinese_name in basic_types:
            try:
                layer_name = f"layer_{geom_name.lower()}"
                layer = datasource.CreateLayer(layer_name, srs, geom_type)
                
                if layer is None:
                    print(f"    ✗ {geom_name} ({chinese_name}) 图层创建失败")
                    continue
                
                # 添加属性字段
                id_field = ogr.FieldDefn("id", ogr.OFTInteger)
                layer.CreateField(id_field)
                
                name_field = ogr.FieldDefn("name", ogr.OFTString)
                name_field.SetWidth(50)
                layer.CreateField(name_field)
                
                # 创建要素
                feature_defn = layer.GetLayerDefn()
                feature = ogr.Feature(feature_defn)
                feature.SetField("id", 1)
                feature.SetField("name", f"测试{chinese_name}")
                
                # 创建几何体
                geom = create_test_geometry(geom_type)
                if geom is not None:
                    feature.SetGeometry(geom)
                
                # 添加要素到图层
                result = layer.CreateFeature(feature)
                if result == 0:  # 0表示成功
                    print(f"    ✓ {geom_name} ({chinese_name}) 图层创建成功")
                    success_count += 1
                else:
                    print(f"    ✗ {geom_name} ({chinese_name}) 要素创建失败，错误码: {result}")
                
                # 清理
                feature = None
            
            except Exception as e:
                print(f"    ✗ {geom_name} ({chinese_name}) 创建异常: {e}")
        
        print(f"  内存驱动测试结果: {success_count}/4 种基本类型成功")
        
        # 清理
        datasource = None
        return success_count > 0
        
    except Exception as e:
        print(f"  ✗ Memory驱动测试失败: {e}")
        return False

def test_file_drivers():
    """测试文件驱动"""
    print("\n测试文件驱动:")
    
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output"
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"  创建输出目录: {output_dir}")
    
    # 测试不同的输出格式
    test_formats = [
        ("GeoJSON", "test_point.geojson", "JSON地理数据"),
        ("GPKG", "test_point.gpkg", "GeoPackage数据库"),
        ("ESRI Shapefile", "test_point.shp", "Shapefile文件"),
    ]
    
    success_drivers = []
    
    for driver_name, filename, description in test_formats:
        try:
            print(f"  测试 {driver_name} ({description}):")
            
            # 获取驱动
            driver = ogr.GetDriverByName(driver_name)
            if driver is None:
                print(f"    ✗ 无法获取 {driver_name} 驱动")
                continue
            
            # 创建文件路径
            file_path = os.path.join(output_dir, filename)
            
            # 如果文件存在，先删除
            if os.path.exists(file_path):
                try:
                    if driver_name == "ESRI Shapefile":
                        # Shapefile需要删除多个相关文件
                        base_name = os.path.splitext(file_path)[0]
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            related_file = base_name + ext
                            if os.path.exists(related_file):
                                os.remove(related_file)
                    else:
                        os.remove(file_path)
                except Exception as e:
                    print(f"    警告: 删除旧文件失败: {e}")
            
            # 创建数据源
            datasource = driver.CreateDataSource(file_path)
            if datasource is None:
                print(f"    ✗ 无法创建 {driver_name} 数据源")
                continue
            
            # 创建坐标系统
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            
            # 创建一个点图层进行测试
            layer = datasource.CreateLayer("test_points", srs, ogr.wkbPoint)
            if layer is None:
                print(f"    ✗ 无法创建图层")
                datasource = None
                continue
            
            # 添加字段
            id_field = ogr.FieldDefn("id", ogr.OFTInteger)
            layer.CreateField(id_field)
            
            name_field = ogr.FieldDefn("name", ogr.OFTString)
            name_field.SetWidth(50)
            layer.CreateField(name_field)
            
            city_field = ogr.FieldDefn("city", ogr.OFTString)
            city_field.SetWidth(30)
            layer.CreateField(city_field)
            
            # 创建测试数据
            test_points = [
                (1, "天安门", "北京", 116.3974, 39.9093),
                (2, "外滩", "上海", 121.4737, 31.2304),
                (3, "小蛮腰", "广州", 113.3333, 23.1333),
            ]
            
            feature_count = 0
            for point_id, name, city, lon, lat in test_points:
                # 创建要素
                feature_defn = layer.GetLayerDefn()
                feature = ogr.Feature(feature_defn)
                feature.SetField("id", point_id)
                feature.SetField("name", name)
                feature.SetField("city", city)
                
                # 创建几何体
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(lon, lat)
                feature.SetGeometry(point)
                
                # 添加要素
                result = layer.CreateFeature(feature)
                if result == 0:
                    feature_count += 1
                else:
                    print(f"    警告: 要素 {name} 创建失败")
                
                # 清理
                feature = None
            
            if feature_count == len(test_points):
                print(f"    ✓ {driver_name} 测试成功，创建了 {feature_count} 个要素")
                success_drivers.append(driver_name)
                print(f"    文件保存为: {file_path}")
            else:
                print(f"    ✗ {driver_name} 部分失败，只创建了 {feature_count}/{len(test_points)} 个要素")
            
            # 关闭数据源
            datasource = None
            
        except Exception as e:
            print(f"    ✗ {driver_name} 测试失败: {e}")
    
    return success_drivers

def main():
    """主函数"""
    print("GDAL图层类型验证程序")
    print("=" * 60)
    print("用于验证GDAL中可以创建的不同图层类型")
    print("=" * 60)
    
    try:
        # 检查GDAL版本
        check_gdal_version()
        
        # 获取支持的驱动程序
        drivers = get_supported_drivers()
        
        # 测试几何类型
        geometry_types = test_geometry_types()
        
        # 测试内存驱动
        memory_success = test_memory_driver()
        
        # 测试文件驱动
        file_drivers = test_file_drivers()
        
        # 输出最终结果
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)
        print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
        print(f"内存驱动测试: {'✓ 成功' if memory_success else '✗ 失败'}")
        print(f"支持的文件格式: {len(file_drivers)} 种")
        
        if file_drivers:
            print("成功测试的文件驱动:")
            for driver in file_drivers:
                print(f"  ✓ {driver}")
        else:
            print("  ✗ 没有成功的文件驱动")
        
        output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output"
        print(f"\n测试文件保存在: {output_dir}")
        print("\n可以使用QGIS等GIS软件打开生成的文件进行验证。")
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()