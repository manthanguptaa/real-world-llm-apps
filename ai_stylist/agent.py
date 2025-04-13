import io
import base64
import google.generativeai as genai
import streamlit as st

class StylistAI:
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.base_prompt = self._get_base_prompt()

    @staticmethod
    def _get_base_prompt():
        return """You are a personal stylist and image consultant with expertise in fashion, grooming, and body-language matching. I will give you two things:

An image of me

The name of a style icon or celebrity whose look I admire

Based on my body type, facial features, skin tone, vibe, and current appearance — analyze what aspects of their style would actually suit me, and what adaptations or alternatives I can try to look like the best version of myself, not just a copy.

I want personalized style tips in these areas:

Clothing (fits, colors, patterns, specific outfit types that match the icon's vibe but suit me)

Hair/grooming (suggest hairstyles, beard styles, etc., aligned with my face shape and style goal)

Accessories & posture (things like glasses, watches, shoes, or body language cues that align with the style icon)

Be honest but constructive. Help me style myself in a way that brings out my strengths while channeling the confidence, edge, or polish of the icon. I don't want generic advice — this should feel like a detailed style breakdown based on who I am.

Use a tone that's practical, self-improvement focused, and motivating without being cheesy. Keep things real and specific."""

    @staticmethod
    def encode_image_to_base64(image):
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def _update_prompt_with_icon(self, style_icon):
        """Update the base prompt with the chosen style icon."""
        return self.base_prompt.replace(
            "The name of a style icon or celebrity whose look I admire",
            f"The style icon I admire: {style_icon}"
        )

    def generate_style_tips(self, image, style_icon):
        """Generate style tips based on the uploaded image and chosen style icon."""
        if not style_icon:
            raise ValueError("Please provide a style icon name")
            
        try:
            prompt = self._update_prompt_with_icon(style_icon)
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            raise Exception(f"Error generating style tips: {str(e)}")

    def run(self):
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
                    analysis = self.generate_style_tips(image, style_icon)
                    st.subheader("Stylist's Analysis:")
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"An error occurred: {e}")