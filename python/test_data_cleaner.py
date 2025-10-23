"""
GDAL测试数据清理模块
提供简化的数据清理功能，可被其他测试脚本导入使用
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

class TestDataCleaner:
    """测试数据清理器（简化版）"""
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """获取文件大小"""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except:
            return 0
    
    @staticmethod
    def delete_files(file_paths: List[Path], description: str = "文件") -> Tuple[int, int]:
        """
        删除文件列表
        返回: (删除数量, 释放的字节数)
        """
        deleted_count = 0
        total_size_freed = 0
        
        for file_path in file_paths:
            try:
                if file_path.exists():
                    size = TestDataCleaner.get_file_size(file_path)
                    file_path.unlink()
                    deleted_count += 1
                    total_size_freed += size
                    print(f"  ✅ 已删除 {description}: {file_path.name}")
            except Exception as e:
                print(f"  ❌ 删除 {description} 失败: {file_path.name} - {e}")
        
        return deleted_count, total_size_freed
    
    @staticmethod
    def delete_directory(dir_path: Path, description: str = "目录") -> Tuple[int, int]:
        """
        删除目录及其内容
        返回: (删除的文件数, 释放的字节数)
        """
        if not dir_path.exists():
            return 0, 0
        
        # 计算总大小
        file_count = 0
        total_size = 0
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += TestDataCleaner.get_file_size(file_path)
        
        try:
            shutil.rmtree(dir_path)
            print(f"  ✅ 已删除 {description}: {dir_path.name}")
            return file_count, total_size
        except Exception as e:
            print(f"  ❌ 删除 {description} 失败: {dir_path.name} - {e}")
            return 0, 0
    
    @staticmethod
    def scan_test_files(base_dir: Path, patterns: List[str]) -> List[Path]:
        """
        扫描测试文件
        patterns: 文件模式列表，如 ['*.shp', '*.gpkg']
        """
        found_files = []
        
        if not base_dir.exists():
            return found_files
        
        for pattern in patterns:
            found_files.extend(base_dir.glob(pattern))
            # 也搜索子目录
            found_files.extend(base_dir.glob(f"**/{pattern}"))
        
        return found_files
    
    @staticmethod
    def offer_simple_cleanup(files_to_clean: List[Path], 
                           description: str = "测试文件",
                           auto_confirm: bool = False) -> bool:
        """
        提供简单的清理选项
        返回: 是否执行了清理
        """
        if not files_to_clean:
            print(f"📁 没有发现需要清理的{description}")
            return False
        
        # 计算总大小
        total_size = sum(TestDataCleaner.get_file_size(f) for f in files_to_clean)
        
        print(f"\n🧹 发现 {len(files_to_clean)} 个{description}")
        print(f"📊 总大小: {TestDataCleaner.format_size(total_size)}")
        
        # 显示前几个文件
        print(f"📄 文件列表 (显示前5个):")
        for i, file_path in enumerate(files_to_clean[:5]):
            size = TestDataCleaner.get_file_size(file_path)
            print(f"  {i+1}. {file_path.name} ({TestDataCleaner.format_size(size)})")
        
        if len(files_to_clean) > 5:
            print(f"  ... 以及其他 {len(files_to_clean) - 5} 个文件")
        
        if auto_confirm:
            print(f"🤖 自动清理模式")
            should_clean = True
        else:
            try:
                choice = input(f"\n是否清理这些{description}? (y/n): ").strip().lower()
                should_clean = choice in ['y', 'yes', '是', '1']
            except KeyboardInterrupt:
                print(f"\n⚠️  操作被取消")
                return False
        
        if should_clean:
            deleted_count, size_freed = TestDataCleaner.delete_files(files_to_clean, description)
            
            print(f"\n📊 清理结果:")
            print(f"  删除文件: {deleted_count} 个")
            print(f"  释放空间: {TestDataCleaner.format_size(size_freed)}")
            
            return deleted_count > 0
        else:
            print(f"⚠️  跳过清理{description}")
            return False

def cleanup_gdal_test_data(base_dir: Optional[Path] = None, 
                          auto_confirm: bool = False,
                          include_reports: bool = False) -> bool:
    """
    清理GDAL测试数据的便捷函数
    
    Args:
        base_dir: 基础目录，默认为当前目录
        auto_confirm: 是否自动确认清理
        include_reports: 是否包含报告文件
    
    Returns:
        是否执行了清理操作
    """
    if base_dir is None:
        base_dir = Path.cwd()
    
    # 数据文件模式
    data_patterns = [
        '*.shp', '*.shx', '*.dbf', '*.prj', '*.cpg',  # Shapefile
        '*.gpkg',                                      # GeoPackage  
        '*.geojson',                                   # GeoJSON
        '*.kml', '*.kmz',                             # KML
        '*.gml',                                      # GML
        '*.tmp', '*.temp'                             # 临时文件
    ]
    
    # 报告文件模式
    report_patterns = ['*.md', '*.txt', '*.log']
    
    patterns = data_patterns
    if include_reports:
        patterns.extend(report_patterns)
    
    # 扫描文件
    test_files = TestDataCleaner.scan_test_files(base_dir, patterns)
    
    # 提供清理选项
    description = "测试数据文件"
    if include_reports:
        description = "测试文件和报告"
    
    return TestDataCleaner.offer_simple_cleanup(
        test_files, 
        description, 
        auto_confirm
    )

def cleanup_test_output_directory(output_dir: Path, 
                                auto_confirm: bool = False) -> bool:
    """
    清理整个测试输出目录
    
    Args:
        output_dir: 输出目录路径
        auto_confirm: 是否自动确认清理
    
    Returns:
        是否执行了清理操作
    """
    if not output_dir.exists():
        print(f"📁 目录不存在: {output_dir}")
        return False
    
    # 计算目录信息
    file_count = 0
    total_size = 0
    
    for file_path in output_dir.rglob('*'):
        if file_path.is_file():
            file_count += 1
            total_size += TestDataCleaner.get_file_size(file_path)
    
    if file_count == 0:
        print(f"📁 目录为空: {output_dir}")
        return False
    
    print(f"\n🧹 发现测试输出目录: {output_dir.name}")
    print(f"📊 包含文件: {file_count} 个")
    print(f"📊 总大小: {TestDataCleaner.format_size(total_size)}")
    
    if auto_confirm:
        print(f"🤖 自动清理模式")
        should_clean = True
    else:
        try:
            choice = input(f"\n⚠️  是否删除整个目录? (y/n): ").strip().lower()
            should_clean = choice in ['y', 'yes', '是', '1']
        except KeyboardInterrupt:
            print(f"\n⚠️  操作被取消")
            return False
    
    if should_clean:
        deleted_count, size_freed = TestDataCleaner.delete_directory(output_dir, "输出目录")
        
        print(f"\n📊 清理结果:")
        print(f"  删除文件: {deleted_count} 个")
        print(f"  释放空间: {TestDataCleaner.format_size(size_freed)}")
        
        return deleted_count > 0
    else:
        print(f"⚠️  跳过清理目录")
        return False

# 便捷函数
def quick_cleanup_current_dir(auto_confirm: bool = False) -> bool:
    """快速清理当前目录的测试数据"""
    return cleanup_gdal_test_data(Path.cwd(), auto_confirm, False)

def full_cleanup_current_dir(auto_confirm: bool = False) -> bool:
    """完全清理当前目录（包括报告）"""
    return cleanup_gdal_test_data(Path.cwd(), auto_confirm, True)