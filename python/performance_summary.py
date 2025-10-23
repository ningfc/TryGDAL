#!/usr/bin/env python3
"""
性能测试结果可视化
生成简单的文本图表显示性能对比
"""

def create_performance_summary():
    """创建性能测试结果总结"""
    print("Shapefile vs GeoPackage 性能测试结果总结")
    print("=" * 60)
    
    # 测试数据（从实际测试结果中提取）
    point_data = {
        'sizes': [100, 500, 1000, 2000],
        'shp_write': [0.013, 0.053, 0.066, 0.126],
        'gpkg_write': [0.036, 0.038, 0.068, 0.125],
        'shp_read': [0.014, 0.003, 0.005, 0.010],
        'gpkg_read': [0.004, 0.005, 0.007, 0.010],
        'shp_size': [22.9, 112.4, 224.2, 447.8],  # KB
        'gpkg_size': [112.0, 172.0, 236.0, 372.0]  # KB
    }
    
    polygon_data = {
        'sizes': [50, 100, 200, 500],
        'shp_write': [0.005, 0.009, 0.015, 0.036],
        'gpkg_write': [0.011, 0.014, 0.020, 0.041],
        'shp_read': [0.001, 0.001, 0.001, 0.003],
        'gpkg_read': [0.003, 0.003, 0.004, 0.005],
        'shp_size': [17.8, 34.7, 69.5, 172.5],  # KB
        'gpkg_size': [112.0, 136.0, 168.0, 280.0]  # KB
    }
    
    print("\n1. 点数据性能对比")
    print("=" * 40)
    create_comparison_table("点数据", point_data)
    
    print("\n2. 多边形数据性能对比")  
    print("=" * 40)
    create_comparison_table("多边形数据", polygon_data)
    
    print("\n3. 性能趋势分析")
    print("=" * 40)
    analyze_trends(point_data, polygon_data)
    
    print("\n4. 最终建议")
    print("=" * 40)
    print_recommendations()

def create_comparison_table(data_type, data):
    """创建对比表格"""
    print(f"\n{data_type}性能指标:")
    print("-" * 50)
    
    # 表头
    print(f"{'数据量':>8s} | {'写入性能':>12s} | {'读取性能':>12s} | {'文件大小':>12s}")
    print(f"{'':>8s} | {'SHP':>5s} {'GPKG':>5s} | {'SHP':>5s} {'GPKG':>5s} | {'SHP':>5s} {'GPKG':>5s}")
    print("-" * 65)
    
    # 数据行
    for i, size in enumerate(data['sizes']):
        shp_w = data['shp_write'][i]
        gpkg_w = data['gpkg_write'][i]
        shp_r = data['shp_read'][i]
        gpkg_r = data['gpkg_read'][i]
        shp_s = data['shp_size'][i]
        gpkg_s = data['gpkg_size'][i]
        
        print(f"{size:>8d} | {shp_w:>5.3f} {gpkg_w:>5.3f} | {shp_r:>5.3f} {gpkg_r:>5.3f} | {shp_s:>5.1f} {gpkg_s:>5.1f}")
    
    # 计算平均性能比
    write_ratios = [data['shp_write'][i] / data['gpkg_write'][i] for i in range(len(data['sizes']))]
    read_ratios = [data['shp_read'][i] / data['gpkg_read'][i] for i in range(len(data['sizes']))]
    size_ratios = [data['shp_size'][i] / data['gpkg_size'][i] for i in range(len(data['sizes']))]
    
    avg_write = sum(write_ratios) / len(write_ratios)
    avg_read = sum(read_ratios) / len(read_ratios)
    avg_size = sum(size_ratios) / len(size_ratios)
    
    print("-" * 65)
    print(f"平均性能比 (Shapefile/GeoPackage):")
    print(f"  写入: {avg_write:.2f}x {'(SHP更快)' if avg_write < 1 else '(GPKG更快)' if avg_write > 1 else '(相当)'}")
    print(f"  读取: {avg_read:.2f}x {'(SHP更快)' if avg_read < 1 else '(GPKG更快)' if avg_read > 1 else '(相当)'}")
    print(f"  大小: {avg_size:.2f}x {'(SHP更小)' if avg_size < 1 else '(GPKG更小)' if avg_size > 1 else '(相当)'}")

def analyze_trends(point_data, polygon_data):
    """分析性能趋势"""
    
    print("写入性能趋势:")
    print("  点数据:")
    for i, size in enumerate(point_data['sizes']):
        ratio = point_data['shp_write'][i] / point_data['gpkg_write'][i]
        winner = "Shapefile" if ratio < 1 else "GeoPackage" if ratio > 1 else "相当"
        print(f"    {size:>4d} 要素: {winner} ({ratio:.2f}x)")
    
    print("  多边形数据:")
    for i, size in enumerate(polygon_data['sizes']):
        ratio = polygon_data['shp_write'][i] / polygon_data['gpkg_write'][i]
        winner = "Shapefile" if ratio < 1 else "GeoPackage" if ratio > 1 else "相当"
        print(f"    {size:>4d} 要素: {winner} ({ratio:.2f}x)")
    
    print("\n文件大小趋势:")
    print("  Shapefile 在小到中等数据量时文件更小")
    print("  GeoPackage 有固定开销(~100KB)，大数据量时可能更紧凑")
    
    print("\n读取性能趋势:")
    print("  多边形数据: Shapefile 明显更快")
    print("  点数据: 小数据量时 GeoPackage 更快，大数据量时 Shapefile 更快")

def print_recommendations():
    """打印使用建议"""
    
    recommendations = {
        "选择 Shapefile 的场景": [
            "小到中等数据量 (<5000 要素)",
            "多边形为主的空间数据", 
            "注重文件大小和存储效率",
            "需要最大的软件兼容性",
            "简单的数据结构和查询",
            "批量数据处理和分析"
        ],
        "选择 GeoPackage 的场景": [
            "大数据量 (>10000 要素)",
            "复杂的属性查询需求",
            "需要多图层管理",
            "现代Web GIS应用", 
            "需要事务和并发支持",
            "复杂的SQL查询功能"
        ]
    }
    
    for category, items in recommendations.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  ✓ {item}")
    
    print(f"\n性能优化提示:")
    print(f"  • 使用事务批量操作提升写入性能")
    print(f"  • Shapefile注意2GB文件大小限制")
    print(f"  • GeoPackage可以使用VACUUM优化文件大小")
    print(f"  • 根据实际数据量和使用模式选择格式")

def create_simple_chart(title, shp_values, gpkg_values, labels):
    """创建简单的文本柱状图"""
    print(f"\n{title}")
    print("-" * 40)
    
    max_val = max(max(shp_values), max(gpkg_values))
    
    for i, label in enumerate(labels):
        shp_val = shp_values[i]
        gpkg_val = gpkg_values[i]
        
        # 计算柱状图长度（最大20个字符）
        shp_bar_len = int((shp_val / max_val) * 20)
        gpkg_bar_len = int((gpkg_val / max_val) * 20)
        
        shp_bar = "█" * shp_bar_len + " " * (20 - shp_bar_len)
        gpkg_bar = "█" * gpkg_bar_len + " " * (20 - gpkg_bar_len)
        
        print(f"{label:>4s}: SHP |{shp_bar}| {shp_val:.3f}")
        print(f"     GPKG |{gpkg_bar}| {gpkg_val:.3f}")
        print()

if __name__ == "__main__":
    create_performance_summary()