from fastapi import FastAPI

app = FastAPI(title="SimpleBank API", version="1.0.0")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the SimpleBank API!"}
