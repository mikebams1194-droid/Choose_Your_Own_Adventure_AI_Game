import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import story, job
from db.database import create_tables

# Initialize DB
create_tables()

# 1. Initialize FastAPI WITHOUT a root_path for now
app = FastAPI(title="Adventure Game API")

# 2. Add CORS Middleware IMMEDIATELY after initializing app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Using wildcard to force permission
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Simple Health Check at the ACTUAL root
@app.get("/")
def home():
    return {"message": "API is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# 4. Include Routers
app.include_router(story.router)
app.include_router(job.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
