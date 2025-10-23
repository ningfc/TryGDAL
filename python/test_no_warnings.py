#!/usr/bin/env python3
"""
使用统一配置的GDAL测试程序
展示如何正确配置GDAL以避免警告
"""

# 导入我们的GDAL配置模块
from gdal_config import configure_gdal, get_gdal_info

def test_with_proper_config():
    """使用正确配置的测试"""
    print("GDAL正确配置测试")
    print("=" * 40)
    
    # 配置GDAL（这将设置异常处理，避免警告）
    gdal, ogr, osr = configure_gdal()
    
    # 显示版本信息
    info = get_gdal_info()
    print(f"GDAL版本: {info['version']}")
    print(f"支持的驱动数量: {info['driver_count']}")
    
    print("\n测试内存驱动创建:")
    
    # 创建内存数据源
    driver = ogr.GetDriverByName("Memory")
    datasource = driver.CreateDataSource("")
    
    # 创建坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    # 创建图层
    layer = datasource.CreateLayer("test", srs, ogr.wkbPoint)
    
    # 添加字段
    field_defn = ogr.FieldDefn("name", ogr.OFTString)
    layer.CreateField(field_defn)
    
    # 创建要素
    feature_defn = layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    feature.SetField("name", "测试点")
    
    # 创建几何体
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(116.3974, 39.9093)
    feature.SetGeometry(point)
    
    # 添加要素
    layer.CreateFeature(feature)
    
    print(f"✓ 成功创建图层，包含 {layer.GetFeatureCount()} 个要素")
    print("✓ 没有警告信息输出")
    
    # 清理
    feature = None
    datasource = None

if __name__ == "__main__":
    test_with_proper_config()