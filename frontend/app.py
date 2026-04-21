import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# UI через REST API
API = "http://api:8000"

st.set_page_config(page_title="AI Sentiment", layout="centered")

st.title("Simple AI Sentiment Analysis From Text Platform")
st.markdown("Analyze text sentiment asynchronously using ML")

text = st.text_area("Enter text", height=150)

if st.button("Analyze"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        try:
            response = requests.post(f"{API}/predict", json={"text": text}, timeout=30)

            if response.status_code != 202:
                st.error(f"API error: {response.text}")
            else:
                task_id = response.json()["task_id"]
                #st.info(f"Task created: {task_id}")
                # Debug only
                print(f"Task created: {task_id}")

                # UX асинхронности
                progress = st.progress(0)
                result_box = st.empty()

                for i in range(50):
                    result = requests.get(f"{API}/result/{task_id}", timeout=30)
                    result_json = result.json()

                    if result_json["status"] == "done":
                        result_box.success(
                            f"Result: {result_json['sentiment']}"
                        )
                        break
                    elif result_json["status"] == "failed":
                        result_box.error(f"Task failed: {result_json}")
                        break

                    progress.progress(min((i + 1) * 2, 100))
                    time.sleep(1)
                else:
                    result_box.warning("Task is still running. Please try again in a moment.")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()

if st.button("Load Analytics"):
    try:
        response = requests.get(f"{API}/history", timeout=30)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)
        st.dataframe(df)

        if not df.empty:
            fig = px.pie(df, names="sentiment", title="Sentiment Distribution") # Визуальная репрезентация
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No predictions yet.")

    except Exception as e:
        st.error(f"Failed to load data: {e}")