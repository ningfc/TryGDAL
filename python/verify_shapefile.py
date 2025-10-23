#!/usr/bin/env python3
"""
验证生成的Shapefile文件内容
特别验证多部分面的正确性
"""

import os
from osgeo import gdal, ogr, osr

# 明确启用异常处理
gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

def verify_shapefile_content():
    """验证Shapefile内容"""
    print("验证Shapefile测试文件内容")
    print("=" * 50)
    
    test_dir = "/Users/fangchaoning/Code/gdal/TryGDAL/python/test_output/shapefile_test"
    
    # 要验证的文件
    files_to_verify = [
        ("points.shp", "点文件"),
        ("multipoints.shp", "多点文件"),
        ("lines.shp", "线文件"),
        ("multilines.shp", "多线文件"),
        ("polygons.shp", "多边形文件"),
        ("multipolygons.shp", "多部分面文件"),  # 重点验证
    ]
    
    for filename, description in files_to_verify:
        file_path = os.path.join(test_dir, filename)
        print(f"\n验证 {description} ({filename}):")
        
        if not os.path.exists(file_path):
            print(f"  ✗ 文件不存在: {file_path}")
            continue
        
        try:
            # 打开数据源
            datasource = ogr.Open(file_path, 0)  # 只读模式
            if datasource is None:
                print(f"  ✗ 无法打开文件")
                continue
            
            # 获取图层
            layer = datasource.GetLayer(0)
            if layer is None:
                print(f"  ✗ 无法获取图层")
                continue
            
            # 获取基本信息
            feature_count = layer.GetFeatureCount()
            layer_defn = layer.GetLayerDefn()
            geom_type = layer_defn.GetGeomType()
            geom_name = ogr.GeometryTypeToName(geom_type)
            
            print(f"  要素数量: {feature_count}")
            print(f"  几何类型: {geom_name} (代码: {geom_type})")
            
            # 获取字段信息
            field_count = layer_defn.GetFieldCount()
            print(f"  字段数量: {field_count}")
            for i in range(field_count):
                field_defn = layer_defn.GetFieldDefn(i)
                field_name = field_defn.GetName()
                field_type = field_defn.GetType()
                print(f"    {i+1}. {field_name} ({ogr.GetFieldTypeName(field_type)})")
            
            # 详细验证要素内容
            layer.ResetReading()
            for i, feature in enumerate(layer):
                if i >= 3:  # 只显示前3个要素
                    break
                
                print(f"  要素 {i+1}:")
                
                # 属性信息
                name = feature.GetField("name")
                geom_type_field = feature.GetField("geom_type")
                print(f"    名称: {name}")
                print(f"    类型: {geom_type_field}")
                
                # 几何信息
                geom = feature.GetGeometryRef()
                if geom:
                    print(f"    几何类型: {geom.GetGeometryName()}")
                    
                    # 特别处理多部分面
                    if geom.GetGeometryName() == "MULTIPOLYGON":
                        polygon_count = geom.GetGeometryCount()
                        print(f"    包含多边形数量: {polygon_count}")
                        
                        total_area = geom.GetArea()
                        print(f"    总面积: {total_area:.6f} 平方度")
                        
                        for j in range(polygon_count):
                            sub_polygon = geom.GetGeometryRef(j)
                            if sub_polygon:
                                ring_count = sub_polygon.GetGeometryCount()
                                area = sub_polygon.GetArea()
                                print(f"      多边形 {j+1}: {ring_count} 个环, 面积 {area:.6f}")
                    
                    elif geom.GetGeometryName() == "POLYGON":
                        ring_count = geom.GetGeometryCount()
                        area = geom.GetArea()
                        print(f"    环数量: {ring_count} (外环+洞)")
                        print(f"    面积: {area:.6f} 平方度")
                    
                    elif geom.GetGeometryName() == "MULTIPOINT":
                        point_count = geom.GetGeometryCount()
                        print(f"    包含点数量: {point_count}")
                    
                    elif geom.GetGeometryName() == "MULTILINESTRING":
                        line_count = geom.GetGeometryCount()
                        print(f"    包含线数量: {line_count}")
                        
                        total_length = 0
                        for j in range(line_count):
                            sub_line = geom.GetGeometryRef(j)
                            if sub_line:
                                length = sub_line.Length()
                                total_length += length
                                print(f"      线 {j+1}: 长度 {length:.6f}")
                        print(f"    总长度: {total_length:.6f}")
                else:
                    print(f"    ✗ 无几何数据")
            
            if feature_count > 3:
                print(f"  ... (还有 {feature_count - 3} 个要素)")
            
            # 关闭数据源
            datasource = None
            print(f"  ✓ 验证完成")
            
        except Exception as e:
            print(f"  ✗ 验证失败: {e}")

def demonstrate_multipolygon_use_cases():
    """演示多部分面的实际用例"""
    print("\n" + "=" * 50)
    print("多部分面（MultiPolygon）实际应用案例")
    print("=" * 50)
    
    use_cases = [
        {
            'title': '1. 群岛国家 - 马尔代夫',
            'description': '由1000多个珊瑚岛组成，每个环礁都是独立的多边形',
            'benefit': '一个要素表示整个国家，便于统计和分析'
        },
        {
            'title': '2. 多校区大学 - 北京大学',
            'description': '燕园校区 + 医学部校区，地理上分离但逻辑上统一',
            'benefit': '共享校名、建校时间等属性，查询时作为整体处理'
        },
        {
            'title': '3. 连锁企业 - 星巴克门店',
            'description': '同一城市的所有星巴克门店，每个门店是一个多边形',
            'benefit': '便于计算总营业面积、分析覆盖范围'
        },
        {
            'title': '4. 行政飞地 - 某市辖区',
            'description': '主城区 + 若干飞地，行政管辖统一但地理分离',
            'benefit': '保持行政区划的完整性，统一管理'
        },
        {
            'title': '5. 自然保护区 - 湿地公园',
            'description': '多个独立的湿地区域组成一个保护区系统',
            'benefit': '统一保护政策，整体生态评估'
        }
    ]
    
    for case in use_cases:
        print(f"\n{case['title']}")
        print(f"场景: {case['description']}")
        print(f"优势: {case['benefit']}")
    
    print(f"\n{'='*50}")
    print("技术优势总结:")
    print("✓ 数据完整性: 逻辑上相关的地理区域保持在一个要素中")
    print("✓ 属性共享: 所有子区域共享相同的属性信息")
    print("✓ 查询效率: 空间查询时作为整体处理，性能更好")
    print("✓ 拓扑正确: 维护复杂地理实体的拓扑关系")
    print("✓ 标准兼容: 符合OGC Simple Features标准")

if __name__ == "__main__":
    verify_shapefile_content()
    demonstrate_multipolygon_use_cases()