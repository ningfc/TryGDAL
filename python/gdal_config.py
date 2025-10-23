#!/usr/bin/env python3
"""
GDAL配置模块
统一管理GDAL相关的配置和初始化设置
"""

def configure_gdal():
    """配置GDAL环境，设置异常处理等"""
    try:
        from osgeo import gdal, ogr, osr
        
        # 明确启用异常处理，避免GDAL 4.0兼容性警告
        gdal.UseExceptions()
        ogr.UseExceptions() 
        osr.UseExceptions()
        
        # 可以在这里添加其他GDAL配置
        # 例如：设置GDAL数据路径、缓存大小等
        
        return gdal, ogr, osr
        
    except ImportError as e:
        print(f"错误: 无法导入GDAL模块 - {e}")
        print("请确保已安装GDAL Python绑定:")
        print("  conda install -c conda-forge gdal")
        print("  或")
        print("  pip install gdal")
        raise

def get_gdal_info():
    """获取GDAL版本和配置信息"""
    gdal, ogr, osr = configure_gdal()
    
    info = {
        'version': gdal.VersionInfo('RELEASE_NAME'),
        'version_num': gdal.VersionInfo(),
        'data_dir': gdal.GetConfigOption('GDAL_DATA'),
        'driver_count': ogr.GetDriverCount(),
    }
    
    return info

def print_gdal_info():
    """打印GDAL信息"""
    info = get_gdal_info()
    print(f"GDAL版本: {info['version']}")
    print(f"GDAL数据目录: {info['data_dir']}")
    print(f"支持的驱动数量: {info['driver_count']}")

if __name__ == "__main__":
    print("GDAL配置测试")
    print("-" * 30)
    print_gdal_info()
    print("✓ GDAL配置成功，无警告信息")