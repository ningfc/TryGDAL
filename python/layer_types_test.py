#!/usr/bin/env python3
"""
GDAL图层类型测试程序
验证GDAL中可以创建的不同图层类型
"""

import os
import sys
from osgeo import gdal, ogr, osr

def check_gdal_version():
    """检查GDAL版本信息"""
    print(f"GDAL Version: {gdal.VersionInfo()}")
    print(f"GDAL Release Name: {gdal.VersionInfo('RELEASE_NAME')}")
    print("-" * 50)

def get_supported_drivers():
    """获取所有支持的OGR驱动程序"""
    print("支持的OGR驱动程序:")
    driver_count = ogr.GetDriverCount()
    drivers = []
    
    for i in range(driver_count):
        driver = ogr.GetDriver(i)
        driver_name = driver.GetName()
        drivers.append(driver_name)
        print(f"{i+1:2d}. {driver_name}")
    
    print(f"\n总共支持 {driver_count} 种驱动程序")
    print("-" * 50)
    return drivers

def test_geometry_types():
    """测试不同的几何图形类型"""
    print("GDAL/OGR支持的几何图形类型:")
    
    # 获取所有几何类型
    geometry_types = [
        (ogr.wkbPoint, "Point"),
        (ogr.wkbLineString, "LineString"),
        (ogr.wkbPolygon, "Polygon"),
        (ogr.wkbMultiPoint, "MultiPoint"),
        (ogr.wkbMultiLineString, "MultiLineString"),
        (ogr.wkbMultiPolygon, "MultiPolygon"),
        (ogr.wkbGeometryCollection, "GeometryCollection"),
        (ogr.wkbNone, "None"),
        (ogr.wkbUnknown, "Unknown"),
    ]
    
    # 如果支持3D几何类型
    if hasattr(ogr, 'wkbPoint25D'):
        geometry_types.extend([
            (ogr.wkbPoint25D, "Point25D"),
            (ogr.wkbLineString25D, "LineString25D"),
            (ogr.wkbPolygon25D, "Polygon25D"),
            (ogr.wkbMultiPoint25D, "MultiPoint25D"),
            (ogr.wkbMultiLineString25D, "MultiLineString25D"),
            (ogr.wkbMultiPolygon25D, "MultiPolygon25D"),
            (ogr.wkbGeometryCollection25D, "GeometryCollection25D"),
        ])
    
    for geom_type, name in geometry_types:
        print(f"  {geom_type:2d}: {name}")
    
    print("-" * 50)
    return geometry_types

def create_test_layers():
    """创建不同类型的测试图层"""
    output_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("创建测试图层:")
    
    # 测试不同的输出格式
    test_formats = [
        ("ESRI Shapefile", "test_layers.shp"),
        ("GeoJSON", "test_layers.geojson"),
        ("GPKG", "test_layers.gpkg"),
        ("Memory", ""),  # 内存格式
    ]
    
    geometry_types = [
        (ogr.wkbPoint, "Point"),
        (ogr.wkbLineString, "LineString"),
        (ogr.wkbPolygon, "Polygon"),
        (ogr.wkbMultiPoint, "MultiPoint"),
    ]
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    
    results = {}
    
    for driver_name, filename in test_formats:
        print(f"\n测试驱动: {driver_name}")
        
        try:
            # 获取驱动
            driver = ogr.GetDriverByName(driver_name)
            if not driver:
                print(f"  错误: 无法获取驱动 {driver_name}")
                continue
            
            # 创建数据源
            if driver_name == "Memory":
                datasource = driver.CreateDataSource("")
            else:
                file_path = os.path.join(output_dir, filename)
                # 如果文件存在，先删除
                if os.path.exists(file_path):
                    driver.DeleteDataSource(file_path)
                datasource = driver.CreateDataSource(file_path)
            
            if not datasource:
                print(f"  错误: 无法创建数据源")
                continue
            
            results[driver_name] = {}
            
            # 为每种几何类型创建图层
            for geom_type, geom_name in geometry_types:
                layer_name = f"layer_{geom_name.lower()}"
                
                try:
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
                            results[driver_name][geom_name] = "成功"
                            print(f"  ✓ {geom_name} 图层创建成功")
                        else:
                            results[driver_name][geom_name] = "创建要素失败"
                            print(f"  ✗ {geom_name} 图层创建要素失败")
                        
                        feature = None
                    else:
                        results[driver_name][geom_name] = "创建图层失败"
                        print(f"  ✗ {geom_name} 图层创建失败")
                
                except Exception as e:
                    results[driver_name][geom_name] = f"异常: {str(e)}"
                    print(f"  ✗ {geom_name} 图层创建异常: {e}")
            
            # 关闭数据源
            datasource = None
            
        except Exception as e:
            print(f"  错误: 驱动 {driver_name} 测试失败: {e}")
            results[driver_name] = {"error": str(e)}
    
    return results

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

def print_summary(results):
    """打印测试结果摘要"""
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print("=" * 60)
    
    for driver_name, driver_results in results.items():
        print(f"\n{driver_name}:")
        if "error" in driver_results:
            print(f"  驱动错误: {driver_results['error']}")
        else:
            for geom_name, status in driver_results.items():
                print(f"  {geom_name:15s}: {status}")

def main():
    """主函数"""
    print("GDAL图层类型验证程序")
    print("=" * 50)
    
    try:
        # 检查GDAL版本
        check_gdal_version()
        
        # 获取支持的驱动程序
        drivers = get_supported_drivers()
        
        # 测试几何类型
        geometry_types = test_geometry_types()
        
        # 创建测试图层
        results = create_test_layers()
        
        # 打印结果摘要
        print_summary(results)
        
        print(f"\n测试完成！输出文件保存在: /Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/")
        
    except ImportError as e:
        print(f"错误: 无法导入GDAL模块")
        print(f"请确保已安装GDAL Python绑定")
        print(f"可以使用以下命令安装:")
        print(f"  conda install -c conda-forge gdal")
        print(f"  或")
        print(f"  pip install gdal")
        sys.exit(1)
    
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)

def offer_cleanup():
    """提供数据清理选项"""
    try:
        from test_data_cleaner import quick_cleanup_current_dir
        
        print(f"\n{'='*50}")
        print(f"🧹 测试完成！是否清理生成的测试数据？")
        
        choice = input(f"清理测试数据文件? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '是', '1']:
            quick_cleanup_current_dir(auto_confirm=True)
        else:
            print(f"⚠️  保留测试数据文件")
    except ImportError:
        print(f"⚠️  清理模块未找到，请手动清理测试数据")
    except KeyboardInterrupt:
        print(f"\n⚠️  清理操作被取消")

if __name__ == "__main__":
    main()
    offer_cleanup()