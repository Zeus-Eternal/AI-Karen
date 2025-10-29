"""
Zero-downtime authentication system updater.
Handles rolling updates of authentication components without service interruption.
"""

import logging
import asyncio
import signal
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import aiofiles
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class HealthCheck:
    """Health check for authentication services."""
    
    def __init__(self, name: str, check_func: Callable, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_check_time: Optional[datetime] = None
        self.last_result: bool = False
    
    async def run(self) -> bool:
        """Run the health check."""
        try:
            self.last_check_time = datetime.utcnow()
            
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=self.timeout
            )
            
            self.last_result = bool(result)
            return self.last_result
            
        except asyncio.TimeoutError:
            logger.warning(f"Health check {self.name} timed out")
            self.last_result = False
            return False
        except Exception as e:
            logger.error(f"Health check {self.name} failed: {e}")
            self.last_result = False
            return False


class ZeroDowntimeUpdater:
    """Manages zero-downtime updates of authentication system components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checks: List[HealthCheck] = []
        self.update_in_progress = False
        self.rollback_data: Optional[Dict[str, Any]] = None
        self.update_log_file = Path(config.get('log_file', 'update_log.json'))
        
        # Update configuration
        self.max_update_time = config.get('max_update_time_minutes', 30)
        self.health_check_interval = config.get('health_check_interval_seconds', 10)
        self.rollback_threshold = config.get('rollback_threshold_failures', 3)
        self.grace_period = config.get('grace_period_seconds', 30)
        
        # State tracking
        self.consecutive_failures = 0
        self.update_start_time: Optional[datetime] = None
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.shutdown_requested = True
    
    def add_health_check(self, name: str, check_func: Callable, timeout: float = 5.0):
        """Add a health check for monitoring during updates."""
        health_check = HealthCheck(name, check_func, timeout)
        self.health_checks.append(health_check)
        logger.info(f"Added health check: {name}")
    
    async def run_health_checks(self) -> Dict[str, bool]:
        """Run all health checks and return results."""
        results = {}
        
        for health_check in self.health_checks:
            try:
                result = await health_check.run()
                results[health_check.name] = result
            except Exception as e:
                logger.error(f"Health check {health_check.name} failed: {e}")
                results[health_check.name] = False
        
        return results
    
    async def wait_for_healthy_state(self, max_wait_time: int = 300) -> bool:
        """Wait for all health checks to pass."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if self.shutdown_requested:
                return False
            
            health_results = await self.run_health_checks()
            
            if all(health_results.values()):
                logger.info("All health checks passed")
                return True
            
            failed_checks = [name for name, result in health_results.items() if not result]
            logger.info(f"Waiting for health checks to pass. Failed: {failed_checks}")
            
            await asyncio.sleep(self.health_check_interval)
        
        logger.error(f"Health checks did not pass within {max_wait_time} seconds")
        return False
    
    @asynccontextmanager
    async def update_context(self, update_name: str):
        """Context manager for zero-downtime updates."""
        if self.update_in_progress:
            raise RuntimeError("Another update is already in progress")
        
        self.update_in_progress = True
        self.update_start_time = datetime.utcnow()
        self.consecutive_failures = 0
        
        update_info = {
            'update_name': update_name,
            'start_time': self.update_start_time.isoformat(),
            'status': 'started'
        }
        
        try:
            logger.info(f"Starting zero-downtime update: {update_name}")
            await self.log_update_event(update_info)
            
            # Wait for initial healthy state
            if not await self.wait_for_healthy_state(60):
                raise RuntimeError("System not healthy before update")
            
            yield self
            
            # Wait for healthy state after update
            if not await self.wait_for_healthy_state(120):
                raise RuntimeError("System not healthy after update")
            
            update_info['status'] = 'completed'
            update_info['end_time'] = datetime.utcnow().isoformat()
            logger.info(f"Zero-downtime update completed: {update_name}")
            
        except Exception as e:
            update_info['status'] = 'failed'
            update_info['error'] = str(e)
            update_info['end_time'] = datetime.utcnow().isoformat()
            logger.error(f"Zero-downtime update failed: {update_name} - {e}")
            raise
            
        finally:
            await self.log_update_event(update_info)
            self.update_in_progress = False
            self.update_start_time = None
    
    async def rolling_restart_services(self, services: List[str], restart_func: Callable) -> bool:
        """Perform rolling restart of services."""
        logger.info(f"Starting rolling restart of services: {services}")
        
        for service in services:
            if self.shutdown_requested:
                logger.info("Shutdown requested, stopping rolling restart")
                return False
            
            try:
                logger.info(f"Restarting service: {service}")
                
                # Restart the service
                await restart_func(service)
                
                # Wait for service to be healthy
                await asyncio.sleep(5)  # Give service time to start
                
                # Check health
                health_results = await self.run_health_checks()
                if not all(health_results.values()):
                    failed_checks = [name for name, result in health_results.items() if not result]
                    logger.error(f"Health checks failed after restarting {service}: {failed_checks}")
                    return False
                
                logger.info(f"Service {service} restarted successfully")
                
                # Brief pause between service restarts
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to restart service {service}: {e}")
                return False
        
        logger.info("Rolling restart completed successfully")
        return True
    
    async def update_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update configuration with zero downtime."""
        try:
            # Create backup of current configuration
            backup_data = await self.create_config_backup()
            self.rollback_data = backup_data
            
            # Apply configuration updates
            for config_file, updates in config_updates.items():
                await self.apply_config_update(config_file, updates)
            
            # Trigger configuration reload
            await self.reload_configuration()
            
            # Wait for services to pick up new configuration
            await asyncio.sleep(10)
            
            # Verify health after configuration update
            health_results = await self.run_health_checks()
            if not all(health_results.values()):
                logger.error("Health checks failed after configuration update")
                await self.rollback_configuration()
                return False
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            if self.rollback_data:
                await self.rollback_configuration()
            return False
    
    async def create_config_backup(self) -> Dict[str, Any]:
        """Create backup of current configuration."""
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'files': {}
        }
        
        config_dir = Path(self.config.get('config_dir', 'config'))
        
        for config_file in config_dir.glob('*.json'):
            try:
                async with aiofiles.open(config_file, 'r') as f:
                    content = await f.read()
                backup_data['files'][str(config_file)] = content
            except Exception as e:
                logger.error(f"Failed to backup {config_file}: {e}")
        
        return backup_data
    
    async def apply_config_update(self, config_file: str, updates: Dict[str, Any]):
        """Apply updates to a configuration file."""
        config_path = Path(config_file)
        
        # Load current configuration
        if config_path.exists():
            async with aiofiles.open(config_path, 'r') as f:
                content = await f.read()
            current_config = json.loads(content) if content.strip() else {}
        else:
            current_config = {}
        
        # Merge updates
        updated_config = self.merge_config(current_config, updates)
        
        # Write updated configuration
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(json.dumps(updated_config, indent=2))
        
        logger.info(f"Applied configuration update to {config_file}")
    
    def merge_config(self, current: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration updates."""
        result = current.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def reload_configuration(self):
        """Trigger configuration reload in running services."""
        # This would typically send a signal to services to reload config
        # For now, we'll just log the action
        logger.info("Triggering configuration reload")
        
        # In a real implementation, this might:
        # - Send SIGHUP to processes
        # - Call reload endpoints on services
        # - Update configuration in shared storage
        
        await asyncio.sleep(1)  # Simulate reload time
    
    async def rollback_configuration(self):
        """Rollback configuration to previous state."""
        if not self.rollback_data:
            logger.error("No rollback data available")
            return
        
        logger.info("Rolling back configuration changes")
        
        try:
            for file_path, content in self.rollback_data['files'].items():
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(content)
            
            # Trigger configuration reload
            await self.reload_configuration()
            
            logger.info("Configuration rollback completed")
            
        except Exception as e:
            logger.error(f"Configuration rollback failed: {e}")
    
    async def monitor_update_progress(self):
        """Monitor update progress and handle failures."""
        while self.update_in_progress and not self.shutdown_requested:
            try:
                # Check if update has exceeded maximum time
                if (self.update_start_time and 
                    datetime.utcnow() - self.update_start_time > timedelta(minutes=self.max_update_time)):
                    logger.error("Update exceeded maximum time limit")
                    if self.rollback_data:
                        await self.rollback_configuration()
                    break
                
                # Run health checks
                health_results = await self.run_health_checks()
                
                if all(health_results.values()):
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    failed_checks = [name for name, result in health_results.items() if not result]
                    logger.warning(f"Health check failures ({self.consecutive_failures}): {failed_checks}")
                    
                    # Trigger rollback if threshold exceeded
                    if self.consecutive_failures >= self.rollback_threshold:
                        logger.error("Health check failure threshold exceeded, triggering rollback")
                        if self.rollback_data:
                            await self.rollback_configuration()
                        break
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring update progress: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def log_update_event(self, event_data: Dict[str, Any]):
        """Log update events for audit trail."""
        try:
            # Load existing log
            if self.update_log_file.exists():
                async with aiofiles.open(self.update_log_file, 'r') as f:
                    content = await f.read()
                log_data = json.loads(content) if content.strip() else {'events': []}
            else:
                log_data = {'events': []}
            
            # Add new event
            log_data['events'].append(event_data)
            
            # Keep only last 1000 events
            log_data['events'] = log_data['events'][-1000:]
            
            # Save log
            self.update_log_file.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.update_log_file, 'w') as f:
                await f.write(json.dumps(log_data, indent=2))
        
        except Exception as e:
            logger.error(f"Failed to log update event: {e}")
    
    async def graceful_shutdown(self):
        """Perform graceful shutdown during updates."""
        logger.info("Starting graceful shutdown")
        
        # Wait for current operations to complete
        if self.update_in_progress:
            logger.info(f"Waiting up to {self.grace_period} seconds for update to complete")
            
            start_time = time.time()
            while (self.update_in_progress and 
                   time.time() - start_time < self.grace_period):
                await asyncio.sleep(1)
            
            if self.update_in_progress:
                logger.warning("Update did not complete within grace period")
        
        logger.info("Graceful shutdown completed")


# Example health check functions
async def check_auth_service_health() -> bool:
    """Example health check for authentication service."""
    try:
        # This would typically make an HTTP request to a health endpoint
        # For now, we'll simulate a health check
        await asyncio.sleep(0.1)  # Simulate network call
        return True  # Assume healthy for example
    except Exception:
        return False


async def check_database_health() -> bool:
    """Example health check for database connectivity."""
    try:
        # This would typically test database connectivity
        await asyncio.sleep(0.1)  # Simulate database query
        return True  # Assume healthy for example
    except Exception:
        return False


async def check_extension_api_health() -> bool:
    """Example health check for extension API."""
    try:
        # This would typically test extension API endpoints
        await asyncio.sleep(0.1)  # Simulate API call
        return True  # Assume healthy for example
    except Exception:
        return False


async def example_service_restart(service_name: str):
    """Example service restart function."""
    logger.info(f"Restarting service: {service_name}")
    # This would typically:
    # - Stop the service gracefully
    # - Wait for it to shut down
    # - Start the service again
    # - Wait for it to be ready
    await asyncio.sleep(2)  # Simulate restart time


async def main():
    """Example usage of zero-downtime updater."""
    config = {
        'max_update_time_minutes': 30,
        'health_check_interval_seconds': 10,
        'rollback_threshold_failures': 3,
        'grace_period_seconds': 30,
        'config_dir': 'config',
        'log_file': 'update_log.json'
    }
    
    updater = ZeroDowntimeUpdater(config)
    
    # Add health checks
    updater.add_health_check('auth_service', check_auth_service_health)
    updater.add_health_check('database', check_database_health)
    updater.add_health_check('extension_api', check_extension_api_health)
    
    try:
        # Example: Update authentication configuration
        async with updater.update_context('auth_config_update'):
            config_updates = {
                'auth.json': {
                    'jwt_expiry_minutes': 60,
                    'refresh_token_expiry_days': 30
                }
            }
            
            success = await updater.update_configuration(config_updates)
            if not success:
                raise RuntimeError("Configuration update failed")
        
        # Example: Rolling restart of services
        async with updater.update_context('service_restart'):
            services = ['auth_service', 'extension_api', 'background_tasks']
            success = await updater.rolling_restart_services(services, example_service_restart)
            if not success:
                raise RuntimeError("Service restart failed")
        
        logger.info("Zero-downtime update completed successfully")
        
    except Exception as e:
        logger.error(f"Zero-downtime update failed: {e}")
    
    finally:
        await updater.graceful_shutdown()


if __name__ == "__main__":
    asyncio.run(main())