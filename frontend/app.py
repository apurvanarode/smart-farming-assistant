import streamlit as st
import requests

st.set_page_config(page_title="Smart Farming Assistant", page_icon="🌱")

st.title("🌱 Smart Farming Assistant")
st.write("Upload a photo of your crop leaf to get an instant diagnosis.")

BACKEND_URL = "https://smart-farming-backend-vbv6.onrender.com"

uploaded_file = st.file_uploader("Upload leaf image", type=["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"])

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude (approx)", value=18.5204, format="%.4f")
with col2:
    lon = st.number_input("Longitude (approx)", value=73.8567, format="%.4f")

if uploaded_file and st.button("Diagnose"):
    with st.spinner("Analyzing image..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(
                f"{BACKEND_URL}/diagnose?lat={lat}&lon={lon}",
                files=files
            )
            response.raise_for_status()
            result = response.json()

            st.image(uploaded_file, width=300)
            st.subheader(f"Diagnosis: {result['disease'].replace('_', ' ')}")
            st.write(f"Confidence: {result['confidence']*100:.1f}%")
            st.info(result['treatment'])

            st.session_state["last_disease"] = result["disease"]
            st.session_state["chat_history"] = []

        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to backend. Make sure the API server is running. Error: {e}")

if "last_disease" in st.session_state:
    st.divider()
    st.subheader("💬 Ask a follow-up question")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for q, a in st.session_state["chat_history"]:
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Assistant:** {a}")

    question = st.text_input("Your question", key="question_input")
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            try:
                chat_response = requests.post(
                    f"{BACKEND_URL}/chat",
                    params={"disease": st.session_state["last_disease"], "question": question}
                )
                chat_response.raise_for_status()
                answer = chat_response.json()["answer"]
                st.session_state["chat_history"].append((question, answer))
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not get response: {e}")