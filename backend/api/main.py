"""
EasyChatBot API Application.

Hosts the user interaction layer.
"""


from fastapi import FastAPI


from backend.api.routes import router


app = FastAPI(
    title="EasyChatBot",
    description=(
        "AI companion learning platform"
    ),
)


app.include_router(
    router,
)


@app.get("/")
def health():

    return {
        "status": "EasyChatBot running",
        "architecture": (
            "Runtime + Agents + Memory"
        ),
    }