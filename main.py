from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import uvicorn
from routes.account import router as account_router
from routes.league import router as league_router
from routes.match import router as match_router
from routes.rag import router as rag_router
app = FastAPI()
app.include_router(account_router, prefix="/account", tags=["account"])
app.include_router(league_router, prefix="/league", tags=["league"])
app.include_router(match_router, prefix="/match", tags=["match"])
app.include_router(rag_router, prefix="/rag", tags=["rag"])

mcp = FastApiMCP(app,
                 name="Expr MCP",
                 describe_all_responses=True,
                 describe_full_response_schema=True
                 )
mcp.mount_http()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)