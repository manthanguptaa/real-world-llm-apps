import streamlit as st
from PIL import Image
from agent import StylistAI
from dotenv import load_dotenv
import os

def main():
    st.title("Stylist AI")
    
    # Initialize StylistAI with API key from Streamlit secrets
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    stylist = StylistAI(api_key=api_key)
    
    uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Read and display the image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", use_column_width=True)

        # Get style icon name from user
        style_icon = st.text_input(
            "Enter the name of a style icon or celebrity whose look you admire:",
            placeholder="e.g., Ryan Gosling, Zendaya, Harry Styles"
        )

        if st.button("Give Tips"):
            try:
                # Encode image to base64
                encoded_image = StylistAI.encode_image_to_base64(image)
                analysis = stylist.generate_style_tips(image, style_icon)
                st.subheader("Stylist's Analysis:")
                st.markdown(analysis)
            except Exception as e:  
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()