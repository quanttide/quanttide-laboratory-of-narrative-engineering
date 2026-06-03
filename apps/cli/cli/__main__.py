"""启动 FastAPI 服务."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("cli.app:app", host="0.0.0.0", port=8000, reload=True)
