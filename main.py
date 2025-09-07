import os
import uuid
import subprocess
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

OUTPUT_DIR = "generated_movies"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Placeholder ML Interpreter ---
def interpret_script(script_text: str):
    """
    Very simple ML stub:
    - If script mentions 'battle' → dark bg
    - If script mentions 'love' → pink bg
    - Otherwise → blue bg
    """
    script_lower = script_text.lower()
    if "battle" in script_lower:
        return "red"
    elif "love" in script_lower:
        return "pink"
    return "blue"


def generate_movie(script_text: str):
    """Generate simple movie using ffmpeg."""
    job_id = str(uuid.uuid4())
    output_file = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    bg_color = interpret_script(script_text)

    cmd = [
        "ffmpeg", "-f", "lavfi", f"-i", f"color=c={bg_color}:s=1280x720:d=6",
        "-vf", f"drawtext=text='{script_text[:40]}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-y", output_file
    ]
    subprocess.run(cmd, check=True)
    return job_id, output_file


def preview_movie(job_id: str):
    preview_file = os.path.join(OUTPUT_DIR, f"{job_id}_preview.jpg")
    movie_file = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    if not os.path.exists(movie_file):
        return None
    cmd = ["ffmpeg", "-i", movie_file, "-ss", "00:00:02.000", "-vframes", "1", preview_file, "-y"]
    subprocess.run(cmd, check=True)
    return preview_file


@app.post("/generate")
async def generate(script: str = Form(...)):
    job_id, output_file = generate_movie(script)
    return {"job_id": job_id, "status": "done"}


@app.get("/preview/{job_id}")
async def preview(job_id: str):
    preview_path = preview_movie(job_id)
    if preview_path:
        return FileResponse(preview_path, media_type="image/jpeg")
    return {"error": "Preview not available"}


@app.get("/download/{job_id}")
async def download(job_id: str):
    movie_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    if os.path.exists(movie_path):
        return FileResponse(movie_path, media_type="video/mp4", filename=f"{job_id}.mp4")
    return {"error": "Movie not found"}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend index.html"""
    with open("index.html", "r") as f:
        return f.read()
