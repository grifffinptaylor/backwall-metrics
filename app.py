import streamlit as st
from pathlib import Path
import tempfile
import cv2

from src.video import extract_frames, get_video_metadata
from src.tracker import detect_people, load_model, draw_detections_on_frame, detect_people_in_frames

st.set_page_config(page_title="BackWall Metrics", layout="wide")

st.title("BackWall Metrics")
st.subheader("Squash movement analytics from back-wall footage")

# Initialize session state
if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "frames" not in st.session_state:
    st.session_state.frames = None
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = None
if "model" not in st.session_state:
    st.session_state.model = None
if "detections" not in st.session_state:
    st.session_state.detections = None

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["Upload Video", "Movement Analysis", "Shot Scouting", "Report"]
)

# TAB 1: Upload Video
with tab1:
    st.header("Upload Video")
    
    uploaded_file = st.file_uploader(
        "Upload a squash rally video",
        type=["mp4", "mov", "avi"]
    )

    if uploaded_file is not None:
        # Save video to temp directory
        if st.session_state.temp_dir is None:
            st.session_state.temp_dir = tempfile.mkdtemp()
        
        st.session_state.video_path = Path(st.session_state.temp_dir) / uploaded_file.name

        with open(st.session_state.video_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success("✓ Video uploaded successfully")
        
        # Show video preview
        st.subheader("Video Preview")
        st.video(str(st.session_state.video_path))
        
        # Get video metadata
        try:
            metadata = get_video_metadata(str(st.session_state.video_path))
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Duration", f"{metadata['duration']:.1f} sec")
            with col2:
                st.metric("FPS", f"{metadata['fps']:.1f}")
            with col3:
                st.metric("Total Frames", metadata['frame_count'])
        except Exception as e:
            st.error(f"Could not read video metadata: {e}")
        
        # Time range inputs
        st.subheader("Select Rally/Point Segment")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input(
                "Start time (seconds)",
                min_value=0.0,
                value=0.0,
                step=0.1
            )
        with col2:
            end_time = st.number_input(
                "End time (seconds)",
                min_value=0.1,
                value=min(30.0, metadata.get('duration', 30.0)),
                step=0.1
            )
        
        # Frame extraction settings
        st.subheader("Frame Extraction Settings")
        every_n_frames = st.slider(
            "Extract every N frames",
            min_value=1,
            max_value=30,
            value=15,
            help="Lower = more frames extracted, higher = fewer frames (faster)"
        )
        
        # Extract frames button
        if st.button("🎬 Extract Frames", key="extract_frames_btn"):
            if start_time >= end_time:
                st.error("❌ Start time must be less than end time")
            else:
                frame_dir = Path(st.session_state.temp_dir) / "frames"
                
                with st.spinner("Extracting frames..."):
                    try:
                        st.session_state.frames = extract_frames(
                            st.session_state.video_path,
                            frame_dir,
                            start_time=start_time,
                            end_time=end_time,
                            every_n_frames=every_n_frames
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error extracting frames: {e}")
        
        # Display results after extraction
        if st.session_state.frames and len(st.session_state.frames) > 0:
            st.divider()
            st.success(f"✓ Successfully extracted {len(st.session_state.frames)} frames")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Frames Extracted", len(st.session_state.frames))
            with col2:
                duration = end_time - start_time
                st.metric("Duration (sec)", f"{duration:.1f}")
            with col3:
                est_fps = len(st.session_state.frames) / (duration if duration > 0 else 1)
                st.metric("Effective FPS", f"{est_fps:.1f}")
            
            st.subheader("First Extracted Frame")
            st.image(str(st.session_state.frames[0]), use_container_width=True)
            st.caption(f"Frame 1 of {len(st.session_state.frames)}")
            
            # Next steps
            st.info("✨ **Next Steps:**\n1. Go to the **Movement Analysis** tab to view the frame gallery\n2. In future milestones: calibrate court, select player, track movement")

# TAB 2: Movement Analysis
with tab2:
    st.header("Movement Analysis")
    
    if st.session_state.frames is None or len(st.session_state.frames) == 0:
        st.info("👈 **First, upload a video and extract frames in the 'Upload Video' tab**")
    else:
        st.success(f"✓ {len(st.session_state.frames)} frames loaded and ready for analysis")
        
        st.divider()
        st.subheader("🤖 Person Detection")
        st.write("Detect people in your video frames using YOLO.")
        
        # Detection settings
        col1, col2 = st.columns(2)
        with col1:
            confidence_threshold = st.slider(
                "Detection Confidence Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Lower = more detections (including false positives), Higher = fewer but more confident detections"
            )
        with col2:
            sample_every_n = st.slider(
                "Sample Every N Frames",
                min_value=1,
                max_value=10,
                value=3,
                help="Run detection on every Nth frame (for speed)"
            )
        
        # Run detection button
        if st.button("🔍 Run Person Detection", key="run_detection_btn"):
            with st.spinner("Loading YOLO model..."):
                if st.session_state.model is None:
                    st.session_state.model = load_model()
            
            with st.spinner("Detecting people in frames..."):
                try:
                    st.session_state.detections = detect_people_in_frames(
                        st.session_state.model,
                        st.session_state.frames,
                        confidence=confidence_threshold,
                        sample_every_n=sample_every_n
                    )
                    st.success(f"✓ Detection complete! Found people in {len(st.session_state.detections)} frames")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error during detection: {e}")
        
        # Display detection results
        if st.session_state.detections:
            st.divider()
            st.subheader("📊 Detection Results")
            
            # Summary stats
            total_detections = sum(len(dets) for dets in st.session_state.detections.values())
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Frames with Detections", len(st.session_state.detections))
            with col2:
                st.metric("Total People Detected", total_detections)
            with col3:
                avg_per_frame = total_detections / len(st.session_state.detections) if st.session_state.detections else 0
                st.metric("Avg People per Frame", f"{avg_per_frame:.1f}")
            
            st.divider()
            
            # Show annotated sample frames
            st.subheader("📽️ Sample Annotated Frames")
            st.write("Frames with detected bounding boxes:")
            
            # Get frames with detections
            detected_frame_paths = list(st.session_state.detections.keys())[:5]
            
            if detected_frame_paths:
                cols = st.columns(min(3, len(detected_frame_paths)))
                
                for idx, frame_path in enumerate(detected_frame_paths):
                    detections = st.session_state.detections[frame_path]
                    
                    if len(detections) > 0:
                        with cols[idx % len(cols)]:
                            with st.spinner(f"Annotating frame {idx+1}..."):
                                annotated = draw_detections_on_frame(
                                    frame_path,
                                    detections,
                                    color=(0, 255, 0)
                                )
                                
                                # Convert BGR to RGB for display
                                annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                                st.image(annotated_rgb, use_container_width=True)
                                st.caption(f"{len(detections)} people detected")
            else:
                st.warning("⚠️ No people detected in any frames")
        
        # Frame gallery (always show)
        st.divider()
        st.subheader("📽️ Full Frame Gallery")
        st.write(f"All extracted frames ({len(st.session_state.frames)} total):")
        
        cols = st.columns(5)
        for idx, frame_path in enumerate(st.session_state.frames[:15]):
            with cols[idx % 5]:
                st.image(str(frame_path), use_container_width=True)
                st.caption(f"Frame {idx+1}")
        
        if len(st.session_state.frames) > 15:
            st.caption(f"... and {len(st.session_state.frames) - 15} more frames")

# TAB 3: Shot Scouting
with tab3:
    st.header("Shot Scouting")
    st.info("Coming in later milestones")

# TAB 4: Report
with tab4:
    st.header("Report")
    st.info("Coming in later milestones")