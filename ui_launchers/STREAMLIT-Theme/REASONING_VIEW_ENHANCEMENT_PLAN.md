# Reasoning View Enhancement Plan

## Overview
This document outlines the plan for improving the reasoning view with structured traces in the Kari AI Lite Streamlit Console. The goal is to create a more informative and visually appealing reasoning display that provides better visibility into the AI's thought process and decision-making.

## Current State Analysis
The current implementation has a basic reasoning view:
- Simple text display of reasoning steps
- Limited visualization of reasoning process
- No interactive elements or controls
- Basic metadata display
- No reasoning timeline or history
- Limited filtering and search capabilities

## Implementation Plan

### 1. Structured Reasoning Display

#### 1.1 Visual Reasoning Hierarchy
- Implement distinct visual styles for different reasoning types
- Create visual grouping for related reasoning steps
- Add visual emphasis for important reasoning steps
- Implement reasoning status indicators

#### 1.2 Advanced Reasoning Components
- Add reasoning step icons and badges
- Implement reasoning step expansion/collapse
- Create reasoning step connections and flow
- Include reasoning step dependencies

#### 1.3 Interactive Reasoning Features
- Implement reasoning step actions (expand, collapse, focus)
- Add reasoning step filtering and search
- Create reasoning step highlighting and emphasis
- Include reasoning step export capabilities

### 2. Reasoning Timeline Visualization

#### 2.1 Timeline Layout
- Implement horizontal and vertical timeline options
- Create timeline zoom and pan controls
- Add timeline bookmarks and markers
- Include timeline navigation controls

#### 2.2 Timeline Elements
- Add reasoning step timing indicators
- Create reasoning step duration displays
- Implement reasoning step overlap visualization
- Include reasoning step parallel processing indicators

#### 2.3 Timeline Interactions
- Implement timeline click and hover interactions
- Add timeline step selection and focus
- Create timeline step comparison features
- Include timeline step context menus

### 3. Reasoning Confidence Indicators

#### 3.1 Confidence Visualization
- Implement confidence score displays
- Create confidence trend visualization
- Add confidence comparison indicators
- Include confidence uncertainty visualization

#### 3.2 Confidence Analysis
- Implement confidence breakdown by reasoning type
- Create confidence factor identification
- Add confidence improvement suggestions
- Include confidence history tracking

#### 3.3 Confidence Controls
- Implement confidence threshold controls
- Add confidence filtering options
- Create confidence highlighting features
- Include confidence alert mechanisms

### 4. Reasoning Step Details

#### 4.1 Detailed Step Information
- Implement step input/output displays
- Create step parameter and setting displays
- Add step performance metrics
- Include step error and exception handling

#### 4.2 Step Context Information
- Implement step context and background
- Create step dependency visualization
- Add step alternative paths
- Include step decision points

#### 4.3 Step Analysis Features
- Implement step comparison tools
- Create step improvement suggestions
- Add step validation and verification
- Include step documentation and references

### 5. Implementation Details

#### 5.1 Enhanced CSS Styling

```css
/* Enhanced reasoning view styling */
.enhanced-reasoning-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    background-color: rgba(26, 26, 46, 0.4);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.reasoning-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.reasoning-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
}

.reasoning-controls {
    display: flex;
    gap: 0.5rem;
}

.reasoning-control-button {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.reasoning-control-button:hover {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.reasoning-timeline {
    position: relative;
    margin: 1rem 0;
    padding: 1rem 0;
}

.timeline-container {
    position: relative;
    height: 100px;
    overflow-x: auto;
    overflow-y: hidden;
    border-radius: 4px;
    background-color: rgba(15, 15, 27, 0.6);
}

.timeline-track {
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 2px;
    background-color: var(--border-color);
    transform: translateY(-50%);
}

.timeline-step {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: var(--primary-neon);
    box-shadow: 0 0 8px rgba(0, 255, 255, 0.6);
    cursor: pointer;
    transition: all 0.2s ease;
}

.timeline-step:hover {
    width: 16px;
    height: 16px;
    box-shadow: 0 0 12px rgba(0, 255, 255, 0.8);
}

.timeline-step.active {
    background-color: var(--secondary-neon);
    box-shadow: 0 0 12px rgba(255, 0, 255, 0.8);
}

.timeline-step-label {
    position: absolute;
    top: -30px;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: 0.75rem;
    color: var(--text-secondary);
    background-color: rgba(15, 15, 27, 0.8);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    opacity: 0;
    transition: opacity 0.2s ease;
}

.timeline-step:hover .timeline-step-label {
    opacity: 1;
}

.timeline-controls {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.reasoning-steps {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-height: 400px;
    overflow-y: auto;
    padding-right: 0.5rem;
}

.reasoning-step {
    background-color: rgba(15, 15, 27, 0.6);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    padding: 1rem;
    transition: all 0.2s ease;
}

.reasoning-step:hover {
    border-color: var(--primary-neon);
    box-shadow: 0 0 8px rgba(0, 255, 255, 0.2);
}

.reasoning-step.active {
    border-color: var(--secondary-neon);
    box-shadow: 0 0 8px rgba(255, 0, 255, 0.2);
}

.reasoning-step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.reasoning-step-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.reasoning-step-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
}

.reasoning-step-type {
    background-color: rgba(0, 255, 255, 0.1);
    color: var(--primary-neon);
    border: 1px solid var(--primary-neon);
    border-radius: 12px;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    white-space: nowrap;
}

.reasoning-step-duration {
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.reasoning-step-confidence {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.confidence-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    min-width: 80px;
}

.confidence-bar {
    flex: 1;
    height: 6px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
    position: relative;
}

.confidence-value {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

.confidence-value.high {
    background: linear-gradient(90deg, #00FF00, rgba(0, 255, 0, 0.5));
}

.confidence-value.medium {
    background: linear-gradient(90deg, #FFFF00, rgba(255, 255, 0, 0.5));
}

.confidence-value.low {
    background: linear-gradient(90deg, #FF0000, rgba(255, 0, 0, 0.5));
}

.confidence-percentage {
    font-size: 0.75rem;
    color: var(--text-secondary);
    min-width: 40px;
    text-align: right;
}

.reasoning-step-content {
    margin-top: 0.5rem;
    color: var(--text-primary);
    font-size: 0.9rem;
    line-height: 1.4;
}

.reasoning-step-details {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    display: none;
}

.reasoning-step.expanded .reasoning-step-details {
    display: block;
}

.reasoning-step-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 0.5rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.reasoning-step:hover .reasoning-step-actions {
    opacity: 1;
}

.reasoning-step-action {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.reasoning-step-action:hover {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.reasoning-filters {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.reasoning-filter {
    background-color: rgba(15, 15, 27, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.reasoning-filter:hover {
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.reasoning-filter.active {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.reasoning-search {
    margin-bottom: 1rem;
}

.reasoning-summary {
    background-color: rgba(15, 15, 27, 0.6);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    padding: 1rem;
    margin-bottom: 1rem;
}

.reasoning-summary-title {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.reasoning-summary-stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.reasoning-stat {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.reasoning-stat-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.reasoning-stat-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
}

.reasoning-dependencies {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.reasoning-dependency {
    background-color: rgba(15, 15, 27, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.reasoning-alternatives {
    margin-top: 0.5rem;
}

.reasoning-alternatives-title {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
}

.reasoning-alternative {
    background-color: rgba(15, 15, 27, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    margin-bottom: 0.25rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.reasoning-alternative-score {
    font-size: 0.75rem;
    color: var(--text-secondary);
    background-color: rgba(0, 255, 255, 0.1);
    border-radius: 4px;
    padding: 0.125rem 0.375rem;
}

.reasoning-input-output {
    margin-top: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.reasoning-input, .reasoning-output {
    background-color: rgba(15, 15, 27, 0.8);
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.8rem;
}

.reasoning-input-title, .reasoning-output-title {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
}

.reasoning-input-content, .reasoning-output-content {
    color: var(--text-primary);
    font-family: monospace;
    white-space: pre-wrap;
    word-break: break-word;
}

.reasoning-error {
    background-color: rgba(255, 0, 0, 0.1);
    border: 1px solid #FF0000;
    border-radius: 4px;
    padding: 0.5rem;
    margin-top: 0.5rem;
    color: #FF6B6B;
    font-size: 0.8rem;
}

.reasoning-error-title {
    font-weight: 600;
    margin-bottom: 0.25rem;
}
```

#### 5.2 Enhanced Reasoning Components

```python
# Enhanced reasoning view rendering
def render_enhanced_reasoning_view():
    """Render enhanced reasoning view with structured traces"""
    st.markdown(
        '<div class="enhanced-reasoning-container">',
        unsafe_allow_html=True
    )
    
    # Reasoning header
    st.markdown(
        '<div class="reasoning-header">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="reasoning-title">Reasoning Process</div>',
        unsafe_allow_html=True
    )
    
    # Reasoning controls
    st.markdown(
        '<div class="reasoning-controls">',
        unsafe_allow_html=True
    )
    
    control_cols = st.columns(4)
    
    with control_cols[0]:
        if st.button("🔄 Refresh", key="refresh_reasoning", help="Refresh reasoning data"):
            # Implement reasoning refresh
            pass
    
    with control_cols[1]:
        if st.button("📋 Copy", key="copy_reasoning", help="Copy reasoning to clipboard"):
            # Implement reasoning copy
            pass
    
    with control_cols[2]:
        if st.button("💾 Save", key="save_reasoning", help="Save reasoning data"):
            # Implement reasoning save
            pass
    
    with control_cols[3]:
        if st.button("🔍 Analyze", key="analyze_reasoning", help="Analyze reasoning process"):
            # Implement reasoning analysis
            pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-controls
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-header
    
    # Reasoning summary
    render_reasoning_summary()
    
    # Reasoning filters
    render_reasoning_filters()
    
    # Reasoning search
    render_reasoning_search()
    
    # Reasoning timeline
    render_reasoning_timeline()
    
    # Reasoning steps
    render_reasoning_steps()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-reasoning-container

def render_reasoning_summary():
    """Render reasoning summary with statistics"""
    st.markdown(
        '<div class="reasoning-summary">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="reasoning-summary-title">Reasoning Summary</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="reasoning-summary-stats">',
        unsafe_allow_html=True
    )
    
    # Get reasoning summary data
    summary_data = get_reasoning_summary_data()
    
    # Display statistics
    stat_cols = st.columns(5)
    
    with stat_cols[0]:
        st.markdown(
            '<div class="reasoning-stat">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="reasoning-stat-label">Total Steps</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="reasoning-stat-value">{summary_data["total_steps"]}</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_cols[1]:
        st.markdown(
            '<div class="reasoning-stat">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="reasoning-stat-label">Duration</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="reasoning-stat-value">{summary_data["duration"]:.2f}s</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_cols[2]:
        st.markdown(
            '<div class="reasoning-stat">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="reasoning-stat-label">Avg. Confidence</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="reasoning-stat-value">{summary_data["avg_confidence"]:.1f}%</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_cols[3]:
        st.markdown(
            '<div class="reasoning-stat">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="reasoning-stat-label">Success Rate</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="reasoning-stat-value">{summary_data["success_rate"]:.1f}%</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_cols[4]:
        st.markdown(
            '<div class="reasoning-stat">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="reasoning-stat-label">Parallel Steps</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="reasoning-stat-value">{summary_data["parallel_steps"]}</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-summary-stats
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-summary

def get_reasoning_summary_data():
    """Get reasoning summary data for display"""
    # This would be replaced with actual data from backend
    # For now, we'll use simulated data
    return {
        "total_steps": 8,
        "duration": 3.45,
        "avg_confidence": 87.5,
        "success_rate": 100.0,
        "parallel_steps": 2
    }

def render_reasoning_filters():
    """Render reasoning filters"""
    st.markdown(
        '<div class="reasoning-filters">',
        unsafe_allow_html=True
    )
    
    # Filter options
    filter_options = [
        {"key": "all", "label": "All Steps"},
        {"key": "high_confidence", "label": "High Confidence"},
        {"key": "medium_confidence", "label": "Medium Confidence"},
        {"key": "low_confidence", "label": "Low Confidence"},
        {"key": "errors", "label": "Errors"},
        {"key": "parallel", "label": "Parallel"}
    ]
    
    # Initialize filter state
    if 'reasoning_filters' not in st.session_state:
        st.session_state.reasoning_filters = {"all": True}
    
    # Render filters
    for i, filter_option in enumerate(filter_options):
        filter_key = filter_option["key"]
        filter_label = filter_option["label"]
        
        # Check if filter is active
        is_active = st.session_state.reasoning_filters.get(filter_key, False)
        
        # Toggle filter on click
        if st.button(filter_label, key=f"filter_{filter_key}"):
            # Toggle filter
            st.session_state.reasoning_filters[filter_key] = not is_active
            
            # If "All Steps" is selected, deselect other filters
            if filter_key == "all" and is_active == False:
                for key in st.session_state.reasoning_filters:
                    if key != "all":
                        st.session_state.reasoning_filters[key] = False
            # If any other filter is selected, deselect "All Steps"
            elif filter_key != "all" and is_active == False:
                st.session_state.reasoning_filters["all"] = False
            
            st.rerun()
        
        # Apply active filter styling
        if is_active:
            st.markdown(
                f'<style>div[data-testid="stButton"] > button[kind="secondary"][data-testid="baseButton-secondary"]:nth-child({i+1}) {{ background-color: rgba(0, 255, 255, 0.1); border-color: var(--primary-neon); color: var(--primary-neon); }}</style>',
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-filters

def render_reasoning_search():
    """Render reasoning search"""
    st.markdown(
        '<div class="reasoning-search">',
        unsafe_allow_html=True
    )
    
    # Search input
    search_query = st.text_input(
        "Search reasoning steps",
        key="reasoning_search",
        placeholder="Search by step name, type, or content...",
        help="Filter reasoning steps by search query"
    )
    
    # Update search state
    if 'reasoning_search_query' not in st.session_state:
        st.session_state.reasoning_search_query = ""
    
    if search_query != st.session_state.reasoning_search_query:
        st.session_state.reasoning_search_query = search_query
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-search

def render_reasoning_timeline():
    """Render reasoning timeline"""
    st.markdown(
        '<div class="reasoning-timeline">',
        unsafe_allow_html=True
    )
    
    # Timeline container
    st.markdown(
        '<div class="timeline-container">',
        unsafe_allow_html=True
    )
    
    # Timeline track
    st.markdown(
        '<div class="timeline-track"></div>',
        unsafe_allow_html=True
    )
    
    # Get reasoning steps data
    reasoning_steps = get_reasoning_steps_data()
    
    # Calculate timeline positions
    total_duration = max([step["end_time"] for step in reasoning_steps]) if reasoning_steps else 1
    
    # Render timeline steps
    for i, step in enumerate(reasoning_steps):
        # Calculate position (0-100%)
        position = (step["start_time"] / total_duration) * 100
        
        # Determine step class
        step_class = "timeline-step"
        if 'active_step' in st.session_state and st.session_state.active_step == i:
            step_class += " active"
        
        # Render step
        st.markdown(
            f'<div class="{step_class}" style="left: {position}%;" onclick="setActiveReasoningStep({i})">',
            unsafe_allow_html=True
        )
        
        # Step label
        st.markdown(
            f'<div class="timeline-step-label">{step["name"]}</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close timeline-container
    
    # Timeline controls
    st.markdown(
        '<div class="timeline-controls">',
        unsafe_allow_html=True
    )
    
    control_cols = st.columns(3)
    
    with control_cols[0]:
        if st.button("⏮️ Start", key="timeline_start", help="Go to start of timeline"):
            # Implement timeline start
            if reasoning_steps:
                st.session_state.active_step = 0
                st.rerun()
    
    with control_cols[1]:
        if st.button("⏯️ Play/Pause", key="timeline_play_pause", help="Play/pause timeline"):
            # Implement timeline play/pause
            pass
    
    with control_cols[2]:
        if st.button("⏭️ End", key="timeline_end", help="Go to end of timeline"):
            # Implement timeline end
            if reasoning_steps:
                st.session_state.active_step = len(reasoning_steps) - 1
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close timeline-controls
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-timeline

def render_reasoning_steps():
    """Render reasoning steps"""
    st.markdown(
        '<div class="reasoning-steps">',
        unsafe_allow_html=True
    )
    
    # Get reasoning steps data
    reasoning_steps = get_reasoning_steps_data()
    
    # Get active step
    active_step = st.session_state.get('active_step', None)
    
    # Render steps
    for i, step in enumerate(reasoning_steps):
        # Check if step should be displayed based on filters
        if not should_display_step(step):
            continue
        
        # Check if step matches search query
        if 'reasoning_search_query' in st.session_state and st.session_state.reasoning_search_query:
            search_query = st.session_state.reasoning_search_query.lower()
            step_text = f"{step['name']} {step['type']} {step['content']}".lower()
            if search_query not in step_text:
                continue
        
        # Determine step class
        step_class = "reasoning-step"
        if active_step == i:
            step_class += " active"
        if f"step_expanded_{i}" in st.session_state and st.session_state[f"step_expanded_{i}"]:
            step_class += " expanded"
        
        # Render step
        st.markdown(
            f'<div class="{step_class}" id="reasoning_step_{i}">',
            unsafe_allow_html=True
        )
        
        # Step header
        st.markdown(
            '<div class="reasoning-step-header">',
            unsafe_allow_html=True
        )
        
        # Step title
        st.markdown(
            '<div class="reasoning-step-title">',
            unsafe_allow_html=True
        )
        
        # Step icon
        icon = get_step_icon(step["type"])
        icon_color = get_step_icon_color(step["type"])
        st.markdown(
            f'<div class="reasoning-step-icon" style="background-color: {icon_color};">{icon}</div>',
            unsafe_allow_html=True
        )
        
        # Step name
        st.markdown(
            f'<div>{step["name"]}</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step-title
        
        # Step type
        st.markdown(
            f'<div class="reasoning-step-type">{step["type"]}</div>',
            unsafe_allow_html=True
        )
        
        # Step duration
        duration = step["end_time"] - step["start_time"]
        st.markdown(
            f'<div class="reasoning-step-duration">⏱️ {duration:.2f}s</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step-header
        
        # Step confidence
        confidence = step.get("confidence", 0)
        confidence_class = "high" if confidence >= 80 else "medium" if confidence >= 50 else "low"
        
        st.markdown(
            '<div class="reasoning-step-confidence">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="confidence-label">Confidence</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="confidence-bar">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            f'<div class="confidence-value {confidence_class}" style="width: {confidence}%;"></div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close confidence-bar
        
        st.markdown(
            f'<div class="confidence-percentage">{confidence:.0f}%</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step-confidence
        
        # Step content
        st.markdown(
            f'<div class="reasoning-step-content">{step["content"]}</div>',
            unsafe_allow_html=True
        )
        
        # Step details (initially hidden)
        st.markdown(
            '<div class="reasoning-step-details">',
            unsafe_allow_html=True
        )
        
        # Step dependencies
        if "dependencies" in step and step["dependencies"]:
            st.markdown(
                '<div class="reasoning-dependencies">',
                unsafe_allow_html=True
            )
            
            st.markdown(
                '<div class="reasoning-step-title">Dependencies</div>',
                unsafe_allow_html=True
            )
            
            for dep in step["dependencies"]:
                st.markdown(
                    f'<div class="reasoning-dependency">🔗 {dep}</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-dependencies
        
        # Step alternatives
        if "alternatives" in step and step["alternatives"]:
            st.markdown(
                '<div class="reasoning-alternatives">',
                unsafe_allow_html=True
            )
            
            st.markdown(
                '<div class="reasoning-alternatives-title">Alternatives</div>',
                unsafe_allow_html=True
            )
            
            for alt in step["alternatives"]:
                st.markdown(
                    '<div class="reasoning-alternative">',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f'<div>{alt["name"]}</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f'<div class="reasoning-alternative-score">{alt["score"]:.0f}%</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-alternatives
        
        # Step input/output
        if "input" in step or "output" in step:
            st.markdown(
                '<div class="reasoning-input-output">',
                unsafe_allow_html=True
            )
            
            # Input
            if "input" in step:
                st.markdown(
                    '<div class="reasoning-input">',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    '<div class="reasoning-input-title">Input</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f'<div class="reasoning-input-content">{step["input"]}</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-input
            
            # Output
            if "output" in step:
                st.markdown(
                    '<div class="reasoning-output">',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    '<div class="reasoning-output-title">Output</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f'<div class="reasoning-output-content">{step["output"]}</div>',
                    unsafe_allow_html=True
                )
                
                st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-output
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-input-output
        
        # Step error
        if "error" in step:
            st.markdown(
                '<div class="reasoning-error">',
                unsafe_allow_html=True
            )
            
            st.markdown(
                '<div class="reasoning-error-title">Error</div>',
                unsafe_allow_html=True
            )
            
            st.markdown(
                f'<div>{step["error"]}</div>',
                unsafe_allow_html=True
            )
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-error
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step-details
        
        # Step actions
        st.markdown(
            '<div class="reasoning-step-actions">',
            unsafe_allow_html=True
        )
        
        action_cols = st.columns(4)
        
        with action_cols[0]:
            expanded = f"step_expanded_{i}" in st.session_state and st.session_state[f"step_expanded_{i}"]
            expand_label = "Collapse" if expanded else "Expand"
            if st.button(expand_label, key=f"expand_step_{i}", help=f"{expand_label} step details"):
                st.session_state[f"step_expanded_{i}"] = not expanded
                st.rerun()
        
        with action_cols[1]:
            if st.button("🔍 Focus", key=f"focus_step_{i}", help="Focus on this step"):
                st.session_state.active_step = i
                st.rerun()
        
        with action_cols[2]:
            if st.button("📋 Copy", key=f"copy_step_{i}", help="Copy step details"):
                # Implement step copy
                pass
        
        with action_cols[3]:
            if st.button("🔗 Link", key=f"link_step_{i}", help="Get link to this step"):
                # Implement step link
                pass
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step-actions
        st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-step
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close reasoning-steps

def get_reasoning_steps_data():
    """Get reasoning steps data for display"""
    # This would be replaced with actual data from backend
    # For now, we'll use simulated data
    return [
        {
            "name": "Analyze User Query",
            "type": "Analysis",
            "content": "Understanding the user's question about the current weather conditions",
            "start_time": 0.0,
            "end_time": 0.5,
            "confidence": 95,
            "dependencies": [],
            "input": "What's the weather like today?",
            "output": "Weather query identified"
        },
        {
            "name": "Check Weather Plugin",
            "type": "Plugin",
            "content": "Invoking weather plugin to get current weather data",
            "start_time": 0.5,
            "end_time": 1.2,
            "confidence": 90,
            "dependencies": ["Analyze User Query"],
            "input": "Weather plugin request",
            "output": "Weather data received"
        },
        {
            "name": "Process Weather Data",
            "type": "Processing",
            "content": "Processing and formatting weather data for user presentation",
            "start_time": 1.2,
            "end_time": 1.8,
            "confidence": 85,
            "dependencies": ["Check Weather Plugin"],
            "input": "Raw weather data",
            "output": "Formatted weather information"
        },
        {
            "name": "Generate Response",
            "type": "Generation",
            "content": "Creating natural language response based on processed weather data",
            "start_time": 1.8,
            "end_time": 2.5,
            "confidence": 80,
            "dependencies": ["Process Weather Data"],
            "input": "Formatted weather information",
            "output": "Natural language response"
        },
        {
            "name": "Validate Response",
            "type": "Validation",
            "content": "Validating response for accuracy and completeness",
            "start_time": 2.5,
            "end_time": 2.8,
            "confidence": 95,
            "dependencies": ["Generate Response"],
            "input": "Natural language response",
            "output": "Validation results"
        },
        {
            "name": "Finalize Response",
            "type": "Finalization",
            "content": "Finalizing response with additional context and formatting",
            "start_time": 2.8,
            "end_time": 3.0,
            "confidence": 90,
            "dependencies": ["Validate Response"],
            "input": "Validated response",
            "output": "Final response"
        },
        {
            "name": "Memory Update",
            "type": "Memory",
            "content": "Updating memory with conversation context for future reference",
            "start_time": 3.0,
            "end_time": 3.2,
            "confidence": 85,
            "dependencies": ["Finalize Response"],
            "input": "Conversation data",
            "output": "Memory update status"
        },
        {
            "name": "Performance Metrics",
            "type": "Metrics",
            "content": "Calculating performance metrics for this interaction",
            "start_time": 3.2,
            "end_time": 3.45,
            "confidence": 95,
            "dependencies": ["Memory Update"],
            "input": "Interaction data",
            "output": "Performance metrics"
        }
    ]

def should_display_step(step):
    """Check if step should be displayed based on active filters"""
    # If no filters are active, display all steps
    if not any(st.session_state.reasoning_filters.values()):
        return True
    
    # If "All Steps" filter is active, display all steps
    if st.session_state.reasoning_filters.get("all", False):
        return True
    
    # Check step against active filters
    confidence = step.get("confidence", 0)
    
    # High confidence filter
    if st.session_state.reasoning_filters.get("high_confidence", False) and confidence >= 80:
        return True
    
    # Medium confidence filter
    if st.session_state.reasoning_filters.get("medium_confidence", False) and 50 <= confidence < 80:
        return True
    
    # Low confidence filter
    if st.session_state.reasoning_filters.get("low_confidence", False) and confidence < 50:
        return True
    
    # Errors filter
    if st.session_state.reasoning_filters.get("errors", False) and "error" in step:
        return True
    
    # Parallel filter
    if st.session_state.reasoning_filters.get("parallel", False) and step.get("parallel", False):
        return True
    
    # Step doesn't match any active filters
    return False

def get_step_icon(step_type):
    """Get icon for reasoning step type"""
    icons = {
        "Analysis": "🔍",
        "Plugin": "🔌",
        "Processing": "⚙️",
        "Generation": "✨",
        "Validation": "✅",
        "Finalization": "🎯",
        "Memory": "🧠",
        "Metrics": "📊"
    }
    return icons.get(step_type, "❓")

def get_step_icon_color(step_type):
    """Get icon color for reasoning step type"""
    colors = {
        "Analysis": "rgba(0, 255, 255, 0.2)",
        "Plugin": "rgba(255, 0, 255, 0.2)",
        "Processing": "rgba(255, 255, 0, 0.2)",
        "Generation": "rgba(0, 255, 0, 0.2)",
        "Validation": "rgba(0, 255, 255, 0.2)",
        "Finalization": "rgba(255, 0, 255, 0.2)",
        "Memory": "rgba(255, 255, 0, 0.2)",
        "Metrics": "rgba(0, 255, 0, 0.2)"
    }
    return colors.get(step_type, "rgba(255, 255, 255, 0.2)")
```

### 6. Integration with Existing Components

#### 6.1 Update Reasoning Zone

```python
# Enhanced reasoning zone
def render_enhanced_reasoning_zone():
    """Render enhanced reasoning interface with improved visualization and features"""
    st.markdown("## Reasoning & Analysis")
    
    # Initialize reasoning state
    if 'active_step' not in st.session_state:
        st.session_state.active_step = None
    
    if 'reasoning_filters' not in st.session_state:
        st.session_state.reasoning_filters = {"all": True}
    
    if 'reasoning_search_query' not in st.session_state:
        st.session_state.reasoning_search_query = ""
    
    # Render enhanced reasoning view
    render_enhanced_reasoning_view()
```

#### 6.2 Update CSS

```python
# Add enhanced reasoning view CSS to load_neon_theme function
def load_neon_theme():
    # Existing CSS...
    
    # Add enhanced reasoning view CSS
    enhanced_reasoning_css = """
    /* Enhanced reasoning view CSS from section 5.1 */
    """
    
    # Combine with existing CSS
    neon_css += enhanced_reasoning_css
    st.markdown(neon_css, unsafe_allow_html=True)
```

### 7. Environment Configuration Updates

#### 7.1 Update .env.example

```bash
# Kari AI Streamlit Console Environment Configuration

# Backend API Configuration
KARI_BACKEND_URL=http://localhost:8000/api

# Authentication (if needed)
KARI_API_KEY=your_api_key_here

# Default Settings
DEFAULT_MODEL=llama-cpp-7B
DEFAULT_MODEL_TYPE=local
DEFAULT_REASONING_MODE=Standard

# Plugin Defaults
DEFAULT_PLUGINS_SEARCH=true
DEFAULT_PLUGINS_MEMORY=true
DEFAULT_PLUGINS_TOOLS=true
DEFAULT_PLUGINS_WEATHER=false

# Chat UI Defaults
DEFAULT_AUTO_RESIZE_INPUT=true
DEFAULT_INPUT_HEIGHT=100
DEFAULT_MAX_INPUT_HEIGHT=300
DEFAULT_STREAMING_SPEED=1.0
DEFAULT_ENABLE_STREAMING_CONTROLS=true
DEFAULT_SHOW_MESSAGE_ACTIONS=true
DEFAULT_SHOW_MESSAGE_METADATA=true
DEFAULT_ENABLE_MESSAGE_FORMATTING=true

# Reasoning View Defaults
DEFAULT_REASONING_VIEW_LAYOUT=steps
DEFAULT_REASONING_VIEW_TIMELINE=true
DEFAULT_REASONING_VIEW_CONFIDENCE=true
DEFAULT_REASONING_VIEW_FILTERS=true
DEFAULT_REASONING_VIEW_SEARCH=true
DEFAULT_REASONING_STEP_EXPANDED=false
DEFAULT_REASONING_STEP_DETAILS=true
DEFAULT_REASONING_STEP_DEPENDENCIES=true
DEFAULT_REASONING_STEP_ALTERNATIVES=true
DEFAULT_REASONING_STEP_INPUT_OUTPUT=true

# Debug and Development
DEBUG_MODE=false
LOG_LEVEL=INFO

# User Configuration (for development)
DEFAULT_USER_ID=dev_user
DEFAULT_USER_ROLE=Creator

# Performance Settings
MAX_CONVERSATION_HISTORY=50
RESPONSE_TIMEOUT=30
MAX_REASONING_STEPS=50
REASONING_STEP_CACHE_SIZE=100
```

### 8. Testing Strategy

#### 8.1 Unit Testing
- Test reasoning step rendering functionality
- Test timeline visualization components
- Test confidence indicator displays
- Test filtering and search functionality

#### 8.2 Integration Testing
- Test reasoning step interactions
- Test timeline navigation controls
- Test filter and search combinations
- Test step detail expansion/collapse

#### 8.3 User Acceptance Testing
- Test overall reasoning view usability
- Test reasoning process visualization
- Test step interaction patterns
- Test filtering and search effectiveness

### 9. Success Metrics

1. **Reasoning View Engagement**:
   - Reasoning step expansion rate
   - Timeline interaction frequency
   - Filter and search usage rate
   - Step detail view duration

2. **Reasoning Process Understanding**:
   - User comprehension of reasoning process
   - Confidence indicator effectiveness
   - Step dependency understanding
   - Alternative path exploration rate

3. **Performance and Efficiency**:
   - Reasoning view load time
   - Step rendering performance
   - Filter and search response time
   - Timeline interaction responsiveness

### 10. Rollout Plan

#### 10.1 Phase 1: Basic Enhancements
- Implement enhanced reasoning step styling
- Add basic timeline visualization
- Include confidence indicators

#### 10.2 Phase 2: Advanced Features
- Add reasoning step details and interactions
- Implement filtering and search functionality
- Include step dependencies and alternatives

#### 10.3 Phase 3: Optimization
- Add performance optimizations
- Implement accessibility features
- Include user preference controls

## Conclusion

This plan outlines a comprehensive approach to improving the reasoning view with structured traces in Kari AI Lite Streamlit Console. By implementing these features, we'll create a more informative and visually appealing reasoning display that provides better visibility into the AI's thought process and decision-making.

The implementation will be done in phases, starting with basic reasoning step styling enhancements, then moving to more advanced features like timeline visualization and filtering functionality.