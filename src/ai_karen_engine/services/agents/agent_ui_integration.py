"""
Agent UI Integration Service

This service provides integration capabilities between agents and the user interface,
allowing agents to interact with UI components and display information to users.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class UIComponentType(Enum):
    """Enumeration of UI component types."""
    TEXT = "text"
    BUTTON = "button"
    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PROGRESS = "progress"
    ALERT = "alert"
    MODAL = "modal"
    TABS = "tabs"
    ACCORDION = "accordion"
    DROPDOWN = "dropdown"
    SLIDER = "slider"
    TOGGLE = "toggle"
    DATE_PICKER = "date_picker"
    COLOR_PICKER = "color_picker"
    FILE_UPLOAD = "file_upload"
    RICH_TEXT = "rich_text"
    CODE_EDITOR = "code_editor"


class UIEvent(Enum):
    """Enumeration of UI events."""
    CLICK = "click"
    CHANGE = "change"
    SUBMIT = "submit"
    FOCUS = "focus"
    BLUR = "blur"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_OVER = "mouse_over"
    MOUSE_OUT = "mouse_out"
    DRAG_START = "drag_start"
    DRAG_END = "drag_end"
    DROP = "drop"
    RESIZE = "resize"
    SCROLL = "scroll"


class UIAlignment(Enum):
    """Enumeration of UI alignments."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


@dataclass
class UIComponent:
    """A UI component."""
    id: str
    component_type: UIComponentType
    content: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, Any] = field(default_factory=dict)
    events: Dict[UIEvent, Callable] = field(default_factory=dict)
    children: List['UIComponent'] = field(default_factory=list)
    visible: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UILayout:
    """A UI layout."""
    id: str
    name: str
    components: List[UIComponent] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIInteraction:
    """A UI interaction."""
    id: str
    component_id: str
    event: UIEvent
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class UIState:
    """A UI state."""
    id: str
    component_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    layout_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentUIIntegration:
    """
    Provides integration capabilities between agents and the user interface.
    
    This class is responsible for:
    - Creating and managing UI components
    - Handling UI events and interactions
    - Managing UI layouts
    - Synchronizing UI state between agents and the UI
    - Providing callbacks for UI events
    """
    
    def __init__(self):
        self._components: Dict[str, UIComponent] = {}
        self._layouts: Dict[str, UILayout] = {}
        self._interactions: List[UIInteraction] = []
        self._states: Dict[str, UIState] = {}
        self._component_layouts: Dict[str, Set[str]] = defaultdict(set)  # component_id -> layout_ids
        self._agent_states: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> state_ids
        self._session_states: Dict[str, Set[str]] = defaultdict(set)  # session_id -> state_ids
        
        # Callbacks for UI events
        self._on_component_created: Optional[Callable[[UIComponent], None]] = None
        self._on_layout_created: Optional[Callable[[UILayout], None]] = None
        self._on_interaction: Optional[Callable[[UIInteraction], None]] = None
        self._on_state_changed: Optional[Callable[[UIState, UIState], None]] = None
    
    def create_component(
        self,
        component_type: UIComponentType,
        content: str = "",
        properties: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        events: Optional[Dict[UIEvent, Callable]] = None,
        children: Optional[List[UIComponent]] = None,
        visible: bool = True,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        component_id: Optional[str] = None
    ) -> UIComponent:
        """
        Create a UI component.
        
        Args:
            component_type: Type of the component
            content: Content of the component
            properties: Properties of the component
            style: Style of the component
            events: Events of the component
            children: Children of the component
            visible: Whether the component is visible
            enabled: Whether the component is enabled
            metadata: Metadata of the component
            component_id: ID of the component
            
        Returns:
            Created UI component
        """
        component_id = component_id or str(uuid.uuid4())
        
        component = UIComponent(
            id=component_id,
            component_type=component_type,
            content=content,
            properties=properties or {},
            style=style or {},
            events=events or {},
            children=children or [],
            visible=visible,
            enabled=enabled,
            metadata=metadata or {}
        )
        
        self._components[component_id] = component
        
        # Call component created callback if set
        if self._on_component_created:
            self._on_component_created(component)
        
        logger.debug(f"Created UI component: {component_id} of type {component_type.value}")
        return component
    
    def get_component(self, component_id: str) -> Optional[UIComponent]:
        """Get a UI component by ID."""
        return self._components.get(component_id)
    
    def update_component(
        self,
        component_id: str,
        content: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        events: Optional[Dict[UIEvent, Callable]] = None,
        children: Optional[List[UIComponent]] = None,
        visible: Optional[bool] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a UI component.
        
        Args:
            component_id: ID of the component
            content: New content of the component
            properties: New properties of the component
            style: New style of the component
            events: New events of the component
            children: New children of the component
            visible: New visibility of the component
            enabled: New enabled state of the component
            metadata: New metadata of the component
            
        Returns:
            True if component was updated, False if not found
        """
        component = self._components.get(component_id)
        if not component:
            logger.warning(f"Attempted to update non-existent component: {component_id}")
            return False
        
        if content is not None:
            component.content = content
        
        if properties is not None:
            component.properties.update(properties)
        
        if style is not None:
            component.style.update(style)
        
        if events is not None:
            component.events.update(events)
        
        if children is not None:
            component.children = children
        
        if visible is not None:
            component.visible = visible
        
        if enabled is not None:
            component.enabled = enabled
        
        if metadata is not None:
            component.metadata.update(metadata)
        
        logger.debug(f"Updated UI component: {component_id}")
        return True
    
    def delete_component(self, component_id: str) -> bool:
        """
        Delete a UI component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            True if component was deleted, False if not found
        """
        if component_id in self._components:
            del self._components[component_id]
            
            # Remove from layouts
            for layout_id in self._component_layouts.get(component_id, set()):
                layout = self._layouts.get(layout_id)
                if layout:
                    layout.components = [c for c in layout.components if c.id != component_id]
            
            # Remove from component layouts mapping
            if component_id in self._component_layouts:
                del self._component_layouts[component_id]
            
            logger.debug(f"Deleted UI component: {component_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent component: {component_id}")
            return False
    
    def create_layout(
        self,
        name: str,
        components: Optional[List[UIComponent]] = None,
        style: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        layout_id: Optional[str] = None
    ) -> UILayout:
        """
        Create a UI layout.
        
        Args:
            name: Name of the layout
            components: Components of the layout
            style: Style of the layout
            metadata: Metadata of the layout
            layout_id: ID of the layout
            
        Returns:
            Created UI layout
        """
        layout_id = layout_id or str(uuid.uuid4())
        
        layout = UILayout(
            id=layout_id,
            name=name,
            components=components or [],
            style=style or {},
            metadata=metadata or {}
        )
        
        self._layouts[layout_id] = layout
        
        # Update component layouts mapping
        for component in layout.components:
            self._component_layouts[component.id].add(layout_id)
        
        # Call layout created callback if set
        if self._on_layout_created:
            self._on_layout_created(layout)
        
        logger.debug(f"Created UI layout: {layout_id} with name {name}")
        return layout
    
    def get_layout(self, layout_id: str) -> Optional[UILayout]:
        """Get a UI layout by ID."""
        return self._layouts.get(layout_id)
    
    def add_component_to_layout(self, layout_id: str, component: UIComponent) -> bool:
        """
        Add a component to a layout.
        
        Args:
            layout_id: ID of the layout
            component: Component to add
            
        Returns:
            True if component was added, False if layout not found
        """
        layout = self._layouts.get(layout_id)
        if not layout:
            logger.warning(f"Attempted to add component to non-existent layout: {layout_id}")
            return False
        
        layout.components.append(component)
        self._component_layouts[component.id].add(layout_id)
        
        logger.debug(f"Added component {component.id} to layout {layout_id}")
        return True
    
    def remove_component_from_layout(self, layout_id: str, component_id: str) -> bool:
        """
        Remove a component from a layout.
        
        Args:
            layout_id: ID of the layout
            component_id: ID of the component
            
        Returns:
            True if component was removed, False if layout or component not found
        """
        layout = self._layouts.get(layout_id)
        if not layout:
            logger.warning(f"Attempted to remove component from non-existent layout: {layout_id}")
            return False
        
        # Find and remove component
        for i, component in enumerate(layout.components):
            if component.id == component_id:
                layout.components.pop(i)
                self._component_layouts[component_id].discard(layout_id)
                
                logger.debug(f"Removed component {component_id} from layout {layout_id}")
                return True
        
        logger.warning(f"Attempted to remove non-existent component {component_id} from layout {layout_id}")
        return False
    
    def delete_layout(self, layout_id: str) -> bool:
        """
        Delete a UI layout.
        
        Args:
            layout_id: ID of the layout
            
        Returns:
            True if layout was deleted, False if not found
        """
        if layout_id in self._layouts:
            del self._layouts[layout_id]
            
            # Update component layouts mapping
            for component_id, layout_ids in self._component_layouts.items():
                layout_ids.discard(layout_id)
            
            logger.debug(f"Deleted UI layout: {layout_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent layout: {layout_id}")
            return False
    
    def record_interaction(
        self,
        component_id: str,
        event: UIEvent,
        data: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        interaction_id: Optional[str] = None
    ) -> UIInteraction:
        """
        Record a UI interaction.
        
        Args:
            component_id: ID of the component
            event: Event that occurred
            data: Data associated with the event
            agent_id: ID of the agent that triggered the event
            session_id: ID of the session
            interaction_id: ID of the interaction
            
        Returns:
            Recorded UI interaction
        """
        interaction_id = interaction_id or str(uuid.uuid4())
        
        interaction = UIInteraction(
            id=interaction_id,
            component_id=component_id,
            event=event,
            data=data or {},
            agent_id=agent_id,
            session_id=session_id
        )
        
        self._interactions.append(interaction)
        
        # Call interaction callback if set
        if self._on_interaction:
            self._on_interaction(interaction)
        
        logger.debug(f"Recorded UI interaction: {interaction_id} on component {component_id}")
        return interaction
    
    def get_interactions(
        self,
        component_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event: Optional[UIEvent] = None,
        limit: int = 100
    ) -> List[UIInteraction]:
        """
        Get UI interactions.
        
        Args:
            component_id: ID of the component
            agent_id: ID of the agent
            session_id: ID of the session
            event: Event type
            limit: Maximum number of interactions to return
            
        Returns:
            List of UI interactions
        """
        interactions = self._interactions
        
        # Filter by component_id
        if component_id:
            interactions = [i for i in interactions if i.component_id == component_id]
        
        # Filter by agent_id
        if agent_id:
            interactions = [i for i in interactions if i.agent_id == agent_id]
        
        # Filter by session_id
        if session_id:
            interactions = [i for i in interactions if i.session_id == session_id]
        
        # Filter by event
        if event:
            interactions = [i for i in interactions if i.event == event]
        
        # Sort by timestamp (newest first)
        interactions.sort(key=lambda i: i.timestamp, reverse=True)
        
        # Apply limit
        return interactions[:limit]
    
    def create_state(
        self,
        component_states: Optional[Dict[str, Dict[str, Any]]] = None,
        layout_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        state_id: Optional[str] = None
    ) -> UIState:
        """
        Create a UI state.
        
        Args:
            component_states: States of components
            layout_id: ID of the layout
            agent_id: ID of the agent
            session_id: ID of the session
            state_id: ID of the state
            
        Returns:
            Created UI state
        """
        state_id = state_id or str(uuid.uuid4())
        
        state = UIState(
            id=state_id,
            component_states=component_states or {},
            layout_id=layout_id,
            agent_id=agent_id,
            session_id=session_id
        )
        
        self._states[state_id] = state
        
        # Update agent states mapping
        if agent_id:
            self._agent_states[agent_id].add(state_id)
        
        # Update session states mapping
        if session_id:
            self._session_states[session_id].add(state_id)
        
        logger.debug(f"Created UI state: {state_id}")
        return state
    
    def get_state(self, state_id: str) -> Optional[UIState]:
        """Get a UI state by ID."""
        return self._states.get(state_id)
    
    def update_state(
        self,
        state_id: str,
        component_states: Optional[Dict[str, Dict[str, Any]]] = None,
        layout_id: Optional[str] = None
    ) -> bool:
        """
        Update a UI state.
        
        Args:
            state_id: ID of the state
            component_states: New states of components
            layout_id: New ID of the layout
            
        Returns:
            True if state was updated, False if not found
        """
        state = self._states.get(state_id)
        if not state:
            logger.warning(f"Attempted to update non-existent state: {state_id}")
            return False
        
        old_state = UIState(
            id=state.id,
            component_states=state.component_states.copy(),
            layout_id=state.layout_id,
            timestamp=state.timestamp,
            agent_id=state.agent_id,
            session_id=state.session_id
        )
        
        if component_states is not None:
            state.component_states.update(component_states)
        
        if layout_id is not None:
            state.layout_id = layout_id
        
        state.timestamp = datetime.now()
        
        # Call state changed callback if set
        if self._on_state_changed:
            self._on_state_changed(old_state, state)
        
        logger.debug(f"Updated UI state: {state_id}")
        return True
    
    def delete_state(self, state_id: str) -> bool:
        """
        Delete a UI state.
        
        Args:
            state_id: ID of the state
            
        Returns:
            True if state was deleted, False if not found
        """
        state = self._states.get(state_id)
        if not state:
            logger.warning(f"Attempted to delete non-existent state: {state_id}")
            return False
        
        # Remove from agent states mapping
        if state.agent_id and state_id in self._agent_states[state.agent_id]:
            self._agent_states[state.agent_id].remove(state_id)
        
        # Remove from session states mapping
        if state.session_id and state_id in self._session_states[state.session_id]:
            self._session_states[state.session_id].remove(state_id)
        
        del self._states[state_id]
        
        logger.debug(f"Deleted UI state: {state_id}")
        return True
    
    def get_states_for_agent(self, agent_id: str) -> List[UIState]:
        """Get UI states for an agent."""
        state_ids = self._agent_states.get(agent_id, set())
        return [self._states[state_id] for state_id in state_ids if state_id in self._states]
    
    def get_states_for_session(self, session_id: str) -> List[UIState]:
        """Get UI states for a session."""
        state_ids = self._session_states.get(session_id, set())
        return [self._states[state_id] for state_id in state_ids if state_id in self._states]
    
    def set_ui_callbacks(
        self,
        on_component_created: Optional[Callable[[UIComponent], None]] = None,
        on_layout_created: Optional[Callable[[UILayout], None]] = None,
        on_interaction: Optional[Callable[[UIInteraction], None]] = None,
        on_state_changed: Optional[Callable[[UIState, UIState], None]] = None
    ) -> None:
        """Set callbacks for UI events."""
        self._on_component_created = on_component_created
        self._on_layout_created = on_layout_created
        self._on_interaction = on_interaction
        self._on_state_changed = on_state_changed
    
    def render_layout(self, layout_id: str) -> Dict[str, Any]:
        """
        Render a layout to a dictionary representation.
        
        Args:
            layout_id: ID of the layout
            
        Returns:
            Dictionary representation of the layout
        """
        layout = self._layouts.get(layout_id)
        if not layout:
            raise ValueError(f"Layout not found: {layout_id}")
        
        return self._render_layout(layout)
    
    def render_component(self, component_id: str) -> Dict[str, Any]:
        """
        Render a component to a dictionary representation.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary representation of the component
        """
        component = self._components.get(component_id)
        if not component:
            raise ValueError(f"Component not found: {component_id}")
        
        return self._render_component(component)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about UI integration.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_components": len(self._components),
            "total_layouts": len(self._layouts),
            "total_interactions": len(self._interactions),
            "total_states": len(self._states),
            "components_by_type": {},
            "layouts_by_component_count": {},
            "interactions_by_event": {},
            "states_by_agent": {agent_id: len(state_ids) for agent_id, state_ids in self._agent_states.items()},
            "states_by_session": {session_id: len(state_ids) for session_id, state_ids in self._session_states.items()}
        }
        
        # Count components by type
        for component in self._components.values():
            component_type = component.component_type.value
            if component_type not in stats["components_by_type"]:
                stats["components_by_type"][component_type] = 0
            stats["components_by_type"][component_type] += 1
        
        # Count layouts by component count
        for layout in self._layouts.values():
            component_count = len(layout.components)
            if component_count not in stats["layouts_by_component_count"]:
                stats["layouts_by_component_count"][component_count] = 0
            stats["layouts_by_component_count"][component_count] += 1
        
        # Count interactions by event
        for interaction in self._interactions:
            event = interaction.event.value
            if event not in stats["interactions_by_event"]:
                stats["interactions_by_event"][event] = 0
            stats["interactions_by_event"][event] += 1
        
        return stats
    
    def _render_layout(self, layout: UILayout) -> Dict[str, Any]:
        """Render a layout to a dictionary representation."""
        return {
            "id": layout.id,
            "name": layout.name,
            "style": layout.style,
            "metadata": layout.metadata,
            "components": [self._render_component(component) for component in layout.components]
        }
    
    def _render_component(self, component: UIComponent) -> Dict[str, Any]:
        """Render a component to a dictionary representation."""
        return {
            "id": component.id,
            "type": component.component_type.value,
            "content": component.content,
            "properties": component.properties,
            "style": component.style,
            "visible": component.visible,
            "enabled": component.enabled,
            "metadata": component.metadata,
            "children": [self._render_component(child) for child in component.children]
        }