import uvicorn

def start_dev_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def start_prod_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
