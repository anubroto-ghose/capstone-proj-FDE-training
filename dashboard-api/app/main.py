from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import dashboard_routes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_routes.router)

@app.get("/")
def read_root():
    return {"message": "Dashboard API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
