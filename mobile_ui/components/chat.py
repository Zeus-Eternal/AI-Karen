import streamlit as st


def render_chat():
    st.title("\U0001F4AC Chat with Kari")

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("\U0001F9E0 Recall Memory"):
            st.info("Memory recall not implemented.")
        if st.button("\U0001F4DC Show Logs"):
            st.info("Log viewer coming soon.")

    with col1:
        show_prompt = st.checkbox("Show system prompt", value=False)
        if show_prompt:
            st.expander("System Prompt").write("Placeholder system prompt.")

        user_input = st.chat_input("Type your message")
        if user_input:
            st.chat_message("user").write(user_input)
            # TODO: integrate with Kari backend
            st.chat_message("assistant").write("\u26A1 Response from Kari goes here.")

