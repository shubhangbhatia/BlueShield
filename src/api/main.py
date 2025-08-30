from fastapi import FastAPI

app = FastAPI(title="Coastal Early Warning System API")

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
