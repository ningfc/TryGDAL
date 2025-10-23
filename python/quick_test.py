#!/usr/bin/env python3
"""
GDAL快速验证脚本
检查GDAL是否正确安装并能够创建基本图层
"""

def quick_test():
    """快速测试GDAL功能"""
    try:
        from osgeo import gdal, ogr, osr
        
        # 明确启用异常处理，避免GDAL 4.0兼容性警告
        gdal.UseExceptions()
        ogr.UseExceptions()
        osr.UseExceptions()
        
        print("✓ GDAL导入成功")
        
        # 检查版本
        print(f"GDAL版本: {gdal.VersionInfo('RELEASE_NAME')}")
        
        # 测试创建内存数据源
        driver = ogr.GetDriverByName("Memory")
        datasource = driver.CreateDataSource("")
        
        # 创建坐标系
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        
        # 创建图层
        layer = datasource.CreateLayer("test", srs, ogr.wkbPoint)
        print("✓ 内存图层创建成功")
        
        # 添加字段
        field_defn = ogr.FieldDefn("name", ogr.OFTString)
        layer.CreateField(field_defn)
        print("✓ 字段添加成功")
        
        # 创建要素
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        feature.SetField("name", "test point")
        
        # 创建几何体
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(116.3974, 39.9093)
        feature.SetGeometry(point)
        
        # 添加要素
        layer.CreateFeature(feature)
        print("✓ 要素创建成功")
        
        print(f"图层中的要素数量: {layer.GetFeatureCount()}")
        print("\n✓ GDAL基本功能测试通过！")
        
        return True
        
    except ImportError as e:
        print("✗ GDAL导入失败")
        print("请安装GDAL: conda install -c conda-forge gdal")
        return False
    
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("GDAL快速验证测试")
    print("-" * 30)
    success = quick_test()
    
    if success:
        print("\n可以运行完整测试: python layer_types_test.py")
    else:
        print("\n请先解决GDAL安装问题")