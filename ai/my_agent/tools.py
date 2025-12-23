from mcp.server.fastmcp import FastMCP
import json
import os
import time

# 1. 创建服务
mcp = FastMCP("MCPService")

# 2. 定义工具 (和之前一模一样)
@mcp.tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气情况"""
    print(f"Server Log: 正在查询 {city} 的天气...")
    weather_data = {
        "北京": "晴朗, 25°C",
        "上海": "小雨, 22°C",
        "纽约": "多云, 18°C"
    }
    return weather_data.get(city, f"未知城市: {city}")

@mcp.tool()
def list_files_in_directory(directory_path: str):
    """
    这是一个工具函数，用于获取指定目录下的所有文件信息。
    
    参数:
        directory_path (str): 目标文件夹的路径 (例如: "./data")
        
    返回:
        str: 包含文件信息的JSON格式字符串
    """
    
    # 1. 安全性检查：确保路径存在
    if not os.path.exists(directory_path):
        return json.dumps({"error": "Directory not found"})

    files_data = []

    try:
        # 2. 遍历目录下的所有条目
        with os.scandir(directory_path) as entries:
            for entry in entries:
                if entry.is_file():
                    # 3. 获取文件元数据 (大小, 修改时间)
                    stats = entry.stat()
                    file_info = {
                        "filename": entry.name,
                        "size_bytes": stats.st_size,
                        "modified_time": time.ctime(stats.st_mtime),
                        "path": entry.path
                    }
                    files_data.append(file_info)
        
        # 4. 返回 JSON 格式
        return json.dumps(files_data, indent=2, ensure_ascii=False)

    except PermissionError:
        return json.dumps({"error": "Permission denied"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# 3. 启动服务
if __name__ == "__main__":
    # 使用 'sse' 传输模式
    # 这会在底层启动一个类似于 FastAPI/Uvicorn 的 Web 服务器
    # 默认监听地址: http://0.0.0.0:8000
    print("🚀 MCP Server 正在启动，监听端口 8000 (SSE模式)...")
    mcp.run(transport='sse')