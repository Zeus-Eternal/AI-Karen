# Personal Context Enhancement Plan

## Overview
This document outlines the plan for enhancing the personal context display in the Kari AI Lite Streamlit Console. The goal is to create a more informative and visually appealing personal context interface that provides better visibility into the user's personal information, preferences, and relevant context for the AI to use in conversations.

## Current State Analysis
The current implementation has a basic personal context display:
- Simple text display of user information
- Limited visualization of personal data
- No interactive elements or controls
- Basic filtering and search capabilities
- No context relevance indicators
- Limited context refresh mechanisms

## Implementation Plan

### 1. Real Data Fetching

#### 1.1 Data Source Integration
- Implement connection to user database
- Create data fetching mechanisms
- Add data caching strategies
- Include data error handling

#### 1.2 Data Transformation
- Implement data normalization
- Create data enrichment processes
- Add data validation
- Include data privacy controls

#### 1.3 Data Synchronization
- Implement real-time data updates
- Create data change notifications
- Add data conflict resolution
- Include data versioning

### 2. Context Filtering

#### 2.1 Filter Categories
- Implement context type filters
- Create relevance level filters
- Add time-based filters
- Include source-based filters

#### 2.2 Filter Controls
- Implement filter selection interface
- Create filter preset management
- Add filter combination logic
- Include filter save/load functionality

#### 2.3 Filter Visualization
- Implement filter result indicators
- Create filter summary displays
- Add filter comparison features
- Include filter history tracking

### 3. Relevance Indicators

#### 3.1 Relevance Scoring
- Implement relevance calculation algorithms
- Create relevance weighting factors
- Add relevance threshold controls
- Include relevance customization

#### 3.2 Relevance Visualization
- Implement relevance score displays
- Create relevance color coding
- Add relevance trend indicators
- Include relevance comparison features

#### 3.3 Relevance Analysis
- Implement relevance factor breakdown
- Create relevance improvement suggestions
- Add relevance feedback mechanisms
- Include relevance learning capabilities

### 4. Refresh Mechanisms

#### 4.1 Manual Refresh
- Implement refresh button controls
- Create refresh progress indicators
- Add refresh success notifications
- Include refresh error handling

#### 4.2 Auto Refresh
- Implement refresh interval controls
- Create background refresh processes
- Add refresh conflict resolution
- Include refresh pause/resume functionality

#### 4.3 Selective Refresh
- Implement partial refresh options
- Create refresh priority settings
- Add refresh dependency management
- Include refresh optimization

### 5. Implementation Details

#### 5.1 Enhanced CSS Styling

```css
/* Enhanced personal context styling */
.enhanced-context-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    background-color: rgba(26, 26, 46, 0.4);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    height: 100%;
    overflow: hidden;
}

.context-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.context-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
}

.context-controls {
    display: flex;
    gap: 0.5rem;
}

.context-control-button {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.context-control-button:hover {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.context-filters {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.context-filter {
    background-color: rgba(15, 15, 27, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.context-filter:hover {
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.context-filter.active {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.context-search {
    margin-bottom: 1rem;
}

.context-content {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
}

.context-category {
    margin-bottom: 1.5rem;
}

.category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.category-title {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.category-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
}

.category-count {
    font-size: 0.8rem;
    color: var(--text-secondary);
    background-color: rgba(15, 15, 27, 0.8);
    border-radius: 12px;
    padding: 0.125rem 0.5rem;
}

.category-items {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.context-item {
    background-color: rgba(15, 15, 27, 0.6);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    padding: 0.75rem;
    transition: all 0.2s ease;
}

.context-item:hover {
    border-color: var(--primary-neon);
    box-shadow: 0 0 8px rgba(0, 255, 255, 0.2);
}

.context-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.context-item-title {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
}

.context-item-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.context-item:hover .context-item-actions {
    opacity: 1;
}

.context-item-action {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 0.25rem;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.context-item-action:hover {
    background-color: rgba(0, 255, 255, 0.1);
    color: var(--primary-neon);
}

.context-item-content {
    color: var(--text-primary);
    font-size: 0.85rem;
    line-height: 1.4;
    margin-bottom: 0.5rem;
}

.context-item-metadata {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.context-metadata {
    background-color: rgba(15, 15, 27, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    white-space: nowrap;
}

.context-metadata.source {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.context-metadata.time {
    background-color: rgba(255, 255, 0, 0.1);
    border-color: #FFFF00;
    color: #FFFF00;
}

.context-metadata.type {
    background-color: rgba(255, 0, 255, 0.1);
    border-color: var(--secondary-neon);
    color: var(--secondary-neon);
}

.relevance-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.relevance-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    min-width: 80px;
}

.relevance-bar {
    flex: 1;
    height: 6px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
    position: relative;
}

.relevance-value {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

.relevance-value.high {
    background: linear-gradient(90deg, #00FF00, rgba(0, 255, 0, 0.5));
}

.relevance-value.medium {
    background: linear-gradient(90deg, #FFFF00, rgba(255, 255, 0, 0.5));
}

.relevance-value.low {
    background: linear-gradient(90deg, #FF0000, rgba(255, 0, 0, 0.5));
}

.relevance-percentage {
    font-size: 0.75rem;
    color: var(--text-secondary);
    min-width: 40px;
    text-align: right;
}

.context-refresh {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
}

.refresh-status {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.status-up-to-date {
    background-color: #00FF00;
    box-shadow: 0 0 4px rgba(0, 255, 0, 0.6);
}

.status-refreshing {
    background-color: #FFFF00;
    box-shadow: 0 0 4px rgba(255, 255, 0, 0.6);
    animation: pulse 1.5s infinite;
}

.status-error {
    background-color: #FF0000;
    box-shadow: 0 0 4px rgba(255, 0, 0, 0.6);
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}

.context-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
    text-align: center;
}

.context-empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.context-empty-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.context-empty-description {
    font-size: 0.9rem;
    max-width: 400px;
    line-height: 1.4;
}

.context-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
    text-align: center;
}

.context-loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(0, 255, 255, 0.2);
    border-top-color: var(--primary-neon);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.context-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
    text-align: center;
}

.context-error-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #FF6B6B;
}

.context-error-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #FF6B6B;
}

.context-error-description {
    font-size: 0.9rem;
    max-width: 400px;
    line-height: 1.4;
    margin-bottom: 1rem;
}

.context-error-actions {
    display: flex;
    gap: 0.5rem;
}
```

#### 5.2 Enhanced Personal Context Components

```python
# Enhanced personal context rendering
def render_enhanced_personal_context():
    """Render enhanced personal context with improved visualization and features"""
    st.markdown(
        '<div class="enhanced-context-container">',
        unsafe_allow_html=True
    )
    
    # Context header
    st.markdown(
        '<div class="context-header">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-title">Personal Context</div>',
        unsafe_allow_html=True
    )
    
    # Context controls
    st.markdown(
        '<div class="context-controls">',
        unsafe_allow_html=True
    )
    
    control_cols = st.columns(4)
    
    with control_cols[0]:
        if st.button("🔄 Refresh", key="refresh_context", help="Refresh personal context data"):
            # Implement context refresh
            refresh_personal_context()
    
    with control_cols[1]:
        if st.button("⚙️ Settings", key="context_settings", help="Configure context settings"):
            # Implement context settings
            pass
    
    with control_cols[2]:
        if st.button("🔍 Search", key="context_search_toggle", help="Toggle search"):
            # Toggle search visibility
            if 'show_context_search' not in st.session_state:
                st.session_state.show_context_search = False
            st.session_state.show_context_search = not st.session_state.show_context_search
            st.rerun()
    
    with control_cols[3]:
        if st.button("📊 Stats", key="context_stats", help="View context statistics"):
            # Implement context statistics
            pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-controls
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-header
    
    # Context filters
    render_context_filters()
    
    # Context search
    if 'show_context_search' in st.session_state and st.session_state.show_context_search:
        render_context_search()
    
    # Context content
    render_context_content()
    
    # Context refresh controls
    render_context_refresh_controls()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-context-container

def render_context_filters():
    """Render context filters"""
    st.markdown(
        '<div class="context-filters">',
        unsafe_allow_html=True
    )
    
    # Filter options
    filter_options = [
        {"key": "all", "label": "All Context"},
        {"key": "profile", "label": "Profile"},
        {"key": "preferences", "label": "Preferences"},
        {"key": "history", "label": "History"},
        {"key": "relationships", "label": "Relationships"},
        {"key": "interests", "label": "Interests"}
    ]
    
    # Initialize filter state
    if 'context_filters' not in st.session_state:
        st.session_state.context_filters = {"all": True}
    
    # Render filters
    for i, filter_option in enumerate(filter_options):
        filter_key = filter_option["key"]
        filter_label = filter_option["label"]
        
        # Check if filter is active
        is_active = st.session_state.context_filters.get(filter_key, False)
        
        # Toggle filter on click
        if st.button(filter_label, key=f"context_filter_{filter_key}"):
            # Toggle filter
            st.session_state.context_filters[filter_key] = not is_active
            
            # If "All Context" is selected, deselect other filters
            if filter_key == "all" and is_active == False:
                for key in st.session_state.context_filters:
                    if key != "all":
                        st.session_state.context_filters[key] = False
            # If any other filter is selected, deselect "All Context"
            elif filter_key != "all" and is_active == False:
                st.session_state.context_filters["all"] = False
            
            st.rerun()
        
        # Apply active filter styling
        if is_active:
            st.markdown(
                f'<style>div[data-testid="stButton"] > button[kind="secondary"][data-testid="baseButton-secondary"]:nth-child({i+1}) {{ background-color: rgba(0, 255, 255, 0.1); border-color: var(--primary-neon); color: var(--primary-neon); }}</style>',
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-filters

def render_context_search():
    """Render context search"""
    st.markdown(
        '<div class="context-search">',
        unsafe_allow_html=True
    )
    
    # Search input
    search_query = st.text_input(
        "Search personal context",
        key="context_search",
        placeholder="Search by title, content, or metadata...",
        help="Filter personal context by search query"
    )
    
    # Update search state
    if 'context_search_query' not in st.session_state:
        st.session_state.context_search_query = ""
    
    if search_query != st.session_state.context_search_query:
        st.session_state.context_search_query = search_query
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-search

def render_context_content():
    """Render context content"""
    st.markdown(
        '<div class="context-content">',
        unsafe_allow_html=True
    )
    
    # Get context data
    context_data = get_personal_context_data()
    
    # Check if context data is available
    if context_data is None:
        # Loading state
        render_context_loading()
    elif isinstance(context_data, dict) and 'error' in context_data:
        # Error state
        render_context_error(context_data['error'])
    elif not context_data or not any(context_data.values()):
        # Empty state
        render_context_empty()
    else:
        # Render context categories
        for category, items in context_data.items():
            # Check if category should be displayed based on filters
            if not should_display_category(category):
                continue
            
            # Check if any items in category match search query
            if 'context_search_query' in st.session_state and st.session_state.context_search_query:
                search_query = st.session_state.context_search_query.lower()
                matching_items = [
                    item for item in items
                    if search_query in item.get('title', '').lower() or 
                       search_query in item.get('content', '').lower() or
                       any(search_query in str(value).lower() for value in item.get('metadata', {}).values())
                ]
                if not matching_items:
                    continue
                items_to_display = matching_items
            else:
                items_to_display = items
            
            if items_to_display:
                render_context_category(category, items_to_display)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-content

def render_context_category(category, items):
    """Render a single context category"""
    # Get category info
    category_info = get_category_info(category)
    
    st.markdown(
        '<div class="context-category">',
        unsafe_allow_html=True
    )
    
    # Category header
    st.markdown(
        '<div class="category-header">',
        unsafe_allow_html=True
    )
    
    # Category title
    st.markdown(
        '<div class="category-title">',
        unsafe_allow_html=True
    )
    
    # Category icon
    icon = category_info.get('icon', '📄')
    icon_color = category_info.get('color', 'rgba(0, 255, 255, 0.2)')
    st.markdown(
        f'<div class="category-icon" style="background-color: {icon_color};">{icon}</div>',
        unsafe_allow_html=True
    )
    
    # Category name
    category_name = category_info.get('name', category.capitalize())
    st.markdown(f'<div>{category_name}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close category-title
    
    # Category count
    st.markdown(
        f'<div class="category-count">{len(items)}</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close category-header
    
    # Category items
    st.markdown(
        '<div class="category-items">',
        unsafe_allow_html=True
    )
    
    # Render items
    for item in items:
        render_context_item(item, category)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close category-items
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-category

def render_context_item(item, category):
    """Render a single context item"""
    # Get item relevance
    relevance = calculate_item_relevance(item, category)
    relevance_class = "high" if relevance >= 80 else "medium" if relevance >= 50 else "low"
    
    # Generate unique item key
    item_key = f"{category}_{item.get('id', '')}_{hash(item.get('title', '') + item.get('content', ''))}"
    
    # Check if item is expanded
    is_expanded = f"item_expanded_{item_key}" in st.session_state and st.session_state[f"item_expanded_{item_key}"]
    
    st.markdown(
        f'<div class="context-item" id="context_item_{item_key}">',
        unsafe_allow_html=True
    )
    
    # Item header
    st.markdown(
        '<div class="context-item-header">',
        unsafe_allow_html=True
    )
    
    # Item title
    st.markdown(
        f'<div class="context-item-title">{item.get("title", "Untitled")}</div>',
        unsafe_allow_html=True
    )
    
    # Item actions
    st.markdown(
        '<div class="context-item-actions">',
        unsafe_allow_html=True
    )
    
    action_cols = st.columns(3)
    
    with action_cols[0]:
        if st.button("👁️", key=f"view_item_{item_key}", help="View item details"):
            st.session_state[f"item_expanded_{item_key}"] = not is_expanded
            st.rerun()
    
    with action_cols[1]:
        if st.button("✏️", key=f"edit_item_{item_key}", help="Edit this item"):
            # Implement item editing
            pass
    
    with action_cols[2]:
        if st.button("🗑️", key=f"delete_item_{item_key}", help="Delete this item"):
            # Implement item deletion
            pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-item-actions
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-item-header
    
    # Item content
    content = item.get("content", "")
    if len(content) > 200 and not is_expanded:
        content = content[:200] + "..."
    
    st.markdown(
        f'<div class="context-item-content">{content}</div>',
        unsafe_allow_html=True
    )
    
    # Item metadata
    metadata = item.get("metadata", {})
    if metadata or is_expanded:
        st.markdown(
            '<div class="context-item-metadata">',
            unsafe_allow_html=True
        )
        
        # Source metadata
        if "source" in metadata:
            st.markdown(
                f'<div class="context-metadata source">📄 {metadata["source"]}</div>',
                unsafe_allow_html=True
            )
        
        # Time metadata
        if "timestamp" in metadata:
            timestamp = metadata["timestamp"]
            # Format timestamp for display
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(timestamp)
                relative_time = get_relative_time(dt)
                time_display = relative_time
            except:
                time_display = timestamp
            
            st.markdown(
                f'<div class="context-metadata time">⏱️ {time_display}</div>',
                unsafe_allow_html=True
            )
        
        # Type metadata
        if "type" in metadata:
            st.markdown(
                f'<div class="context-metadata type">🏷️ {metadata["type"]}</div>',
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close context-item-metadata
    
    # Relevance indicator
    if relevance > 0:
        st.markdown(
            '<div class="relevance-indicator">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="relevance-label">Relevance</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="relevance-bar">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            f'<div class="relevance-value {relevance_class}" style="width: {relevance}%;"></div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close relevance-bar
        
        st.markdown(
            f'<div class="relevance-percentage">{relevance:.0f}%</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close relevance-indicator
    
    # Expanded content
    if is_expanded:
        # Additional details
        if "details" in item:
            st.markdown(
                f'<div class="context-item-content">{item["details"]}</div>',
                unsafe_allow_html=True
            )
        
        # Related items
        if "related" in item:
            st.markdown(
                '<div class="context-item-content">Related items:</div>',
                unsafe_allow_html=True
            )
            
            for related_item in item["related"]:
                st.markdown(
                    f'<div class="context-item-content">- {related_item}</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-item

def render_context_refresh_controls():
    """Render context refresh controls"""
    st.markdown(
        '<div class="context-refresh">',
        unsafe_allow_html=True
    )
    
    # Get refresh status
    refresh_status = get_context_refresh_status()
    
    # Refresh status
    st.markdown(
        '<div class="refresh-status">',
        unsafe_allow_html=True
    )
    
    status_class = f"status-{refresh_status['status']}"
    st.markdown(
        f'<div class="status-indicator {status_class}"></div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div>{refresh_status["message"]}</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close refresh-status
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox(
        "Auto-refresh",
        value=st.session_state.get('auto_refresh_context', False),
        key="auto_refresh_context",
        help="Automatically refresh context data at regular intervals"
    )
    
    # Update auto-refresh state
    st.session_state.auto_refresh_context = auto_refresh
    
    # Refresh interval
    if auto_refresh:
        refresh_interval = st.slider(
            "Refresh interval (minutes)",
            min_value=1,
            max_value=60,
            value=st.session_state.get('refresh_interval', 5),
            key="refresh_interval"
        )
        
        # Update refresh interval state
        st.session_state.refresh_interval = refresh_interval
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-refresh

def render_context_loading():
    """Render context loading state"""
    st.markdown(
        '<div class="context-loading">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-loading-spinner"></div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-empty-title">Loading personal context...</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-empty-description">Please wait while we fetch your personal context data.</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-loading

def render_context_empty():
    """Render context empty state"""
    st.markdown(
        '<div class="context-empty">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-empty-icon">📭</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-empty-title">No personal context available</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-empty-description">Your personal context appears to be empty. Add information to help Kari provide more personalized responses.</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-error-actions">',
        unsafe_allow_html=True
    )
    
    if st.button("Add Context", key="add_context_empty", help="Add new personal context"):
        # Implement context addition
        pass
    
    if st.button("Import Context", key="import_context_empty", help="Import personal context from file"):
        # Implement context import
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-error-actions
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-empty

def render_context_error(error_message):
    """Render context error state"""
    st.markdown(
        '<div class="context-error">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-error-icon">❌</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-error-title">Error loading personal context</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div class="context-error-description">{error_message}</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="context-error-actions">',
        unsafe_allow_html=True
    )
    
    if st.button("Try Again", key="retry_context_error", help="Retry loading personal context"):
        # Implement context retry
        refresh_personal_context()
    
    if st.button("Report Issue", key="report_context_error", help="Report this issue"):
        # Implement issue reporting
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-error-actions
    st.markdown('</div>', unsafe_allow_html=True)  # Close context-error

def get_personal_context_data():
    """Get personal context data for display"""
    # Check if we have cached data
    if 'personal_context_data' in st.session_state:
        return st.session_state.personal_context_data
    
    # Check if we're currently loading
    if 'loading_personal_context' in st.session_state and st.session_state.loading_personal_context:
        return None
    
    # Set loading state
    st.session_state.loading_personal_context = True
    
    # This would be replaced with actual data fetching from backend
    # For now, we'll use simulated data
    try:
        # Simulate API call delay
        import time
        time.sleep(1)
        
        # Get simulated context data
        context_data = get_simulated_personal_context_data()
        
        # Cache the data
        st.session_state.personal_context_data = context_data
        
        return context_data
    except Exception as e:
        # Return error state
        return {"error": str(e)}
    finally:
        # Clear loading state
        st.session_state.loading_personal_context = False

def get_simulated_personal_context_data():
    """Get simulated personal context data for demonstration"""
    return {
        "profile": [
            {
                "id": "profile_1",
                "title": "Basic Information",
                "content": "Name: Alex Johnson, Age: 32, Location: San Francisco, Occupation: Software Engineer",
                "metadata": {
                    "source": "user_profile",
                    "timestamp": "2023-05-15T10:30:00",
                    "type": "basic_info"
                },
                "details": "Alex Johnson is a 32-year-old software engineer living in San Francisco. They have been working in the tech industry for 10 years and specialize in full-stack development."
            },
            {
                "id": "profile_2",
                "title": "Contact Information",
                "content": "Email: alex.johnson@example.com, Phone: (555) 123-4567",
                "metadata": {
                    "source": "user_profile",
                    "timestamp": "2023-05-15T10:30:00",
                    "type": "contact_info"
                }
            }
        ],
        "preferences": [
            {
                "id": "pref_1",
                "title": "Communication Style",
                "content": "Prefers concise, direct communication with occasional humor",
                "metadata": {
                    "source": "user_preferences",
                    "timestamp": "2023-06-20T14:15:00",
                    "type": "communication"
                },
                "details": "Alex prefers responses that are direct and to the point, but appreciates occasional humor to keep the conversation engaging. They dislike overly formal language."
            },
            {
                "id": "pref_2",
                "title": "Technical Preferences",
                "content": "Prefers Python for most tasks, JavaScript for web development",
                "metadata": {
                    "source": "user_preferences",
                    "timestamp": "2023-06-20T14:15:00",
                    "type": "technical"
                }
            }
        ],
        "history": [
            {
                "id": "history_1",
                "title": "Recent Project: E-commerce Platform",
                "content": "Led development of a new e-commerce platform using React and Node.js",
                "metadata": {
                    "source": "conversation_history",
                    "timestamp": "2023-07-10T09:45:00",
                    "type": "project"
                },
                "details": "Alex recently led a team of 5 developers to build a new e-commerce platform from scratch. The project took 6 months and resulted in a 40% increase in online sales for the client."
            },
            {
                "id": "history_2",
                "title": "Previous Job: Tech Startup",
                "content": "Worked as a senior developer at a tech startup for 3 years",
                "metadata": {
                    "source": "conversation_history",
                    "timestamp": "2023-06-05T16:20:00",
                    "type": "employment"
                }
            }
        ],
        "relationships": [
            {
                "id": "rel_1",
                "title": "Professional Network",
                "content": "Connected with 150+ professionals in the tech industry",
                "metadata": {
                    "source": "user_data",
                    "timestamp": "2023-07-15T11:30:00",
                    "type": "network"
                },
                "details": "Alex has built a strong professional network over the past 10 years, with connections at major tech companies including Google, Apple, and Microsoft."
            },
            {
                "id": "rel_2",
                "title": "Mentorship",
                "content": "Mentors 3 junior developers",
                "metadata": {
                    "source": "user_data",
                    "timestamp": "2023-07-01T13:45:00",
                    "type": "mentorship"
                }
            }
        ],
        "interests": [
            {
                "id": "interest_1",
                "title": "Hiking",
                "content": "Enjoys hiking on weekends, especially in the Bay Area",
                "metadata": {
                    "source": "user_interests",
                    "timestamp": "2023-07-20T08:15:00",
                    "type": "outdoor"
                },
                "details": "Alex is an avid hiker and tries to go hiking at least twice a month. Favorite trails include Mount Tamalpais and the Muir Woods."
            },
            {
                "id": "interest_2",
                "title": "Technology Trends",
                "content": "Follows AI and machine learning developments closely",
                "metadata": {
                    "source": "user_interests",
                    "timestamp": "2023-07-18T19:30:00",
                    "type": "technology"
                }
            }
        ]
    }

def should_display_category(category):
    """Check if category should be displayed based on active filters"""
    # If no filters are active, display all categories
    if not any(st.session_state.context_filters.values()):
        return True
    
    # If "All Context" filter is active, display all categories
    if st.session_state.context_filters.get("all", False):
        return True
    
    # Check category against active filters
    if st.session_state.context_filters.get(category, False):
        return True
    
    # Category doesn't match any active filters
    return False

def get_category_info(category):
    """Get information about a context category"""
    categories = {
        "profile": {
            "name": "Profile",
            "icon": "👤",
            "color": "rgba(0, 255, 255, 0.2)"
        },
        "preferences": {
            "name": "Preferences",
            "icon": "⚙️",
            "color": "rgba(255, 0, 255, 0.2)"
        },
        "history": {
            "name": "History",
            "icon": "📜",
            "color": "rgba(255, 255, 0, 0.2)"
        },
        "relationships": {
            "name": "Relationships",
            "icon": "👥",
            "color": "rgba(0, 255, 0, 0.2)"
        },
        "interests": {
            "name": "Interests",
            "icon": "❤️",
            "color": "rgba(255, 0, 0, 0.2)"
        }
    }
    
    return categories.get(category, {
        "name": category.capitalize(),
        "icon": "📄",
        "color": "rgba(255, 255, 255, 0.2)"
    })

def calculate_item_relevance(item, category):
    """Calculate relevance score for a context item"""
    # This would be replaced with actual relevance calculation
    # For now, we'll use a simple random score
    import random
    return random.randint(30, 95)

def get_relative_time(dt):
    """Get relative time string from datetime object"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")

def get_context_refresh_status():
    """Get current context refresh status"""
    # This would be replaced with actual refresh status
    # For now, we'll use a simple status
    return {
        "status": "up-to-date",
        "message": "Context data is up to date"
    }

def refresh_personal_context():
    """Refresh personal context data"""
    # Clear cached data
    if 'personal_context_data' in st.session_state:
        del st.session_state.personal_context_data
    
    # Set refresh status
    st.session_state.context_refresh_status = {
        "status": "refreshing",
        "message": "Refreshing context data..."
    }
    
    # Trigger data reload
    get_personal_context_data()
    
    # Update refresh status
    st.session_state.context_refresh_status = {
        "status": "up-to-date",
        "message": "Context data refreshed"
    }
    
    # Rerun to update UI
    st.rerun()
```

### 6. Integration with Existing Components

#### 6.1 Update Personal Context Zone

```python
# Enhanced personal context zone
def render_enhanced_personal_context_zone():
    """Render enhanced personal context interface with improved visualization and features"""
    st.markdown("## Personal Context")
    
    # Initialize context state
    if 'personal_context_data' not in st.session_state:
        st.session_state.personal_context_data = None
    
    if 'context_filters' not in st.session_state:
        st.session_state.context_filters = {"all": True}
    
    if 'context_search_query' not in st.session_state:
        st.session_state.context_search_query = ""
    
    if 'auto_refresh_context' not in st.session_state:
        st.session_state.auto_refresh_context = False
    
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 5
    
    # Render enhanced personal context
    render_enhanced_personal_context()
```

#### 6.2 Update CSS

```python
# Add enhanced personal context CSS to load_neon_theme function
def load_neon_theme():
    # Existing CSS...
    
    # Add enhanced personal context CSS
    enhanced_context_css = """
    /* Enhanced personal context CSS from section 5.1 */
    """
    
    # Combine with existing CSS
    neon_css += enhanced_context_css
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

# Personal Context Defaults
DEFAULT_CONTEXT_AUTO_REFRESH=false
DEFAULT_CONTEXT_REFRESH_INTERVAL=5
DEFAULT_CONTEXT_FILTERS=true
DEFAULT_CONTEXT_SEARCH=true
DEFAULT_CONTEXT_RELEVANCE=true
DEFAULT_CONTEXT_ITEM_EXPANDED=false
DEFAULT_CONTEXT_ITEM_DETAILS=true
DEFAULT_CONTEXT_ITEM_RELATED=true

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
MAX_CONTEXT_ITEMS=100
CONTEXT_ITEM_CACHE_SIZE=200
```

### 8. Testing Strategy

#### 8.1 Unit Testing
- Test context data fetching functionality
- Test context filtering and search
- Test relevance calculation
- Test refresh mechanisms

#### 8.2 Integration Testing
- Test context item interactions
- Test filter and search combinations
- Test refresh controls
- Test context display performance

#### 8.3 User Acceptance Testing
- Test overall personal context usability
- Test context filtering effectiveness
- Test relevance indicator accuracy
- Test refresh mechanism reliability

### 9. Success Metrics

1. **Context Engagement**:
   - Context item expansion rate
   - Context filter usage frequency
   - Context search query rate
   - Context refresh frequency

2. **Context Relevance**:
   - User satisfaction with context relevance
   - Relevance indicator accuracy
   - Context filtering effectiveness
   - Context search result quality

3. **Performance and Efficiency**:
   - Context data load time
   - Context filtering response time
   - Context search response time
   - Context refresh performance

### 10. Rollout Plan

#### 10.1 Phase 1: Basic Enhancements
- Implement enhanced context item styling
- Add basic filtering and search
- Include relevance indicators

#### 10.2 Phase 2: Advanced Features
- Add context item details and interactions
- Implement refresh mechanisms
- Include context category management

#### 10.3 Phase 3: Optimization
- Add performance optimizations
- Implement accessibility features
- Include user preference controls

## Conclusion

This plan outlines a comprehensive approach to enhancing the personal context display in Kari AI Lite Streamlit Console. By implementing these features, we'll create a more informative and visually appealing personal context interface that provides better visibility into the user's personal information, preferences, and relevant context for the AI to use in conversations.

The implementation will be done in phases, starting with basic context item styling enhancements, then moving to more advanced features like refresh mechanisms and filtering functionality.