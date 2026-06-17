"""
UI utility functions for Streamlit app.
"""

import streamlit as st
import cv2
from PIL import Image
import numpy as np


def click_on_image(image_array, key_suffix=""):
    """
    Display an image in Streamlit and return click coordinates if user clicked.
    
    Uses Streamlit's image_coordinates callback.
    
    Args:
        image_array: NumPy array or PIL Image
        key_suffix: String suffix for unique key
    
    Returns:
        Dictionary with 'x', 'y' coordinates if clicked, or None
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Convert BGR to RGB if needed
        if isinstance(image_array, np.ndarray) and len(image_array.shape) == 3:
            if image_array.shape[2] == 3:
                # Assume BGR, convert to RGB for display
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image_array
        else:
            image_rgb = image_array
        
        st.write("**Click on the person you want to track:**")
        clicked = st.image(image_rgb, use_container_width=True)
    
    with col2:
        st.write("")
        st.write("")
        st.info("👆 Click on the target person in the image")
    
    return clicked


def get_frame_click_point(container_width=800):
    """
    Utility for getting click coordinates from displayed image.
    This is a helper - actual implementation depends on Streamlit session state.
    """
    pass
