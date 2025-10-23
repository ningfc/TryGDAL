#!/usr/bin/env python3
"""
GDAL图层类型测试程序（简化版本）
验证GDAL中可以创建的不同图层类型
"""

import os
import sys
from osgeo import gdal, ogr, osr

# 启用GDAL错误处理
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def check_gdal_version():
    """检查GDAL版本信息"""
    print(f"GDAL Version: {gdal.VersionInfo()}")
    print(f"GDAL Release Name: {gdal.VersionInfo('RELEASE_NAME')}")
    print("-" * 50)

def get_supported_drivers():
    """获取所有支持的OGR驱动程序"""
    print("支持的OGR驱动程序（前20个）:")
    driver_count = ogr.GetDriverCount()
    drivers = []
    
    for i in range(min(20, driver_count)):  # 只显示前20个
        driver = ogr.GetDriver(i)
        driver_name = driver.GetName()
        drivers.append(driver_name)
        print(f"{i+1:2d}. {driver_name}")
    
    print(f"\n总共支持 {driver_count} 种驱动程序")
    print("-" * 50)
    return drivers

def test_geometry_types():
    """测试不同的几何图形类型"""
    print("主要的几何图形类型:")
    
    geometry_types = [
        (ogr.wkbPoint, "Point"),
        (ogr.wkbLineString, "LineString"),
        (ogr.wkbPolygon, "Polygon"),
        (ogr.wkbMultiPoint, "MultiPoint"),
    ]
    
    for geom_type, name in geometry_types:
        print(f"  {geom_type:2d}: {name}")
    
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
        geom.AddPoint(116.3974, 39.9093)
        geom.AddPoint(121.4737, 31.2304)  # 上海坐标
        return geom
    
    elif geom_type == ogr.wkbPolygon:
        # 创建一个矩形
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(116.0, 39.5)
        ring.AddPoint(117.0, 39.5)
        ring.AddPoint(117.0, 40.5)
        ring.AddPoint(116.0, 40.5)
        ring.AddPoint(116.0, 39.5)
        
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
        if not driver:
            print("  ✗ 无法获取Memory驱动")
            return False
        
        # 创建数据源
        datasource = driver.CreateDataSource("")
        if not datasource:
            print("  ✗ 无法创建Memory数据源")
            return False
        
        print("  ✓ Memory数据源创建成功")
        
        # 测试不同几何类型
        geometry_types = [
            (ogr.wkbPoint, "Point"),
            (ogr.wkbLineString, "LineString"),
            (ogr.wkbPolygon, "Polygon"),
            (ogr.wkbMultiPoint, "MultiPoint"),
        ]
        
        success_count = 0
        
        for geom_type, geom_name in geometry_types:
            try:
                layer_name = f"layer_{geom_name.lower()}"
                layer = datasource.CreateLayer(layer_name, srs, geom_type)
                
                if layer:
                    # 添加字段
                    field_defn = ogr.FieldDefn("id", ogr.OFTInteger)
                    layer.CreateField(field_defn)
                    
                    field_defn = ogr.FieldDefn("name", ogr.OFTString)
                    field_defn.SetWidth(50)
                    layer.CreateField(field_defn)
                    
                    # 创建要素
                    feature_defn = layer.GetLayerDefn()
                    feature = ogr.Feature(feature_defn)
                    feature.SetField("id", 1)
                    feature.SetField("name", f"Test {geom_name}")
                    
                    # 创建几何体
                    geom = create_test_geometry(geom_type)
                    if geom:
                        feature.SetGeometry(geom)
                    
                    # 添加要素到图层
                    if layer.CreateFeature(feature) == 0:
                        print(f"    ✓ {geom_name} 图层创建成功")
                        success_count += 1
                    else:
                        print(f"    ✗ {geom_name} 要素创建失败")
                    
                    feature = None
                else:
                    print(f"    ✗ {geom_name} 图层创建失败")
            
            except Exception as e:
                print(f"    ✗ {geom_name} 创建异常: {e}")
        
        print(f"  成功创建 {success_count}/4 种图层类型")
        
        # 关闭数据源
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
        ("GeoJSON", "test.geojson"),
        ("GPKG", "test.gpkg"),
        ("ESRI Shapefile", "test.shp"),
    ]
    
    success_drivers = []
    
    for driver_name, filename in test_formats:
        try:
            print(f"  测试 {driver_name}:")
            
            # 获取驱动
            driver = ogr.GetDriverByName(driver_name)
            if not driver:
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
                        for ext in ['.shp', '.shx', '.dbf', '.prj']:
                            related_file = base_name + ext
                            if os.path.exists(related_file):
                                os.remove(related_file)
                    else:
                        os.remove(file_path)
                    print(f"    删除旧文件: {filename}")
                except Exception as e:
                    print(f"    警告: 删除旧文件失败: {e}")
            
            # 创建数据源
            datasource = driver.CreateDataSource(file_path)
            if not datasource:
                print(f"    ✗ 无法创建 {driver_name} 数据源")
                continue
            
            # 创建坐标系统
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            
            # 创建一个点图层进行测试
            layer = datasource.CreateLayer("test_layer", srs, ogr.wkbPoint)
            if not layer:
                print(f"    ✗ 无法创建图层")
                datasource = None
                continue
            
            # 添加字段
            field_defn = ogr.FieldDefn("name", ogr.OFTString)
            layer.CreateField(field_defn)
            
            # 创建要素
            feature_defn = layer.GetLayerDefn()
            feature = ogr.Feature(feature_defn)
            feature.SetField("name", f"Test Point")
            
            # 创建几何体
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(116.3974, 39.9093)
            feature.SetGeometry(point)
            
            # 添加要素
            if layer.CreateFeature(feature) == 0:
                print(f"    ✓ {driver_name} 测试成功")
                success_drivers.append(driver_name)
            else:
                print(f"    ✗ {driver_name} 要素创建失败")
            
            # 关闭
            feature = None
            datasource = None
            
        except Exception as e:
            print(f"    ✗ {driver_name} 测试失败: {e}")
    
    return success_drivers

def main():
    """主函数"""
    print("GDAL图层类型验证程序（简化版）")
    print("=" * 50)
    
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
        
        print("\n" + "=" * 50)
        print("测试结果摘要:")
        print("=" * 50)
        print(f"内存驱动测试: {'✓ 成功' if memory_success else '✗ 失败'}")
        print(f"成功的文件驱动: {', '.join(file_drivers) if file_drivers else '无'}")
        print(f"测试文件保存在: /Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/")
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()