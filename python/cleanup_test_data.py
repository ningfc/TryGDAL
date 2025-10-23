#!/usr/bin/env python3
"""
GDAL测试数据清理工具
用于清理所有测试生成的数据文件
"""

import os
import sys
import shutil
from pathlib import Path
import glob

class GDALTestDataCleaner:
    """GDAL测试数据清理器"""
    
    def __init__(self):
        self.base_dir = Path("/Users/fangchaoning/Code/gdal/TryGDAL/python")
        self.test_output_dir = self.base_dir / "test_output"
        
        # 支持的测试文件扩展名
        self.data_extensions = [
            '.shp', '.shx', '.dbf', '.prj', '.cpg',  # Shapefile
            '.gpkg',                                  # GeoPackage
            '.geojson',                              # GeoJSON
            '.kml', '.kmz',                          # KML
            '.gml',                                  # GML
            '.tmp', '.temp'                          # 临时文件
        ]
        
        # 报告文件扩展名
        self.report_extensions = ['.md', '.txt', '.log']
    
    def scan_test_data(self):
        """扫描所有测试数据"""
        print("GDAL测试数据清理工具")
        print("=" * 50)
        
        if not self.test_output_dir.exists():
            print(f"📁 测试输出目录不存在: {self.test_output_dir}")
            return
        
        # 扫描所有测试子目录
        test_dirs = {}
        total_data_size = 0
        total_report_size = 0
        
        for item in self.test_output_dir.iterdir():
            if item.is_dir():
                data_files, report_files, data_size, report_size = self.scan_directory(item)
                if data_files or report_files:
                    test_dirs[item.name] = {
                        'path': item,
                        'data_files': data_files,
                        'report_files': report_files,
                        'data_size': data_size,
                        'report_size': report_size
                    }
                    total_data_size += data_size
                    total_report_size += report_size
        
        # 扫描根目录的零散文件
        root_data, root_reports, root_data_size, root_report_size = self.scan_directory(self.test_output_dir)
        if root_data or root_reports:
            test_dirs['根目录文件'] = {
                'path': self.test_output_dir,
                'data_files': root_data,
                'report_files': root_reports,
                'data_size': root_data_size,
                'report_size': root_report_size
            }
            total_data_size += root_data_size
            total_report_size += root_report_size
        
        if not test_dirs:
            print("📁 没有发现测试数据，目录很干净！")
            return
        
        self.display_summary(test_dirs, total_data_size, total_report_size)
        self.offer_cleanup_options(test_dirs)
    
    def scan_directory(self, directory):
        """扫描单个目录"""
        data_files = []
        report_files = []
        data_size = 0
        report_size = 0
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    
                    if any(file_path.suffix.lower() == ext for ext in self.data_extensions):
                        data_files.append(file_path)
                        data_size += size
                    elif any(file_path.suffix.lower() == ext for ext in self.report_extensions):
                        report_files.append(file_path)
                        report_size += size
        except PermissionError:
            pass
        
        return data_files, report_files, data_size, report_size
    
    def display_summary(self, test_dirs, total_data_size, total_report_size):
        """显示扫描结果摘要"""
        print(f"📊 测试数据扫描结果:")
        print(f"  测试目录数量: {len(test_dirs)} 个")
        print(f"  数据文件总大小: {self.format_size(total_data_size)}")
        print(f"  报告文件总大小: {self.format_size(total_report_size)}")
        print(f"  总占用空间: {self.format_size(total_data_size + total_report_size)}")
        
        print(f"\n📁 详细目录信息:")
        for dir_name, info in test_dirs.items():
            data_count = len(info['data_files'])
            report_count = len(info['report_files'])
            total_size = info['data_size'] + info['report_size']
            
            print(f"  📂 {dir_name}:")
            print(f"    数据文件: {data_count} 个 ({self.format_size(info['data_size'])})")
            print(f"    报告文件: {report_count} 个 ({self.format_size(info['report_size'])})")
            print(f"    小计: {self.format_size(total_size)}")
        
        # 显示最大的几个文件
        all_files = []
        for info in test_dirs.values():
            all_files.extend([(f, f.stat().st_size, 'data') for f in info['data_files']])
            all_files.extend([(f, f.stat().st_size, 'report') for f in info['report_files']])
        
        if all_files:
            all_files.sort(key=lambda x: x[1], reverse=True)
            print(f"\n📈 最大的文件 (前5个):")
            for file_path, size, file_type in all_files[:5]:
                type_icon = "📄" if file_type == 'report' else "📊"
                print(f"    {type_icon} {file_path.name:30} {self.format_size(size):>10}")
    
    def offer_cleanup_options(self, test_dirs):
        """提供清理选项"""
        print(f"\n🧹 清理选项:")
        print(f"  1. 仅清理数据文件 (保留报告)")
        print(f"  2. 仅清理报告文件 (保留数据)")  
        print(f"  3. 清理所有文件")
        print(f"  4. 选择性清理目录")
        print(f"  5. 清理整个test_output目录")
        print(f"  0. 不清理，退出")
        
        try:
            choice = input(f"\n请选择清理选项 [0-5]: ").strip()
            
            if choice == '0':
                print("✅ 未进行任何清理操作")
                return
            elif choice == '1':
                self.cleanup_data_files(test_dirs)
            elif choice == '2':
                self.cleanup_report_files(test_dirs)
            elif choice == '3':
                self.cleanup_all_files(test_dirs)
            elif choice == '4':
                self.selective_cleanup(test_dirs)
            elif choice == '5':
                self.cleanup_entire_output_directory()
            else:
                print("⚠️  无效选择")
                
        except KeyboardInterrupt:
            print("\n⚠️  操作被取消")
    
    def cleanup_data_files(self, test_dirs):
        """清理数据文件，保留报告"""
        print(f"\n🧹 清理数据文件 (保留报告)...")
        
        total_deleted = 0
        total_size_freed = 0
        
        for dir_name, info in test_dirs.items():
            if info['data_files']:
                print(f"\n  📂 处理目录: {dir_name}")
                deleted, size_freed = self.delete_files(info['data_files'])
                total_deleted += deleted
                total_size_freed += size_freed
        
        self.print_cleanup_result(total_deleted, total_size_freed, "数据文件")
    
    def cleanup_report_files(self, test_dirs):
        """清理报告文件，保留数据"""
        print(f"\n🧹 清理报告文件 (保留数据)...")
        
        total_deleted = 0
        total_size_freed = 0
        
        for dir_name, info in test_dirs.items():
            if info['report_files']:
                print(f"\n  📂 处理目录: {dir_name}")
                deleted, size_freed = self.delete_files(info['report_files'])
                total_deleted += deleted
                total_size_freed += size_freed
        
        self.print_cleanup_result(total_deleted, total_size_freed, "报告文件")
    
    def cleanup_all_files(self, test_dirs):
        """清理所有文件"""
        print(f"\n🧹 清理所有文件...")
        
        total_deleted = 0
        total_size_freed = 0
        
        for dir_name, info in test_dirs.items():
            all_files = info['data_files'] + info['report_files']
            if all_files:
                print(f"\n  📂 处理目录: {dir_name}")
                deleted, size_freed = self.delete_files(all_files)
                total_deleted += deleted
                total_size_freed += size_freed
                
                # 如果目录为空，删除目录
                if info['path'] != self.test_output_dir:
                    try:
                        if not any(info['path'].iterdir()):
                            info['path'].rmdir()
                            print(f"    ✅ 已删除空目录: {info['path'].name}")
                    except OSError:
                        pass
        
        self.print_cleanup_result(total_deleted, total_size_freed, "所有文件")
    
    def selective_cleanup(self, test_dirs):
        """选择性清理"""
        print(f"\n🎯 选择性清理:")
        
        for i, (dir_name, info) in enumerate(test_dirs.items(), 1):
            data_count = len(info['data_files'])
            report_count = len(info['report_files'])
            total_size = info['data_size'] + info['report_size']
            
            print(f"  {i}. {dir_name}")
            print(f"     数据文件: {data_count} 个, 报告文件: {report_count} 个")
            print(f"     总大小: {self.format_size(total_size)}")
        
        try:
            choices = input(f"\n请选择要清理的目录 (用逗号分隔，如: 1,3,5): ").strip()
            
            if not choices:
                print("未选择任何目录")
                return
            
            selected_indices = [int(x.strip()) for x in choices.split(',')]
            dir_list = list(test_dirs.items())
            
            total_deleted = 0
            total_size_freed = 0
            
            for index in selected_indices:
                if 1 <= index <= len(dir_list):
                    dir_name, info = dir_list[index - 1]
                    print(f"\n  🧹 清理目录: {dir_name}")
                    
                    all_files = info['data_files'] + info['report_files']
                    deleted, size_freed = self.delete_files(all_files)
                    total_deleted += deleted
                    total_size_freed += size_freed
                    
                    # 删除空目录
                    if info['path'] != self.test_output_dir:
                        try:
                            if not any(info['path'].iterdir()):
                                info['path'].rmdir()
                                print(f"    ✅ 已删除空目录: {info['path'].name}")
                        except OSError:
                            pass
            
            self.print_cleanup_result(total_deleted, total_size_freed, "选定目录")
            
        except (ValueError, IndexError):
            print("⚠️  无效的选择")
    
    def cleanup_entire_output_directory(self):
        """清理整个输出目录"""
        print(f"\n⚠️  警告: 这将删除整个test_output目录!")
        print(f"📁 目录路径: {self.test_output_dir}")
        
        try:
            confirm = input(f"确认删除? 输入 'DELETE' 确认: ").strip()
            
            if confirm == 'DELETE':
                if self.test_output_dir.exists():
                    # 计算目录大小
                    total_size = sum(f.stat().st_size for f in self.test_output_dir.rglob('*') if f.is_file())
                    file_count = len(list(self.test_output_dir.rglob('*')))
                    
                    shutil.rmtree(self.test_output_dir)
                    
                    print(f"  ✅ 已删除整个目录: {self.test_output_dir}")
                    print(f"  📊 清理统计:")
                    print(f"    删除项目: {file_count} 个")
                    print(f"    释放空间: {self.format_size(total_size)}")
                else:
                    print("  📁 目录不存在")
            else:
                print("  ⚠️  操作已取消")
                
        except Exception as e:
            print(f"  ❌ 删除失败: {e}")
    
    def delete_files(self, file_list):
        """删除文件列表"""
        deleted_count = 0
        total_size = 0
        
        for file_path in file_list:
            try:
                size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                total_size += size
                print(f"    ✅ 已删除: {file_path.name}")
            except Exception as e:
                print(f"    ❌ 删除失败: {file_path.name} - {e}")
        
        return deleted_count, total_size
    
    def print_cleanup_result(self, deleted_count, size_freed, description):
        """打印清理结果"""
        print(f"\n📊 清理结果 ({description}):")
        print(f"  删除文件数量: {deleted_count} 个")
        print(f"  释放磁盘空间: {self.format_size(size_freed)}")
        
        if deleted_count > 0:
            print(f"  ✅ 清理完成")
        else:
            print(f"  ⚠️  没有文件被删除")
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def main():
    """主函数"""
    cleaner = GDALTestDataCleaner()
    
    try:
        cleaner.scan_test_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()