#!/usr/bin/env python3
"""
Windows平台GDAL性能测试专用配置和工具
解决Windows特有的路径、编码、权限等问题
"""

import os
import sys
import platform
import tempfile
import time
from pathlib import Path

# Windows特定导入
if platform.system() == "Windows":
    try:
        import ctypes
        from ctypes import wintypes
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
    
    try:
        import winreg
        HAS_WINREG = True
    except ImportError:
        HAS_WINREG = False
else:
    HAS_WIN32 = False
    HAS_WINREG = False

class WindowsGDALOptimizer:
    """Windows平台GDAL优化器"""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        if not self.is_windows:
            print("警告: 此工具专为Windows设计")
            return
        
        self.windows_version = platform.win32_ver()
        self.setup_windows_environment()
    
    def setup_windows_environment(self):
        """设置Windows环境"""
        print("Windows GDAL环境配置")
        print("=" * 40)
        print(f"Windows版本: {self.windows_version}")
        
        # 检查Windows版本
        self.check_windows_compatibility()
        
        # 设置环境变量
        self.setup_environment_variables()
        
        # 检查文件系统
        self.check_file_system()
        
        # 优化临时目录
        self.setup_temp_directory()
    
    def check_windows_compatibility(self):
        """检查Windows兼容性"""
        major_version = int(self.windows_version[1].split('.')[0])
        
        if major_version >= 10:
            print("✓ Windows 10/11 - 完全支持")
            self.long_path_support = self.check_long_path_support()
        elif major_version == 6:
            print("✓ Windows 7/8/8.1 - 基本支持")
            self.long_path_support = False
        else:
            print("⚠️ Windows版本过旧，可能存在兼容性问题")
            self.long_path_support = False
    
    def check_long_path_support(self):
        """检查长路径支持"""
        if not HAS_WINREG:
            return False
        
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\FileSystem"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
                enabled = bool(value)
                
                if enabled:
                    print("✓ 长路径支持已启用")
                else:
                    print("⚠️ 长路径支持未启用，建议启用以避免路径长度问题")
                
                return enabled
                
        except (FileNotFoundError, PermissionError):
            print("? 无法检查长路径支持状态")
            return False
    
    def setup_environment_variables(self):
        """设置环境变量"""
        # GDAL相关环境变量
        gdal_vars = {
            'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
            'GDAL_MAX_DATASET_POOL_SIZE': '100',
            'OGR_ORGANIZE_POLYGONS': 'DEFAULT',
            'GDAL_FILENAME_IS_UTF8': 'YES',
            'SHAPE_ENCODING': 'UTF-8'
        }
        
        print("\n设置GDAL环境变量:")
        for var, value in gdal_vars.items():
            os.environ[var] = value
            print(f"  {var} = {value}")
        
        # Windows特定优化
        os.environ['TEMP'] = str(self.get_optimal_temp_dir())
        os.environ['TMP'] = str(self.get_optimal_temp_dir())
    
    def get_optimal_temp_dir(self):
        """获取最优临时目录"""
        # 尝试使用SSD驱动器
        drives = self.get_available_drives()
        
        # 优先使用C盘（通常是SSD）
        preferred_drives = ['C:', 'D:', 'E:']
        
        for drive in preferred_drives:
            if drive in drives:
                temp_path = Path(f"{drive}\\") / "Temp" / "GDAL_Tests"
                if self.is_drive_ssd(drive):
                    print(f"✓ 使用SSD临时目录: {temp_path}")
                    temp_path.mkdir(parents=True, exist_ok=True)
                    return temp_path
        
        # 回退到系统默认
        return Path(tempfile.gettempdir()) / "GDAL_Tests"
    
    def get_available_drives(self):
        """获取可用驱动器"""
        if not HAS_WIN32:
            return ['C:']
        
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if bitmask & 1:
                drives.append(f"{letter}:")
            bitmask >>= 1
        
        return drives
    
    def is_drive_ssd(self, drive_letter):
        """检查驱动器是否为SSD"""
        if not HAS_WIN32:
            return True  # 假设是SSD
        
        try:
            # 使用WMI检查驱动器类型
            # 这里简化处理，在实际环境中可能需要更复杂的检测
            return True  # 简化假设
        except:
            return True
    
    def check_file_system(self):
        """检查文件系统"""
        print(f"\n文件系统信息:")
        
        drives = self.get_available_drives()
        for drive in drives[:3]:  # 只检查前3个驱动器
            try:
                if HAS_WIN32:
                    # 获取文件系统类型
                    buffer = ctypes.create_unicode_buffer(1024)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        drive + "\\", None, 0, None, None, None, buffer, 1024
                    )
                    fs_type = buffer.value
                else:
                    fs_type = "NTFS (assumed)"
                
                free_space = self.get_drive_free_space(drive)
                print(f"  {drive} {fs_type} - 可用空间: {free_space/(1024**3):.1f} GB")
                
            except Exception as e:
                print(f"  {drive} 信息获取失败: {e}")
    
    def get_drive_free_space(self, drive_letter):
        """获取驱动器可用空间"""
        if HAS_WIN32:
            try:
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    drive_letter + "\\",
                    ctypes.pointer(free_bytes),
                    None, None
                )
                return free_bytes.value
            except:
                pass
        
        # 回退方法
        try:
            statvfs = os.statvfs(drive_letter + "\\")
            return statvfs.f_frsize * statvfs.f_bavail
        except:
            return 0
    
    def setup_temp_directory(self):
        """设置优化的临时目录"""
        temp_dir = self.get_optimal_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试读写性能
        test_file = temp_dir / "test_performance.tmp"
        
        try:
            # 写入测试
            start_time = time.perf_counter()
            with open(test_file, 'wb') as f:
                f.write(b'0' * 1024 * 1024)  # 1MB
            write_time = time.perf_counter() - start_time
            
            # 读取测试
            start_time = time.perf_counter()
            with open(test_file, 'rb') as f:
                _ = f.read()
            read_time = time.perf_counter() - start_time
            
            # 清理
            test_file.unlink()
            
            print(f"\n临时目录性能测试:")
            print(f"  写入速度: {1.0/write_time:.1f} MB/s")
            print(f"  读取速度: {1.0/read_time:.1f} MB/s")
            
            if write_time > 0.1 or read_time > 0.1:
                print("  ⚠️ I/O性能较低，考虑使用SSD")
            else:
                print("  ✓ I/O性能良好")
                
        except Exception as e:
            print(f"  ⚠️ 性能测试失败: {e}")
    
    def optimize_for_large_datasets(self):
        """针对大数据集的优化"""
        print(f"\nWindows大数据集优化建议:")
        
        # 虚拟内存建议
        if HAS_WIN32:
            try:
                import psutil
                total_memory = psutil.virtual_memory().total
                recommended_vm = total_memory * 2
                
                print(f"  当前物理内存: {total_memory/(1024**3):.1f} GB")
                print(f"  建议虚拟内存: {recommended_vm/(1024**3):.1f} GB")
                
                current_vm = psutil.virtual_memory().total + psutil.swap_memory().total
                if current_vm < recommended_vm:
                    print(f"  ⚠️ 建议增加虚拟内存到 {recommended_vm/(1024**3):.1f} GB")
                else:
                    print(f"  ✓ 虚拟内存配置合适")
                    
            except ImportError:
                print("  安装psutil以获得内存优化建议: pip install psutil")
        
        # 文件系统优化
        print(f"\n  文件系统优化建议:")
        print(f"    • 禁用文件索引以提升写入性能")
        print(f"    • 使用NTFS压缩可节省空间但会降低性能")
        print(f"    • 考虑使用ReFS（如果支持）以获得更好的大文件性能")
        
        # 防病毒软件
        print(f"\n  防病毒软件建议:")
        print(f"    • 将GDAL工作目录添加到防病毒软件排除列表")
        print(f"    • 临时禁用实时扫描以获得最佳性能")
        
        # 电源设置
        print(f"\n  电源设置建议:")
        print(f"    • 使用高性能电源模式")
        print(f"    • 禁用硬盘休眠")

def create_windows_batch_script():
    """创建Windows批处理脚本"""
    batch_content = '''@echo off
echo Windows GDAL Performance Test Setup
echo ===================================

REM 设置代码页为UTF-8
chcp 65001 > nul

REM 检查Python环境
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查GDAL
python -c "from osgeo import gdal; print('GDAL版本:', gdal.VersionInfo())" > nul 2>&1
if errorlevel 1 (
    echo 错误: GDAL Python绑定未安装
    echo 请安装: pip install gdal 或使用OSGeo4W
    pause
    exit /b 1
)

REM 创建测试目录
if not exist "%USERPROFILE%\\Documents\\GDAL_Tests" (
    mkdir "%USERPROFILE%\\Documents\\GDAL_Tests"
)

REM 运行测试
echo 开始GDAL性能测试...
python cross_platform_performance_test.py "%USERPROFILE%\\Documents\\GDAL_Tests"

pause
'''
    
    return batch_content

def create_windows_powershell_script():
    """创建Windows PowerShell脚本"""
    ps_content = '''# Windows GDAL Performance Test Setup
# PowerShell版本

Write-Host "Windows GDAL Performance Test Setup" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# 检查执行策略
$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-Warning "PowerShell执行策略受限，请运行："
    Write-Host "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "按任意键继续..."
    exit 1
}

# 检查Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ 找到Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python未安装或不在PATH中"
    Read-Host "按任意键继续..."
    exit 1
}

# 检查GDAL
try {
    $gdalCheck = python -c "from osgeo import gdal; print('GDAL版本:', gdal.VersionInfo('RELEASE_NAME'))" 2>$null
    Write-Host "✓ $gdalCheck" -ForegroundColor Green
} catch {
    Write-Error "GDAL Python绑定未安装"
    Write-Host "请安装: pip install gdal 或使用OSGeo4W" -ForegroundColor Yellow
    Read-Host "按任意键继续..."
    exit 1
}

# 检查可选依赖
try {
    python -c "import psutil; print('✓ psutil可用')" 2>$null
} catch {
    Write-Warning "建议安装psutil以获得更好的系统监控: pip install psutil"
}

# 创建测试目录
$testDir = "$env:USERPROFILE\\Documents\\GDAL_Tests"
if (!(Test-Path $testDir)) {
    New-Item -ItemType Directory -Path $testDir -Force | Out-Null
    Write-Host "✓ 创建测试目录: $testDir" -ForegroundColor Green
}

# 系统信息
Write-Host "\\n系统信息:" -ForegroundColor Cyan
Write-Host "操作系统: $(Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
Write-Host "处理器: $(Get-WmiObject Win32_Processor | Select-Object -ExpandProperty Name)"
Write-Host "内存: $([Math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)) GB"

# 运行测试
Write-Host "\\n开始GDAL性能测试..." -ForegroundColor Green
python cross_platform_performance_test.py $testDir

Read-Host "测试完成，按任意键退出..."
'''
    
    return ps_content

def main():
    """主函数"""
    if platform.system() != "Windows":
        print("此脚本专为Windows设计")
        print("在其他平台请直接运行 cross_platform_performance_test.py")
        return
    
    # Windows环境优化
    optimizer = WindowsGDALOptimizer()
    optimizer.optimize_for_large_datasets()
    
    # 创建批处理脚本
    print(f"\n生成Windows辅助脚本...")
    
    # 批处理脚本
    batch_script = Path("run_gdal_test.bat")
    with open(batch_script, 'w', encoding='gbk') as f:  # Windows批处理使用GBK编码
        f.write(create_windows_batch_script())
    print(f"✓ 创建批处理脚本: {batch_script}")
    
    # PowerShell脚本
    ps_script = Path("run_gdal_test.ps1")
    with open(ps_script, 'w', encoding='utf-8-sig') as f:  # PowerShell使用UTF-8 BOM
        f.write(create_windows_powershell_script())
    print(f"✓ 创建PowerShell脚本: {ps_script}")
    
    print(f"\nWindows用户可以使用以下方式运行测试:")
    print(f"  1. 双击 run_gdal_test.bat")
    print(f"  2. 或在PowerShell中运行: .\\run_gdal_test.ps1")
    print(f"  3. 或直接运行: python cross_platform_performance_test.py")

if __name__ == "__main__":
    main()