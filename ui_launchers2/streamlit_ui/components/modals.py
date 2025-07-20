"""
Modal dialog components for the Streamlit UI
"""

import streamlit as st


def render_modal_dialog(title: str, content: str, show: bool = False):
    """Render modal dialog using Streamlit components"""
    if show:
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            ">
                <h3>{title}</h3>
                <p>{content}</p>
                <button onclick="closeModal()" style="
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                ">Close</button>
            </div>
        </div>
        <script>
        function closeModal() {{
            document.querySelector('[data-testid="stMarkdownContainer"]').style.display = 'none';
        }}
        </script>
        """, unsafe_allow_html=True)


def render_drag_drop_interface():
    """Drag and drop interface for file uploads and data management"""
    st.subheader("📁 Drag & Drop Interface")
    
    # File uploader with drag-and-drop
    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        accept_multiple_files=True,
        type=['csv', 'json', 'txt', 'xlsx'],
        help="Drag and drop multiple files for batch processing"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        
        for file in uploaded_files:
            with st.expander(f"📄 {file.name}"):
                file_details = {
                    "Filename": file.name,
                    "File size": f"{file.size} bytes",
                    "File type": file.type
                }
                st.json(file_details)
                
                # Show preview for CSV files
                if file.name.endswith('.csv'):
                    try:
                        import pandas as pd
                        df = pd.read_csv(file)
                        st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error reading CSV: {e}")
    
    # Sortable list interface (simulated)
    st.markdown("### 🔄 Sortable Task List")
    
    if 'task_list' not in st.session_state:
        st.session_state.task_list = [
            "📊 Generate monthly report",
            "🔧 Update system configuration", 
            "📧 Send notification emails",
            "🧹 Clean up temporary files",
            "📈 Analyze user metrics"
        ]
    
    # Display tasks with move buttons
    for i, task in enumerate(st.session_state.task_list):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"{i+1}. {task}")
        
        with col2:
            if st.button("⬆️", key=f"up_{i}", disabled=i==0):
                # Move task up
                st.session_state.task_list[i], st.session_state.task_list[i-1] = \
                    st.session_state.task_list[i-1], st.session_state.task_list[i]
                st.rerun()
        
        with col3:
            if st.button("⬇️", key=f"down_{i}", disabled=i==len(st.session_state.task_list)-1):
                # Move task down
                st.session_state.task_list[i], st.session_state.task_list[i+1] = \
                    st.session_state.task_list[i+1], st.session_state.task_list[i]
                st.rerun()
        
        with col4:
            if st.button("🗑️", key=f"delete_{i}"):
                # Delete task
                st.session_state.task_list.pop(i)
                st.rerun()