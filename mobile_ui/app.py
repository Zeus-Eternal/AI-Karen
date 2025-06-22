import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Kari Mobile", layout="wide")

st.sidebar.title("Kari Mobile Control")
page = st.sidebar.radio("Navigate", ["Chat", "Memory", "Plugins", "Metrics"])


def api_post(path, payload=None):
    try:
        res = requests.post(f"{API_URL}{path}", json=payload or {})
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        return None


def api_get(path):
    try:
        res = requests.get(f"{API_URL}{path}")
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        return None


if page == "Chat":
    st.header("Chat")
    msg = st.text_input("Message")
    if st.button("Send") and msg:
        data = api_post("/chat", {"text": msg})
        if data:
            st.write(f"**Intent:** {data['intent']} ({data['confidence']:.2f})")
            st.write(data['response'])

elif page == "Memory":
    st.header("Memory")
    sub = st.radio("Mode", ["Store", "Search"])
    if sub == "Store":
        text = st.text_area("Text to store")
        if st.button("Store") and text:
            res = api_post("/store", {"text": text})
            if res:
                st.success(f"Stored with id {res['id']}")
    else:
        query = st.text_input("Search")
        top_k = st.number_input("Top K", 1, 10, 3)
        if st.button("Search") and query:
            res = api_post("/search", {"text": query, "top_k": int(top_k)})
            if res:
                for item in res:
                    st.write(item)

elif page == "Plugins":
    st.header("Plugin Management")
    if st.button("Reload Plugins"):
        api_post("/plugins/reload")
    plugins = api_get("/plugins") or []
    for p in plugins:
        st.write(f"### {p}")
        if st.expander("Show manifest", expanded=False):
            manifest = api_get(f"/plugins/{p}")
            st.json(manifest)

else:
    st.header("Metrics")
    metrics = api_get("/metrics")
    if metrics:
        st.json(metrics)
