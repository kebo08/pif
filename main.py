from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI()


origins = [
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_obj_file")
def get_obj_file():
    file_path = Path("sample.obj")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="application/octet-stream", filename="sample.obj")

# @app.get("/get_nii_image")
# def get_nii_image():
#     file_path = Path("example.nii.gz")
#     if not file_path.exists():
#         raise HTTPException(status_code=404, detail="File not found")
#     return FileResponse(path=file_path, media_type="application/octet-stream", filename="example.nii.gz")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=3000)
