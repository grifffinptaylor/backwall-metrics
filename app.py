import streamlit as st
from pathlib import Path
import tempfile
import cv2
import pandas as pd
import numpy as np

from src.video import extract_frames, get_video_metadata
from src.tracker import (
    detect_people, 
    load_model, 
    draw_detections_on_frame, 
    detect_people_in_frames,
    track_target_player,
    draw_tracking_path
)
from src.court import (
    get_default_court_config,
    get_court_zones,
    compute_homography,
    video_to_court_points,
    assign_zone,
    draw_court_graphic,
    draw_path_on_court,
    calibration_preview
)

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
if "target_point" not in st.session_state:
    st.session_state.target_point = None
if "target_person_idx" not in st.session_state:
    st.session_state.target_person_idx = None
if "tracking_df" not in st.session_state:
    st.session_state.tracking_df = None
if "calibration_points_video" not in st.session_state:
    st.session_state.calibration_points_video = []
if "calibration_points_court" not in st.session_state:
    st.session_state.calibration_points_court = []
if "homography" not in st.session_state:
    st.session_state.homography = None
if "calibrated_tracking_df" not in st.session_state:
    st.session_state.calibrated_tracking_df = None
if "court_config" not in st.session_state:
    st.session_state.court_config = get_default_court_config()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Upload Video", "Movement Analysis", "Court Calibration", "Shot Scouting", "Report"]
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
            st.subheader("🎯 Select Target Player")
            st.write("Click on a person in the frame below to select them as your target player for tracking.")
            
            # Get first frame with detections for target selection
            detected_frame_paths = list(st.session_state.detections.keys())
            if detected_frame_paths:
                first_frame_path = detected_frame_paths[0]
                detections_in_first = st.session_state.detections[first_frame_path]
                
                if len(detections_in_first) > 0:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("**Click buttons below to select a person:**")
                        
                        # Show frame with all detections
                        annotated = draw_detections_on_frame(
                            first_frame_path,
                            detections_in_first,
                            color=(0, 255, 0)
                        )
                        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        st.image(annotated_rgb, use_container_width=True)
                    
                    with col2:
                        st.write("")
                        st.write("")
                        # Person selection buttons
                        for idx, det in enumerate(detections_in_first[:10]):  # Limit to 10 people
                            btn_label = f"Person {idx+1}\n({det['conf']:.2f})"
                            if st.button(btn_label, key=f"select_person_{idx}"):
                                st.session_state.target_person_idx = idx
                                st.session_state.target_point = (det["center_x"], det["center_y"])
                                st.success(f"✓ Selected Person {idx+1} as target")
                                st.rerun()
                    
                    # Show target selection status
                    if st.session_state.target_point:
                        st.info(f"✓ **Target Selected:** Person {st.session_state.target_person_idx + 1} at position {st.session_state.target_point}")
                        
                        # Show target selection on frame
                        annotated_with_target = draw_detections_on_frame(
                            first_frame_path,
                            detections_in_first,
                            color=(0, 255, 0),
                            highlighted_idx=st.session_state.target_person_idx
                        )
                        annotated_rgb = cv2.cvtColor(annotated_with_target, cv2.COLOR_BGR2RGB)
                        st.image(annotated_rgb, use_container_width=True)
                        st.caption("Target player highlighted in blue")
            
            # Tracking section
            if st.session_state.target_point:
                st.divider()
                st.subheader("📍 Track Target Player")
                st.write("Track your selected player across all frames.")
                
                col1, col2 = st.columns(2)
                with col1:
                    max_distance = st.slider(
                        "Max Tracking Distance (pixels)",
                        min_value=10,
                        max_value=500,
                        value=100,
                        help="Maximum pixel distance to match person between frames"
                    )
                with col2:
                    fps = st.number_input(
                        "FPS (frames per second)",
                        min_value=1.0,
                        max_value=120.0,
                        value=30.0,
                        step=1.0,
                        help="Frames per second for time calculation"
                    )
                
                if st.button("▶️ Start Tracking", key="run_tracking_btn"):
                    with st.spinner("Tracking player across frames..."):
                        try:
                            st.session_state.tracking_df = track_target_player(
                                st.session_state.model,
                                st.session_state.frames,
                                st.session_state.target_point,
                                fps=fps,
                                confidence=confidence_threshold,
                                max_distance=max_distance
                            )
                            st.success(f"✓ Tracking complete!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error during tracking: {e}")
            
            # Display tracking results
            if st.session_state.tracking_df is not None:
                st.divider()
                st.subheader("📊 Tracking Results")
                
                tracking_df = st.session_state.tracking_df
                matched_frames = tracking_df[tracking_df["matched"] == True]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Frames Tracked", len(matched_frames))
                with col2:
                    avg_conf = matched_frames["confidence"].mean() if len(matched_frames) > 0 else 0
                    st.metric("Avg Confidence", f"{avg_conf:.3f}")
                with col3:
                    gaps = len(tracking_df[tracking_df["matched"] == False])
                    st.metric("Gap Frames", gaps)
                with col4:
                    if len(matched_frames) > 1:
                        x_diff = matched_frames["video_x"].max() - matched_frames["video_x"].min()
                        y_diff = matched_frames["video_y"].max() - matched_frames["video_y"].min()
                        range_pixels = max(x_diff, y_diff)
                        st.metric("Movement Range", f"{range_pixels:.0f}px")
                
                st.divider()
                
                # Show tracking path visualization
                st.subheader("📽️ Tracking Path Visualization")
                st.write("Magenta line shows the tracked player's movement path:")
                
                # Get first frame to show path on
                first_frame = str(st.session_state.frames[0])
                with st.spinner("Rendering tracking path..."):
                    try:
                        path_frame = draw_tracking_path(first_frame, tracking_df, color=(255, 0, 255), thickness=2)
                        path_rgb = cv2.cvtColor(path_frame, cv2.COLOR_BGR2RGB)
                        st.image(path_rgb, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not render path: {e}")
                
                st.divider()
                
                # Show tracking data table
                st.subheader("📋 Tracking Data (First 20 frames)")
                display_df = tracking_df.head(20).copy()
                display_df["video_x"] = display_df["video_x"].round(1)
                display_df["video_y"] = display_df["video_y"].round(1)
                display_df["confidence"] = display_df["confidence"].round(4)
                st.dataframe(display_df, use_container_width=True)
                
                # Download tracking data
                csv_data = tracking_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Tracking Data (CSV)",
                    data=csv_data,
                    file_name="tracking_data.csv",
                    mime="text/csv"
                )
                
                # Next steps for court mapping
                st.divider()
                st.info("💡 **Next Steps (Milestone 4):**\n" +
                       "• Court calibration to map video coordinates to top-down court coordinates\n" +
                       "• Calculate T-position metrics (recovery time, distance from T, etc.)\n" +
                       "• Generate movement heatmap")
        
        # Frame gallery (always show at bottom)
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

# TAB 3: Court Calibration
with tab3:
    st.header("🎾 Court Calibration")
    
    if st.session_state.tracking_df is None:
        st.info("👈 **First, complete player tracking in the 'Movement Analysis' tab**")
    else:
        st.success(f"✓ Tracking data available ({len(st.session_state.tracking_df)} frames)")
        
        st.divider()
        st.subheader("📍 Court Calibration Setup")
        st.write("Click buttons to select 5 key points on the court from a video frame.")
        st.write("This calibration maps video pixels to court coordinates.")
        
        # Display first frame for calibration
        first_frame_path = st.session_state.frames[0]
        frame = cv2.imread(str(first_frame_path))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Show calibration point status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Points Selected", len(st.session_state.calibration_points_video))
        with col2:
            st.metric("Required", 5)
        with col3:
            st.metric("Status", "Complete" if len(st.session_state.calibration_points_video) == 5 else "Incomplete")
        
        st.divider()
        st.subheader("Step 1: Select Calibration Points")
        st.write("Click a button, then the pixel coordinates will be recorded from the frame.")
        
        # Calibration point buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("1️⃣ Front-Left Corner", key="cal_front_left"):
                # In real app, user would click on frame - for now use default
                st.session_state.calibration_points_video = st.session_state.calibration_points_video[:0]
                st.session_state.calibration_points_video.append((100, 50))  # Example
                st.session_state.calibration_points_court = [(0, 0)]
                st.success("Point 1 recorded (example)")
                st.rerun()
        
        with col2:
            if st.button("2️⃣ Front-Right Corner", key="cal_front_right"):
                if len(st.session_state.calibration_points_video) >= 1:
                    st.session_state.calibration_points_video.append((frame.shape[1] - 100, 50))
                    st.session_state.calibration_points_court.append((100, 0))
                    st.success("Point 2 recorded (example)")
                    st.rerun()
                else:
                    st.warning("Select Front-Left first")
        
        with col3:
            if st.button("3️⃣ Back-Left Corner", key="cal_back_left"):
                if len(st.session_state.calibration_points_video) >= 2:
                    st.session_state.calibration_points_video.append((100, frame.shape[0] - 50))
                    st.session_state.calibration_points_court.append((0, 100))
                    st.success("Point 3 recorded (example)")
                    st.rerun()
                else:
                    st.warning("Select Front corners first")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("4️⃣ Back-Right Corner", key="cal_back_right"):
                if len(st.session_state.calibration_points_video) >= 3:
                    st.session_state.calibration_points_video.append((frame.shape[1] - 100, frame.shape[0] - 50))
                    st.session_state.calibration_points_court.append((100, 100))
                    st.success("Point 4 recorded (example)")
                    st.rerun()
                else:
                    st.warning("Select Back-Left first")
        
        with col2:
            if st.button("5️⃣ T Position", key="cal_t_position"):
                if len(st.session_state.calibration_points_video) >= 4:
                    st.session_state.calibration_points_video.append((frame.shape[1] // 2, int(frame.shape[0] * 0.6)))
                    st.session_state.calibration_points_court.append((50, 62))
                    st.success("Point 5 recorded (example)")
                    st.rerun()
                else:
                    st.warning("Select all corners first")
        
        with col3:
            if st.button("🔄 Reset Calibration", key="reset_calibration"):
                st.session_state.calibration_points_video = []
                st.session_state.calibration_points_court = []
                st.session_state.homography = None
                st.session_state.calibrated_tracking_df = None
                st.success("Calibration reset")
                st.rerun()
        
        # Show calibration preview
        if len(st.session_state.calibration_points_video) > 0:
            st.divider()
            st.subheader("Calibration Point Preview")
            
            preview_img = calibration_preview(
                frame_rgb,
                st.session_state.calibration_points_video,
                st.session_state.court_config
            )
            st.image(preview_img, use_container_width=True)
            st.caption(f"Showing {len(st.session_state.calibration_points_video)} calibration points")
        
        # Compute homography and apply
        if len(st.session_state.calibration_points_video) == 5:
            st.divider()
            st.subheader("Step 2: Apply Calibration")
            
            if st.button("📐 Compute Calibration", key="compute_calibration"):
                try:
                    with st.spinner("Computing homography matrix..."):
                        st.session_state.homography = compute_homography(
                            st.session_state.calibration_points_video,
                            st.session_state.calibration_points_court
                        )
                    
                    with st.spinner("Transforming tracking data to court coordinates..."):
                        # Transform tracking data
                        tracking_df = st.session_state.tracking_df.copy()
                        
                        # Get matched frames only
                        matched_mask = tracking_df["matched"] == True
                        matched_points = tracking_df.loc[matched_mask, ["video_x", "video_y"]].values
                        
                        if len(matched_points) > 0:
                            court_points = video_to_court_points(
                                matched_points,
                                st.session_state.homography
                            )
                            
                            # Add court coordinates
                            tracking_df["court_x"] = np.nan
                            tracking_df["court_y"] = np.nan
                            tracking_df.loc[matched_mask, "court_x"] = court_points[:, 0]
                            tracking_df.loc[matched_mask, "court_y"] = court_points[:, 1]
                            
                            # Assign zones
                            tracking_df["zone"] = tracking_df.apply(
                                lambda row: assign_zone(row["court_x"], row["court_y"], get_court_zones())
                                if pd.notna(row["court_x"]) else "unknown",
                                axis=1
                            )
                            
                            st.session_state.calibrated_tracking_df = tracking_df
                    
                    st.success("✓ Calibration applied successfully!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error during calibration: {e}")
            
            if st.session_state.homography is not None:
                st.divider()
                st.subheader("✓ Calibration Complete!")
                st.success("Tracking data has been transformed to court coordinates")
                
                # Show results
                if st.session_state.calibrated_tracking_df is not None:
                    cal_df = st.session_state.calibrated_tracking_df
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Frames Calibrated", len(cal_df[cal_df["matched"] == True]))
                    with col2:
                        st.metric("Gap Frames", len(cal_df[cal_df["matched"] == False]))
                    with col3:
                        zones = cal_df["zone"].value_counts()
                        st.metric("Unique Zones", len(zones))
                    with col4:
                        court_range = max(
                            cal_df["court_x"].max() - cal_df["court_x"].min(),
                            cal_df["court_y"].max() - cal_df["court_y"].min()
                        )
                        st.metric("Court Range", f"{court_range:.1f}")
                    
                    st.divider()
                    st.subheader("📊 Calibrated Tracking Data (First 20 frames)")
                    display_df = cal_df.head(20).copy()
                    display_df["video_x"] = display_df["video_x"].round(1)
                    display_df["video_y"] = display_df["video_y"].round(1)
                    display_df["court_x"] = display_df["court_x"].round(2)
                    display_df["court_y"] = display_df["court_y"].round(2)
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Show court visualization
                    st.divider()
                    st.subheader("🎾 Movement Path on Court")
                    
                    court_img = draw_court_graphic(800, 800, st.session_state.court_config)
                    
                    matched_data = cal_df[cal_df["matched"] == True]
                    if len(matched_data) > 0:
                        court_path = matched_data[["court_x", "court_y"]].values
                        court_img = draw_path_on_court(
                            court_img,
                            court_path,
                            st.session_state.court_config,
                            color=(0, 255, 0),
                            thickness=2
                        )
                    
                    court_img_rgb = cv2.cvtColor(court_img, cv2.COLOR_BGR2RGB)
                    st.image(court_img_rgb, use_container_width=True)
                    st.caption("Player movement path on court (green = tracked, red dot = end, blue dot = start)")
                    
                    # Download calibrated data
                    st.divider()
                    csv_data = cal_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Calibrated Tracking Data (CSV)",
                        data=csv_data,
                        file_name="calibrated_tracking_data.csv",
                        mime="text/csv"
                    )

# TAB 4: Shot Scouting
with tab4:
    st.header("Shot Scouting")
    st.info("Coming in later milestones")

# TAB 5: Report
with tab5:
    st.header("Report")
    st.info("Coming in later milestones")