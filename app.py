import streamlit as st
from pathlib import Path
import tempfile

from src.video import extract_frames
from src.tracker import load_model, detect_people

st.set_page_config(page_title="BackWall Metrics", layout="wide")

st.title("BackWall Metrics")
st.subheader("Squash movement analytics from back-wall footage")

uploaded_file = st.file_uploader(
    "Upload a squash rally video",
    type=["mp4", "mov", "avi"]
)

if uploaded_file is not None:
    temp_dir = tempfile.mkdtemp()
    video_path = Path(temp_dir) / uploaded_file.name

    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("Video uploaded successfully.")
    st.video(str(video_path))

    if st.button("Extract frames"):
        frame_dir = Path(temp_dir) / "frames"
        frames = extract_frames(video_path, frame_dir, every_n_frames=15)

        st.write(f"Extracted {len(frames)} frames.")

        if frames:
            st.image(str(frames[0]), caption="First extracted frame")


if st.button("Detect people in first frame"):
    model = load_model()
    people = detect_people(model, frames[0])

    st.write(people)