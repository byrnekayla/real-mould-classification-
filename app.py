import base64

import streamlit as st
from PIL import Image
from openai import OpenAI


st.set_page_config(
    page_title="Mould Visual Classifier",
    page_icon="🔬"
)

st.title("🔬 Mould Visual Classifier")

st.write(
    "Upload a photograph of suspected mould and the AI will "
    "provide a general visual classification."
)

st.warning(
    "This is a visual screening tool only. A photograph cannot "
    "reliably identify the exact mould species or determine whether "
    "mould is toxic, dangerous, or safe."
)


client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)


uploaded_file = st.file_uploader(
    "Choose a mould photograph",
    type=["jpg", "jpeg", "png", "webp"]
)


def analyse_mould(image_file):

    image_bytes = image_file.getvalue()

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = image_file.type

    image_data = f"data:{mime_type};base64,{encoded_image}"

    prompt = """
Analyse this photograph as a general visual mould-screening task.

Give a cautious visual classification using one of these categories:

- Cladosporium-like
- Aspergillus-like
- Penicillium-like
- Alternaria-like
- Fusarium-like
- Other fungal/mould growth
- Not obviously mould
- Unable to determine from photograph

Do NOT claim to identify an exact species.

Do NOT state that the material is toxic, dangerous, or safe based
only on its appearance.

Return the answer using these headings:

VISUAL CLASSIFICATION:
CONFIDENCE:
OTHER POSSIBILITIES:
VISIBLE CHARACTERISTICS:
LIMITATIONS:

Explain that visual appearance alone cannot provide a definitive
biological identification.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data
                    }
                ]
            }
        ]
    )

    return response.output_text


if uploaded_file is not None:

    image = Image.open(uploaded_file)

    st.subheader("Your image")

    st.image(
        image,
        caption="Uploaded photograph",
        width="stretch"
    )

    width, height = image.size

    st.write(
        f"Image size: **{width} × {height} pixels**"
    )

    if st.button("🔍 Analyse image"):

        with st.spinner("Analysing the photograph..."):

            try:

                result = analyse_mould(uploaded_file)

                st.subheader("🔬 Analysis")

                st.write(result)

            except Exception as e:

                st.error(
                    "The image analysis could not be completed."
                )

                st.write(
                    f"Error: {e}"
                )

else:

    st.info(
        "Upload a clear photograph of suspected mould to begin."
    )