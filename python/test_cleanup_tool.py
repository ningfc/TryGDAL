#!/usr/bin/env python3
"""
测试清理工具功能
创建一些测试文件，然后测试清理功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_files():
    """创建一些测试文件用于测试清理功能"""
    print("🔧 创建测试文件...")
    
    test_files = [
        "test_point.shp",
        "test_point.shx", 
        "test_point.dbf",
        "test_point.prj",
        "test_line.gpkg",
        "test_polygon.geojson",
        "performance_report.txt",
        "test_summary.md",
        "temp_data.tmp"
    ]
    
    created_files = []
    
    for filename in test_files:
        file_path = Path(filename)
        try:
            # 创建测试内容
            content = f"Test file: {filename}\nCreated for cleanup testing\n"
            content += "A" * (1024 * (len(created_files) + 1))  # 不同大小的文件
            
            file_path.write_text(content)
            created_files.append(file_path)
            print(f"  ✅ 创建: {filename} ({len(content)} bytes)")
            
        except Exception as e:
            print(f"  ❌ 创建失败: {filename} - {e}")
    
    return created_files

def test_cleanup_functions():
    """测试清理功能"""
    try:
        from test_data_cleaner import (
            TestDataCleaner, 
            quick_cleanup_current_dir, 
            full_cleanup_current_dir,
            cleanup_gdal_test_data
        )
        
        print(f"\n🧪 测试清理功能...")
        
        # 1. 测试文件大小格式化
        print(f"\n📏 测试文件大小格式化:")
        sizes = [512, 1536, 1048576, 1073741824]
        for size in sizes:
            formatted = TestDataCleaner.format_size(size)
            print(f"  {size:>10} bytes = {formatted}")
        
        # 2. 测试文件扫描
        print(f"\n🔍 测试文件扫描:")
        current_dir = Path.cwd()
        data_patterns = ['*.shp', '*.gpkg', '*.geojson', '*.tmp']
        found_files = TestDataCleaner.scan_test_files(current_dir, data_patterns)
        
        print(f"  找到数据文件: {len(found_files)} 个")
        for file_path in found_files:
            size = TestDataCleaner.get_file_size(file_path)
            print(f"    📄 {file_path.name} ({TestDataCleaner.format_size(size)})")
        
        # 3. 测试清理选项（演示模式）
        print(f"\n🧹 演示清理功能 (自动确认模式):")
        
        print(f"\n  测试快速清理（仅数据文件）:")
        result = quick_cleanup_current_dir(auto_confirm=True)
        print(f"  清理结果: {'成功' if result else '无文件清理'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入清理模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试清理功能失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 GDAL测试数据清理工具 - 功能测试")
    print("=" * 50)
    
    try:
        # 1. 创建测试文件
        created_files = create_test_files()
        
        if not created_files:
            print("❌ 没有创建任何测试文件")
            return
        
        print(f"\n✅ 成功创建 {len(created_files)} 个测试文件")
        
        # 2. 测试清理功能
        success = test_cleanup_functions()
        
        if success:
            print(f"\n✅ 清理功能测试完成")
        else:
            print(f"\n❌ 清理功能测试失败")
        
        # 3. 最终清理剩余文件
        print(f"\n🧹 最终清理...")
        remaining_files = []
        for file_path in created_files:
            if file_path.exists():
                remaining_files.append(file_path)
        
        if remaining_files:
            print(f"  发现 {len(remaining_files)} 个剩余文件:")
            for file_path in remaining_files:
                try:
                    file_path.unlink()
                    print(f"    ✅ 已删除: {file_path.name}")
                except Exception as e:
                    print(f"    ❌ 删除失败: {file_path.name} - {e}")
        else:
            print(f"  所有测试文件已清理完成")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()