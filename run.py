"""Standalone entrypoint to launch Foothold Sitac."""

import uvicorn

from foothold_sitac.config import get_config

if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "foothold_sitac.main:app",
        host=config.web.host,
        port=config.web.port,
        reload=config.web.reload,
    )
