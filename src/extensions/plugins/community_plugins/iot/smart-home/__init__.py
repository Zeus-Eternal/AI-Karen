"""
IoT Smart Home Extension - Migrated from ui_logic/pages/iot.py

This extension provides comprehensive IoT device management including:
- Device discovery and registration
- Scene automation and scheduling
- Real-time monitoring and logging
- AI-powered optimization recommendations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

# Import the original IoT components
from ui_logic.components.iot.device_manager import render_device_manager
from ui_logic.components.iot.iot_logs import render_iot_logs
from ui_logic.components.iot.scene_builder import render_scene_builder

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """IoT device types."""
    LIGHT = "light"
    SWITCH = "switch"
    SENSOR = "sensor"
    THERMOSTAT = "thermostat"
    CAMERA = "camera"
    SPEAKER = "speaker"
    LOCK = "lock"
    UNKNOWN = "unknown"


class DeviceStatus(str, Enum):
    """Device status."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UPDATING = "updating"


class Device(BaseModel):
    """IoT device model."""
    id: str
    name: str
    device_type: DeviceType
    status: DeviceStatus
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen: str
    properties: Dict[str, Any] = {}
    capabilities: List[str] = []


class Scene(BaseModel):
    """Smart home scene model."""
    id: str
    name: str
    description: Optional[str] = None
    devices: List[Dict[str, Any]]  # Device actions
    triggers: List[Dict[str, Any]] = []
    conditions: List[Dict[str, Any]] = []
    enabled: bool = True
    created_at: str
    last_executed: Optional[str] = None


class DeviceControl(BaseModel):
    """Device control request."""
    device_id: str
    action: str
    parameters: Dict[str, Any] = {}


class IoTSmartHomeExtension(BaseExtension, HookMixin):
    """IoT Smart Home Extension with device management and automation."""
    
    async def _initialize(self) -> None:
        """Initialize the IoT Smart Home Extension."""
        self.logger.info("IoT Smart Home Extension initializing...")
        
        # Initialize device and scene storage
        self.devices: Dict[str, Device] = {}
        self.scenes: Dict[str, Scene] = {}
        self.device_logs: List[Dict[str, Any]] = []
        self.automation_history: List[Dict[str, Any]] = []
        
        # Discover existing devices
        await self._discover_devices()
        
        # Load default scenes
        await self._load_default_scenes()
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        # Register hooks for device monitoring
        await self._register_device_hooks()
        
        self.logger.info("IoT Smart Home Extension initialized successfully")
    
    async def _discover_devices(self) -> None:
        """Discover IoT devices on the network."""
        try:
            # Simulate device discovery - in practice, this would scan the network
            default_devices = {
                "light_living_room": Device(
                    id="light_living_room",
                    name="Living Room Light",
                    device_type=DeviceType.LIGHT,
                    status=DeviceStatus.ONLINE,
                    location="Living Room",
                    manufacturer="Philips",
                    model="Hue Bulb",
                    ip_address="192.168.1.100",
                    last_seen=datetime.utcnow().isoformat(),
                    properties={"brightness": 80, "color": "#FFFFFF", "power": True},
                    capabilities=["brightness", "color", "power"]
                ),
                "thermostat_main": Device(
                    id="thermostat_main",
                    name="Main Thermostat",
                    device_type=DeviceType.THERMOSTAT,
                    status=DeviceStatus.ONLINE,
                    location="Hallway",
                    manufacturer="Nest",
                    model="Learning Thermostat",
                    ip_address="192.168.1.101",
                    last_seen=datetime.utcnow().isoformat(),
                    properties={"temperature": 22.5, "target_temperature": 23.0, "mode": "heat"},
                    capabilities=["temperature", "target_temperature", "mode"]
                ),
                "sensor_front_door": Device(
                    id="sensor_front_door",
                    name="Front Door Sensor",
                    device_type=DeviceType.SENSOR,
                    status=DeviceStatus.ONLINE,
                    location="Front Door",
                    manufacturer="SmartThings",
                    model="Motion Sensor",
                    ip_address="192.168.1.102",
                    last_seen=datetime.utcnow().isoformat(),
                    properties={"motion": False, "battery": 85, "temperature": 20.1},
                    capabilities=["motion", "battery", "temperature"]
                )
            }
            
            self.devices.update(default_devices)
            self.logger.info(f"Discovered {len(default_devices)} IoT devices")
            
        except Exception as e:
            self.logger.error(f"Failed to discover devices: {e}")
    
    async def _load_default_scenes(self) -> None:
        """Load default smart home scenes."""
        default_scenes = {
            "good_morning": Scene(
                id="good_morning",
                name="Good Morning",
                description="Morning routine - turn on lights, adjust thermostat",
                devices=[
                    {"device_id": "light_living_room", "action": "turn_on", "parameters": {"brightness": 100}},
                    {"device_id": "thermostat_main", "action": "set_temperature", "parameters": {"temperature": 21}}
                ],
                triggers=[{"type": "time", "time": "07:00"}],
                created_at=datetime.utcnow().isoformat()
            ),
            "good_night": Scene(
                id="good_night",
                name="Good Night",
                description="Night routine - turn off lights, lower thermostat",
                devices=[
                    {"device_id": "light_living_room", "action": "turn_off"},
                    {"device_id": "thermostat_main", "action": "set_temperature", "parameters": {"temperature": 18}}
                ],
                triggers=[{"type": "time", "time": "22:00"}],
                created_at=datetime.utcnow().isoformat()
            ),
            "away_mode": Scene(
                id="away_mode",
                name="Away Mode",
                description="Security mode when away from home",
                devices=[
                    {"device_id": "light_living_room", "action": "turn_off"},
                    {"device_id": "thermostat_main", "action": "set_temperature", "parameters": {"temperature": 16}}
                ],
                triggers=[{"type": "manual"}],
                created_at=datetime.utcnow().isoformat()
            )
        }
        
        self.scenes.update(default_scenes)
        self.logger.info(f"Loaded {len(default_scenes)} default scenes")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered IoT management."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register IoT management tools
            await self.register_mcp_tool(
                name="control_device",
                handler=self._control_device_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Device identifier"},
                        "action": {"type": "string", "description": "Action to perform"},
                        "parameters": {"type": "object", "description": "Action parameters"}
                    },
                    "required": ["device_id", "action"]
                },
                description="Control IoT devices with specific actions"
            )
            
            await self.register_mcp_tool(
                name="create_scene",
                handler=self._create_scene_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Scene name"},
                        "description": {"type": "string", "description": "Scene description"},
                        "device_actions": {"type": "array", "description": "List of device actions"},
                        "triggers": {"type": "array", "description": "Scene triggers"}
                    },
                    "required": ["name", "device_actions"]
                },
                description="Create smart home scenes with multiple device actions"
            )
            
            await self.register_mcp_tool(
                name="optimize_energy_usage",
                handler=self._optimize_energy_usage_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "optimization_goal": {"type": "string", "enum": ["energy_saving", "comfort", "security"], "description": "Optimization target"},
                        "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "daily", "description": "Optimization period"}
                    },
                    "required": ["optimization_goal"]
                },
                description="Get AI-powered energy optimization recommendations"
            )
    
    async def _register_device_hooks(self) -> None:
        """Register hooks for device monitoring and automation."""
        try:
            await self.register_hook(
                'device_status_change',
                self._track_device_status,
                priority=90
            )
            
            await self.register_hook(
                'scene_execution',
                self._track_scene_execution,
                priority=90
            )
            
            self.logger.info("Device monitoring hooks registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register device hooks: {e}")
    
    async def _control_device_tool(self, device_id: str, action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """MCP tool to control IoT devices."""
        try:
            device = self.devices.get(device_id)
            if not device:
                return {
                    "success": False,
                    "error": f"Device '{device_id}' not found"
                }
            
            if device.status != DeviceStatus.ONLINE:
                return {
                    "success": False,
                    "error": f"Device '{device_id}' is {device.status.value}"
                }
            
            # Simulate device control - in practice, this would send commands to actual devices
            parameters = parameters or {}
            
            # Update device properties based on action
            if action == "turn_on" and "power" in device.capabilities:
                device.properties["power"] = True
            elif action == "turn_off" and "power" in device.capabilities:
                device.properties["power"] = False
            elif action == "set_brightness" and "brightness" in device.capabilities:
                brightness = parameters.get("brightness", 50)
                device.properties["brightness"] = max(0, min(100, brightness))
            elif action == "set_temperature" and "target_temperature" in device.capabilities:
                temperature = parameters.get("temperature", 20)
                device.properties["target_temperature"] = temperature
            elif action == "set_color" and "color" in device.capabilities:
                color = parameters.get("color", "#FFFFFF")
                device.properties["color"] = color
            
            # Log the action
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": device_id,
                "device_name": device.name,
                "action": action,
                "parameters": parameters,
                "success": True,
                "user_initiated": True
            }
            self.device_logs.append(log_entry)
            
            # Keep only recent logs (last 1000 entries)
            if len(self.device_logs) > 1000:
                self.device_logs = self.device_logs[-1000:]
            
            return {
                "success": True,
                "device_id": device_id,
                "action": action,
                "parameters": parameters,
                "new_state": device.properties,
                "message": f"Successfully executed {action} on {device.name}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to control device: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_scene_tool(self, name: str, device_actions: List[Dict[str, Any]], description: Optional[str] = None, triggers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """MCP tool to create smart home scenes."""
        try:
            scene_id = f"scene_{len(self.scenes) + 1}"
            
            # Validate device actions
            for action in device_actions:
                device_id = action.get("device_id")
                if device_id not in self.devices:
                    return {
                        "success": False,
                        "error": f"Device '{device_id}' not found"
                    }
            
            scene = Scene(
                id=scene_id,
                name=name,
                description=description,
                devices=device_actions,
                triggers=triggers or [{"type": "manual"}],
                created_at=datetime.utcnow().isoformat()
            )
            
            self.scenes[scene_id] = scene
            
            return {
                "success": True,
                "scene": scene.dict(),
                "message": f"Scene '{name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create scene: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_energy_usage_tool(self, optimization_goal: str, time_period: str = "daily") -> Dict[str, Any]:
        """MCP tool for AI-powered energy optimization."""
        try:
            # Analyze current device usage patterns
            current_usage = self._analyze_device_usage()
            
            # Generate optimization recommendations
            recommendations = self._generate_energy_recommendations(optimization_goal, current_usage)
            
            return {
                "success": True,
                "optimization_goal": optimization_goal,
                "time_period": time_period,
                "current_usage": current_usage,
                "recommendations": recommendations,
                "potential_savings": self._calculate_potential_savings(recommendations)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize energy usage: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_device_usage(self) -> Dict[str, Any]:
        """Analyze current device usage patterns."""
        usage_analysis = {
            "total_devices": len(self.devices),
            "online_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.ONLINE]),
            "device_types": {},
            "power_consuming_devices": [],
            "recent_activity": len([log for log in self.device_logs if 
                                  datetime.fromisoformat(log["timestamp"]) > datetime.utcnow() - timedelta(hours=24)])
        }
        
        # Analyze by device type
        for device in self.devices.values():
            device_type = device.device_type.value
            if device_type not in usage_analysis["device_types"]:
                usage_analysis["device_types"][device_type] = 0
            usage_analysis["device_types"][device_type] += 1
            
            # Identify power-consuming devices
            if device.device_type in [DeviceType.LIGHT, DeviceType.THERMOSTAT] and device.properties.get("power"):
                usage_analysis["power_consuming_devices"].append({
                    "device_id": device.id,
                    "name": device.name,
                    "type": device.device_type.value,
                    "estimated_consumption": self._estimate_power_consumption(device)
                })
        
        return usage_analysis
    
    def _estimate_power_consumption(self, device: Device) -> float:
        """Estimate power consumption for a device."""
        # Simplified power estimation based on device type
        consumption_map = {
            DeviceType.LIGHT: 10.0,  # 10W
            DeviceType.THERMOSTAT: 150.0,  # 150W when heating/cooling
            DeviceType.SENSOR: 0.5,  # 0.5W
            DeviceType.CAMERA: 5.0,  # 5W
            DeviceType.SPEAKER: 20.0,  # 20W
            DeviceType.LOCK: 2.0,  # 2W
        }
        
        base_consumption = consumption_map.get(device.device_type, 5.0)
        
        # Adjust based on device properties
        if device.device_type == DeviceType.LIGHT:
            brightness = device.properties.get("brightness", 50)
            base_consumption *= (brightness / 100)
        
        return base_consumption
    
    def _generate_energy_recommendations(self, goal: str, usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate energy optimization recommendations."""
        recommendations = []
        
        if goal == "energy_saving":
            # Recommend turning off unused devices
            for device in usage_analysis["power_consuming_devices"]:
                if device["estimated_consumption"] > 50:  # High consumption devices
                    recommendations.append({
                        "type": "reduce_consumption",
                        "device_id": device["device_id"],
                        "device_name": device["name"],
                        "action": "Schedule automatic turn-off during low usage periods",
                        "potential_savings": f"{device['estimated_consumption'] * 0.3:.1f}W"
                    })
            
            # Recommend scene optimization
            recommendations.append({
                "type": "scene_optimization",
                "action": "Create 'Energy Saver' scene to turn off non-essential devices",
                "potential_savings": "15-25% energy reduction"
            })
        
        elif goal == "comfort":
            # Recommend temperature optimization
            recommendations.append({
                "type": "comfort_optimization",
                "action": "Optimize thermostat scheduling based on occupancy patterns",
                "benefit": "Maintain comfort while reducing energy waste"
            })
            
            # Recommend lighting optimization
            recommendations.append({
                "type": "lighting_optimization",
                "action": "Adjust lighting brightness based on time of day and natural light",
                "benefit": "Improved comfort and energy efficiency"
            })
        
        elif goal == "security":
            # Recommend security automation
            recommendations.append({
                "type": "security_automation",
                "action": "Create motion-activated lighting scenes for security",
                "benefit": "Enhanced security with minimal energy impact"
            })
            
            recommendations.append({
                "type": "presence_simulation",
                "action": "Schedule random lighting patterns when away",
                "benefit": "Simulate presence for security"
            })
        
        return recommendations
    
    def _calculate_potential_savings(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate potential energy and cost savings."""
        total_power_savings = 0
        for rec in recommendations:
            if "potential_savings" in rec and "W" in rec["potential_savings"]:
                savings_str = rec["potential_savings"].replace("W", "")
                try:
                    total_power_savings += float(savings_str)
                except ValueError:
                    continue
        
        # Estimate cost savings (assuming $0.12 per kWh)
        daily_kwh_savings = (total_power_savings * 24) / 1000
        monthly_cost_savings = daily_kwh_savings * 30 * 0.12
        
        return {
            "power_savings_watts": total_power_savings,
            "daily_energy_savings_kwh": daily_kwh_savings,
            "monthly_cost_savings_usd": round(monthly_cost_savings, 2)
        }
    
    async def _track_device_status(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to track device status changes."""
        try:
            device_data = context.get("device", {})
            device_id = device_data.get("id")
            
            if device_id and device_id in self.devices:
                device = self.devices[device_id]
                old_status = device.status
                new_status = device_data.get("status", device.status)
                
                if old_status != new_status:
                    # Log status change
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "device_id": device_id,
                        "device_name": device.name,
                        "event_type": "status_change",
                        "old_status": old_status.value,
                        "new_status": new_status,
                        "user_initiated": False
                    }
                    self.device_logs.append(log_entry)
                    
                    # Update device status
                    device.status = DeviceStatus(new_status)
                    device.last_seen = datetime.utcnow().isoformat()
            
            return {"success": True, "status_tracked": True}
            
        except Exception as e:
            self.logger.error(f"Failed to track device status: {e}")
            return {"success": False, "error": str(e)}
    
    async def _track_scene_execution(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to track scene execution."""
        try:
            scene_data = context.get("scene", {})
            scene_id = scene_data.get("id")
            
            if scene_id and scene_id in self.scenes:
                scene = self.scenes[scene_id]
                scene.last_executed = datetime.utcnow().isoformat()
                
                # Log scene execution
                automation_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "scene_id": scene_id,
                    "scene_name": scene.name,
                    "trigger_type": scene_data.get("trigger_type", "manual"),
                    "devices_affected": len(scene.devices),
                    "success": scene_data.get("success", True)
                }
                self.automation_history.append(automation_record)
                
                # Keep only recent history
                if len(self.automation_history) > 500:
                    self.automation_history = self.automation_history[-500:]
            
            return {"success": True, "scene_tracked": True}
            
        except Exception as e:
            self.logger.error(f"Failed to track scene execution: {e}")
            return {"success": False, "error": str(e)}
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the IoT Smart Home Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.get("/devices")
        async def list_devices():
            """List all IoT devices."""
            return {"devices": [device.dict() for device in self.devices.values()]}
        
        @router.get("/devices/{device_id}")
        async def get_device(device_id: str):
            """Get a specific device."""
            if device_id not in self.devices:
                raise HTTPException(status_code=404, detail="Device not found")
            return self.devices[device_id].dict()
        
        @router.post("/control")
        async def control_device(request: DeviceControl):
            """Control an IoT device."""
            result = await self._control_device_tool(
                request.device_id, request.action, request.parameters
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/scenes")
        async def list_scenes():
            """List all smart home scenes."""
            return {"scenes": [scene.dict() for scene in self.scenes.values()]}
        
        @router.post("/scenes")
        async def create_scene(name: str, device_actions: List[Dict[str, Any]], description: Optional[str] = None, triggers: Optional[List[Dict[str, Any]]] = None):
            """Create a new smart home scene."""
            result = await self._create_scene_tool(name, device_actions, description, triggers)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/scenes/{scene_id}/execute")
        async def execute_scene(scene_id: str):
            """Execute a smart home scene."""
            if scene_id not in self.scenes:
                raise HTTPException(status_code=404, detail="Scene not found")
            
            scene = self.scenes[scene_id]
            results = []
            
            for device_action in scene.devices:
                result = await self._control_device_tool(
                    device_action["device_id"],
                    device_action["action"],
                    device_action.get("parameters", {})
                )
                results.append(result)
            
            return {
                "success": True,
                "scene_id": scene_id,
                "scene_name": scene.name,
                "device_results": results
            }
        
        @router.get("/logs")
        async def get_device_logs(device_id: Optional[str] = None, limit: int = Query(default=100, le=1000)):
            """Get device activity logs."""
            logs = self.device_logs
            if device_id:
                logs = [log for log in logs if log.get("device_id") == device_id]
            
            return {
                "logs": logs[-limit:] if limit > 0 else logs,
                "total_logs": len(logs)
            }
        
        @router.post("/optimize")
        async def optimize_energy_usage(optimization_goal: str, time_period: str = "daily"):
            """Get energy optimization recommendations."""
            result = await self._optimize_energy_usage_tool(optimization_goal, time_period)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/automation-history")
        async def get_automation_history(limit: int = Query(default=50, le=500)):
            """Get scene automation history."""
            return {
                "history": self.automation_history[-limit:] if limit > 0 else self.automation_history,
                "total_executions": len(self.automation_history)
            }
        
        return router
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Smart Home Dashboard."""
        components = super().create_ui_components()
        
        # Add smart home dashboard data
        components["smart_home_dashboard"] = {
            "title": "IoT Smart Home Dashboard",
            "description": "Comprehensive IoT device management and automation",
            "data": {
                "total_devices": len(self.devices),
                "online_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.ONLINE]),
                "total_scenes": len(self.scenes),
                "active_scenes": len([s for s in self.scenes.values() if s.enabled]),
                "recent_activity": len([log for log in self.device_logs if 
                                      datetime.fromisoformat(log["timestamp"]) > datetime.utcnow() - timedelta(hours=1)]),
                "automation_executions": len(self.automation_history)
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the IoT Smart Home Extension."""
        self.logger.info("IoT Smart Home Extension shutting down...")
        
        # Save device states and scene configurations if needed
        # Clear caches
        self.devices.clear()
        self.scenes.clear()
        self.device_logs.clear()
        self.automation_history.clear()
        
        self.logger.info("IoT Smart Home Extension shut down successfully")


# Export the extension class
__all__ = ["IoTSmartHomeExtension"]