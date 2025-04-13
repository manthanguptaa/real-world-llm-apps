import streamlit as st
from PIL import Image
from agent import StylistAI

def main():
    stylist = StylistAI()
    st.title("Stylist AI")
    
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
                analysis = stylist.generate_style_tips(image, style_icon)
                st.subheader("Stylist's Analysis:")
                st.markdown(analysis)
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()