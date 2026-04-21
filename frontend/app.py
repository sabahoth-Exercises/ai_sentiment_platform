import os
import time

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import json

# UI через REST API
API = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="AI Sentiment", layout="centered")

st.title("Simple AI Sentiment Analysis From Text Platform")
st.markdown("Analyze Latin-only text sentiment asynchronously using ML")

text = st.text_area(
    "Enter text",
    height=150,
    help="Only Latin letters, numbers, spaces and basic punctuation are allowed. Text must contain at least one Latin letter, 5 letters.",
)

if st.button("Analyze"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        try:
            response = requests.post(
                f"{API}/predict",
                data=json.dumps({"text": text}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30,
                )
            if response.status_code == 422:
                try:
                    detail = response.json()
                    hint = detail.get(
                        "hint",
                        "Validation failed. Only Latin text is allowed."
                    )
                    st.error(hint)
                except Exception:
                    st.error("Validation failed. Only Latin text is allowed.")

            elif response.status_code != 202:
                try:
                    st.error(f"API error: {response.json()}")
                except Exception:
                    st.error(f"API error: {response.text}")

            else:
                task_id = response.json()["task_id"]

                progress = st.progress(0)
                result_box = st.empty()

                for i in range(50):
                    result = requests.get(f"{API}/result/{task_id}", timeout=30)
                    result_json = result.json()

                    if result_json["status"] == "done":
                        sentiment = result_json["sentiment"]
                        icon = {
                            "positive": "😊",
                            "neutral": "😐",
                            "negative": "😞",
                        }.get(sentiment, "ℹ️")
                        result_box.success(f"{icon} Result: {sentiment}")
                        break

                    elif result_json["status"] == "failed":
                        result_box.error("Task failed")
                        break

                    progress.progress(min((i + 1) * 2, 100))
                    time.sleep(1)
                else:
                    result_box.warning("Task is still running. Please try again in a moment.")

        except requests.exceptions.RequestException as e:
            st.error(f"Service temporarily unavailable: {e}")

st.divider()

if st.button("Load Analytics"):
    try:
        response = requests.get(f"{API}/history", timeout=30)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)
        st.dataframe(df)

        if not df.empty:
            fig = px.pie(df, names="sentiment", title="Sentiment Distribution")  # Визуальная репрезентация
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No predictions yet.")

    except requests.exceptions.RequestException:
        st.error("Service temporarily unavailable")