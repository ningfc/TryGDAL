#!/usr/bin/env python3
"""
GDAL调试测试程序
"""

import os
import sys
from osgeo import gdal, ogr, osr

# 明确启用异常处理，避免GDAL 4.0兼容性警告
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def debug_gdal():
    """调试GDAL配置"""
    print("GDAL调试信息:")
    print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
    print(f"GDAL数据目录: {gdal.GetConfigOption('GDAL_DATA')}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查内存驱动
    print(f"\n检查驱动:")
    
    # 不启用异常处理，手动检查错误
    memory_driver = ogr.GetDriverByName("Memory")
    print(f"Memory驱动: {memory_driver}")
    
    if memory_driver:
        print("尝试创建内存数据源...")
        
        # 尝试不同的方式创建数据源
        try:
            ds1 = memory_driver.CreateDataSource("")
            print(f"方式1（空字符串）: {ds1}")
            if ds1:
                ds1 = None  # 清理
        except Exception as e:
            print(f"方式1异常: {e}")
        
        try:
            ds2 = memory_driver.CreateDataSource("memory_test")
            print(f"方式2（命名）: {ds2}")
            if ds2:
                ds2 = None  # 清理
        except Exception as e:
            print(f"方式2异常: {e}")
        
        try:
            ds3 = memory_driver.CreateDataSource("/vsimem/test.mem")
            print(f"方式3（虚拟内存）: {ds3}")
            if ds3:
                ds3 = None  # 清理
        except Exception as e:
            print(f"方式3异常: {e}")
    
    # 检查文件驱动
    print(f"\n检查文件驱动:")
    geojson_driver = ogr.GetDriverByName("GeoJSON")
    print(f"GeoJSON驱动: {geojson_driver}")
    
    if geojson_driver:
        test_file = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/debug_test.geojson"
        print(f"尝试创建文件: {test_file}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        try:
            ds = geojson_driver.CreateDataSource(test_file)
            print(f"GeoJSON数据源: {ds}")
            if ds:
                print("✓ GeoJSON数据源创建成功")
                
                # 尝试创建图层
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(4326)
                
                layer = ds.CreateLayer("test", srs, ogr.wkbPoint)
                print(f"图层: {layer}")
                
                if layer:
                    print("✓ 图层创建成功")
                    
                    # 添加字段
                    field_defn = ogr.FieldDefn("name", ogr.OFTString)
                    result = layer.CreateField(field_defn)
                    print(f"字段创建结果: {result}")
                    
                    # 创建要素
                    feature_defn = layer.GetLayerDefn()
                    feature = ogr.Feature(feature_defn)
                    feature.SetField("name", "test")
                    
                    # 创建几何体
                    point = ogr.Geometry(ogr.wkbPoint)
                    point.AddPoint(0, 0)
                    feature.SetGeometry(point)
                    
                    # 添加要素
                    result = layer.CreateFeature(feature)
                    print(f"要素创建结果: {result}")
                    
                    if result == 0:
                        print("✓ 完整测试成功")
                    else:
                        print("✗ 要素创建失败")
                    
                    feature = None
                else:
                    print("✗ 图层创建失败")
                
                ds = None
            else:
                print("✗ GeoJSON数据源创建失败")
        except Exception as e:
            print(f"GeoJSON异常: {e}")
            import traceback
            traceback.print_exc()

def simple_working_test():
    """最简单的工作测试"""
    print("\n" + "="*50)
    print("最简单的工作测试:")
    
    try:
        # 使用最基本的方法
        driver = ogr.GetDriverByName("Memory")
        if not driver:
            print("✗ 无法获取Memory驱动")
            return
        
        # 直接调用CreateDataSource，不传参数
        print("尝试创建数据源...")
        ds = ogr.Open("")  # 尝试不同的方法
        print(f"Open('')结果: {ds}")
        
        # 尝试用驱动创建
        ds = driver.CreateDataSource("")
        print(f"CreateDataSource('')结果: {ds}")
        
        if ds is None:
            print("尝试不同的参数...")
            ds = driver.CreateDataSource("test")
            print(f"CreateDataSource('test')结果: {ds}")
        
        if ds is None:
            print("尝试虚拟内存文件系统...")
            ds = driver.CreateDataSource("/vsimem/test")
            print(f"CreateDataSource('/vsimem/test')结果: {ds}")
        
        if ds:
            print("✓ 成功创建数据源")
            
            # 尝试创建图层
            layer = ds.CreateLayer("test", None, ogr.wkbPoint)
            if layer:
                print("✓ 成功创建图层")
            else:
                print("✗ 图层创建失败")
        else:
            print("✗ 所有方法都无法创建数据源")
            
            # 获取GDAL错误信息
            error = gdal.GetLastErrorMsg()
            if error:
                print(f"GDAL错误信息: {error}")
    
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_gdal()
    simple_working_test()