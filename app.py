
import base64
import requests
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from streamlit_geolocation import streamlit_geolocation
import gspread
from pathlib import Path


# Connect to Google Sheets
try:
    google_client = gspread.service_account_from_dict(
        dict(st.secrets["google_sheets"])
    )

    st.session_state["google_client"] = google_client

except Exception as error:
    st.warning("Google Sheets connection is not available.")
    st.caption(f"Technical details: {error}")


# ------------------------------
# PAGE SETUP
# ------------------------------

st.set_page_config(
    page_title="Mould Visual Classifier",
    page_icon="🔬",
    layout="centered",
)

st.title("🔬 Mould Visual Classifier")

st.write(
    "Upload a photograph of suspected mould for a cautious "
    "AI-powered visual assessment."
)

st.warning(
    "A photograph cannot reliably identify the exact mould species "
    "or determine whether mould is toxic, dangerous, or safe. "
    "This tool is for general information only."
)


# ------------------------------
# OPENAI CONNECTION
# ------------------------------

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
except Exception:
    st.error(
        "The Gemini connection is not configured. "
        "Check GEMINI_API_KEY in your secrets.toml file."
    )
    st.stop()


# ------------------------------
# SUPABASE CONNECTION
# ------------------------------

supabase = None



# ------------------------------
# LOCATION FINDER
# ------------------------------

st.divider()
st.subheader("📍 Find your general area")

st.write(
    "Allow location access to look up your general town or county. "
    "Your exact coordinates will not be displayed in the app."
)

location = streamlit_geolocation()

area = None
county = None

if (
    location
    and location.get("latitude") is not None
    and location.get("longitude") is not None
):
    latitude = location["latitude"]
    longitude = location["longitude"]

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "zoom": 10,
            },
            headers={
                "User-Agent": "MouldVisualClassifier/1.0"
            },
            timeout=10,
        )

        response.raise_for_status()
        address = response.json().get("address", {})

        area = (
            address.get("town")
            or address.get("city")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
        )

        county = address.get("county")

        if area:
            st.success("General area detected.")

            if county and county.lower() not in area.lower():
                st.write(f"**Area:** {area}, {county}")
            else:
                st.write(f"**Area:** {area}")

            st.caption(
                "Location names may be approximate. "
                "Your exact coordinates are not shown."
            )
        else:
            st.info(
                "Your location was detected, but a general "
                "area name could not be found."
            )

    except Exception:
        st.warning(
            "We could not look up your area right now. "
            "You can still use the image classifier."
        )
else:
    st.info(
        "Location has not been provided. Allow location access "
        "in your browser if you want to look up your general area."
    )


# ------------------------------
# MOULD IMAGE CLASSIFICATION
# ------------------------------

st.divider()
st.subheader("📸 Analyse a mould photograph")

uploaded_file = st.file_uploader(
    "Choose a photograph",
    type=["jpg", "jpeg", "png", "webp"],
)

def analyse_mould(image_file):
    image_bytes = image_file.getvalue()

    prompt = """
    Analyse this photograph as a cautious visual mould-screening task.

    Choose the closest visual category, if supported by the image:
    - Cladosporium-like
    - Aspergillus-like
    - Penicillium-like
    - Alternaria-like
    - Other possible fungal growth
    - Not obviously mould
    - Unable to determine from photograph

    Return these headings:
    VISUAL CLASSIFICATION:
    CONFIDENCE:
    VISIBLE CHARACTERISTICS:
    OTHER POSSIBILITIES:
    LIMITATIONS:
    SUGGESTED NEXT STEPS:

    Do not claim to identify an exact species.
    Do not claim that mould is toxic, dangerous, or safe based
    only on appearance. Explain the uncertainty of visual assessment.
    """

    response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        prompt,
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=image_file.type or "image/jpeg",
        ),
    ],
)

    return response.text or "Gemini did not return a text result."


if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(
            image,
            caption="Your uploaded photograph",
            width="stretch",
        )

        st.write(
            f"Image size: {image.width} × {image.height} pixels"
        )

        if st.button("🔍 Analyse image", type="primary"):
            with st.spinner(
                "Analysing your photograph..."
            ):
                try:
                    result = analyse_mould(uploaded_file)
                    st.subheader("🔬 Analysis results")
                    st.markdown(result)

                except Exception as error:
                    st.error(
                        "The image analysis could not be completed. "
                        "Check your API key, model access, and internet "
                        "connection."
                    )
                    st.caption(f"Technical details: {error}")

    except Exception:
        st.error(
            "This image could not be opened. "
            "Please try another JPG, PNG, or WebP photograph."
        )
else:
    st.info(
        "Upload a clear photograph of suspected mould to begin."
    )


# ------------------------------
# OPTIONAL MOULD REPORT
# ------------------------------

st.divider()
st.subheader("📝 Submit a general mould report")

st.info(
    "🔒 Privacy notice: Submitting a mould report is optional. "
    "Please enter only your town or general area, not your home address "
    "or other personal information. "
    "Your submitted area, optional county, report type and submission "
    "date will be stored in a private Google Sheet for reviewing "
    "user-submitted mould reports. "
    "Reports are not independently verified."
)

st.write(
    "You can voluntarily submit a report for your general area. "
    "Reports are user-submitted and are not independently verified."
)

report_area = st.text_input(
    "Town or general area",
    value=area or "",
)

report_county = st.text_input(
    "County (optional)",
    value=county or "",
)

report_type = st.selectbox(
    "What did you observe?",
    [
        "Visible mould",
        "Possible mould",
        "Dampness or condensation",
    ],
)


if st.button("Submit mould report"):
    if not report_area.strip():
        st.warning("Please enter a town or general area before submitting.")

    elif "google_client" not in st.session_state:
        st.error("Google Sheets is not connected. Your report was not saved.")



    else:
        try:
            from datetime import datetime, timezone

            spreadsheet = st.session_state["google_client"].open("Mould Reports")
            worksheet = spreadsheet.sheet1

            worksheet.append_row([
                report_area.strip(),
                report_county.strip(),
                report_type,
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            ])

            st.success("Your mould report was submitted successfully!")

        except Exception as error:
            st.error("Your report could not be saved. Please try again later.")
            st.caption(f"Technical details: {error}")




        except Exception as error:
            st.error(
                "Your report could not be saved. "
                "Please try again later."
            )
            st.caption(f"Technical details: {error}")