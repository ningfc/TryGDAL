#!/usr/bin/env python3
"""
简化版本的跨平台测试，用于调试
"""

import os
from pathlib import Path
from osgeo import gdal, ogr, osr

# 启用异常
gdal.UseExceptions()
ogr.UseExceptions() 
osr.UseExceptions()

def test_simple_create():
    """简单测试文件创建"""
    output_dir = Path("/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/debug_cross_platform")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"测试目录: {output_dir}")
    print(f"目录是否存在: {output_dir.exists()}")
    print(f"目录权限: 可写={os.access(output_dir, os.W_OK)}")
    
    # 测试Shapefile
    shp_path = str(output_dir / "test.shp")
    print(f"\n测试Shapefile创建: {shp_path}")
    
    try:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        print(f"Shapefile驱动: {driver}")
        
        # 清理旧文件
        base_name = os.path.splitext(shp_path)[0]
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            related_file = base_name + ext
            if os.path.exists(related_file):
                os.remove(related_file)
                print(f"删除旧文件: {related_file}")
        
        datasource = driver.CreateDataSource(shp_path)
        if datasource:
            print("✅ Shapefile数据源创建成功")
            
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            
            layer = datasource.CreateLayer("test", srs, ogr.wkbLineString)
            if layer:
                print("✅ Shapefile图层创建成功")
                datasource = None
            else:
                print("❌ Shapefile图层创建失败")
        else:
            print("❌ Shapefile数据源创建失败")
            
    except Exception as e:
        print(f"❌ Shapefile测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试GeoPackage
    gpkg_path = str(output_dir / "test.gpkg")
    print(f"\n测试GeoPackage创建: {gpkg_path}")
    
    try:
        if os.path.exists(gpkg_path):
            os.remove(gpkg_path)
            print(f"删除旧文件: {gpkg_path}")
        
        driver = ogr.GetDriverByName("GPKG")
        print(f"GeoPackage驱动: {driver}")
        
        datasource = driver.CreateDataSource(gpkg_path)
        if datasource:
            print("✅ GeoPackage数据源创建成功")
            
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            
            layer = datasource.CreateLayer("test", srs, ogr.wkbLineString)
            if layer:
                print("✅ GeoPackage图层创建成功")
                datasource = None
            else:
                print("❌ GeoPackage图层创建失败")
        else:
            print("❌ GeoPackage数据源创建失败")
            
    except Exception as e:
        print(f"❌ GeoPackage测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 检查创建的文件
    print(f"\n文件检查:")
    for file_path in [shp_path, gpkg_path]:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} - 大小: {size} bytes")
        else:
            print(f"❌ {file_path} - 不存在")

if __name__ == "__main__":
    test_simple_create()