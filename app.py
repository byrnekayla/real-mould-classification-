import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Mould Classifier",
    page_icon="🔬"
)

st.title("🔬 Mould Visual Classifier")

st.write(
    "Upload a photograph of suspected mould and the app "
    "will help classify its visual appearance."
)

st.warning(
    "This is a visual screening tool only. A photograph cannot "
    "reliably identify mould species or determine whether mould "
    "is hazardous. Professional testing is required for a "
    "confirmed identification."
)

uploaded_file = st.file_uploader(
    "Choose a mould photograph",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:

    image = Image.open(uploaded_file)

    st.subheader("Your image")

    st.image(
        image,
        caption="Uploaded photograph",
        use_container_width=True
    )

    st.subheader("Image information")

    width, height = image.size

    st.write(f"Image size: **{width} × {height} pixels**")

    if st.button("🔍 Analyse image"):

        st.info(
            "The image has been successfully uploaded. "
            "The AI classification system will be connected "
            "in the next step."
        )

        st.subheader("Current status")

        st.write(
            "Image received successfully. "
            "No biological identification has been made yet."
        )

else:

    st.info(
        "Upload a clear photograph of the suspected mould "
        "to begin."
    )