from fastapi import FastAPI

from router.advertisements import router as advertisement_router

app = FastAPI(
    title="Newspaper Advertisement API",
    version="1.0.0"
)

app.include_router(advertisement_router)


@app.get("/")
def get():
    return {"message": "Newspaper API is running"}