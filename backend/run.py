"""后端启动脚本"""
import uvicorn
from config import HOST, PORT, DEBUG

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,  # 开发环境自动重载
        log_level="info"
    )

