"""
Configuration deployment and rollback tools for extension authentication system.
Handles deploying configuration changes across environments with rollback capability.
"""

import logging
import json
import yaml
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

class ConfigDeployer:
    """Handles deployment and rollback of configuration changes."""
    
    def __init__(self, config_dir: Path, backup_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir)
        self.backup_dir = backup_dir or (self.config_dir.parent / "config_backups")
        self.deployment_log_file = self.backup_dir / "deployment_log.json"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_config_checksum(self, config_path: Path) -> str:
        """Calculate checksum of configuration file."""
        if not config_path.exists():
            return ""
        
        with open(config_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()[:16]
    
    async def backup_current_config(self, config_files: List[str]) -> str:
        """Create backup of current configuration files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        backup_manifest = {
            'backup_id': backup_id,
            'timestamp': timestamp,
            'files': {},
            'checksums': {}
        }
        
        for config_file in config_files:
            source_path = self.config_dir / config_file
            if source_path.exists():
                dest_path = backup_path / config_file
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                
                # Record in manifest
                backup_manifest['files'][config_file] = str(dest_path)
                backup_manifest['checksums'][config_file] = self.calculate_config_checksum(source_path)
        
        # Save backup manifest
        manifest_path = backup_path / "manifest.json"
        async with aiofiles.open(manifest_path, 'w') as f:
            await f.write(json.dumps(backup_manifest, indent=2))
        
        logger.info(f"Created configuration backup: {backup_id}")
        return backup_id
    
    async def deploy_config(self, 
                          config_updates: Dict[str, Any], 
                          environment: str = "production") -> Dict[str, Any]:
        """Deploy configuration updates with backup."""
        deployment_id = f"deploy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Validate configuration updates
            validation_result = await self.validate_config_updates(config_updates)
            if not validation_result['valid']:
                raise ValueError(f"Configuration validation failed: {validation_result['errors']}")
            
            # Determine which files will be affected
            affected_files = list(config_updates.keys())
            
            # Create backup
            backup_id = await self.backup_current_config(affected_files)
            
            # Apply configuration updates
            deployment_result = {
                'deployment_id': deployment_id,
                'backup_id': backup_id,
                'environment': environment,
                'timestamp': datetime.utcnow().isoformat(),
                'files_updated': [],
                'errors': [],
                'success': True
            }
            
            for config_file, updates in config_updates.items():
                try:
                    await self.update_config_file(config_file, updates, environment)
                    deployment_result['files_updated'].append(config_file)
                    logger.info(f"Updated configuration file: {config_file}")
                    
                except Exception as e:
                    error_msg = f"Failed to update {config_file}: {e}"
                    logger.error(error_msg)
                    deployment_result['errors'].append(error_msg)
                    deployment_result['success'] = False
            
            # Log deployment
            await self.log_deployment(deployment_result)
            
            # Validate deployed configuration
            if deployment_result['success']:
                post_deploy_validation = await self.validate_deployed_config(environment)
                if not post_deploy_validation['valid']:
                    logger.warning("Post-deployment validation failed, consider rollback")
                    deployment_result['post_validation_warnings'] = post_deploy_validation['errors']
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Configuration deployment failed: {e}")
            return {
                'deployment_id': deployment_id,
                'environment': environment,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    async def update_config_file(self, config_file: str, updates: Dict[str, Any], environment: str):
        """Update a specific configuration file."""
        config_path = self.config_dir / config_file
        
        # Load existing configuration
        if config_path.exists():
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                async with aiofiles.open(config_path, 'r') as f:
                    content = await f.read()
                current_config = yaml.safe_load(content) or {}
            else:
                async with aiofiles.open(config_path, 'r') as f:
                    content = await f.read()
                current_config = json.loads(content) if content.strip() else {}
        else:
            current_config = {}
        
        # Apply updates
        updated_config = self.merge_config(current_config, updates)
        
        # Add environment-specific metadata
        if 'metadata' not in updated_config:
            updated_config['metadata'] = {}
        
        updated_config['metadata'].update({
            'environment': environment,
            'last_updated': datetime.utcnow().isoformat(),
            'deployed_by': 'config_deployer'
        })
        
        # Write updated configuration
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(yaml.dump(updated_config, default_flow_style=False))
        else:
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(json.dumps(updated_config, indent=2))
    
    def merge_config(self, current: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration updates."""
        result = current.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def rollback_config(self, backup_id: str) -> Dict[str, Any]:
        """Rollback configuration to a previous backup."""
        backup_path = self.backup_dir / backup_id
        manifest_path = backup_path / "manifest.json"
        
        if not manifest_path.exists():
            raise ValueError(f"Backup {backup_id} not found or invalid")
        
        # Load backup manifest
        async with aiofiles.open(manifest_path, 'r') as f:
            content = await f.read()
        manifest = json.loads(content)
        
        rollback_result = {
            'rollback_id': f"rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'backup_id': backup_id,
            'timestamp': datetime.utcnow().isoformat(),
            'files_restored': [],
            'errors': [],
            'success': True
        }
        
        try:
            # Create backup of current state before rollback
            current_files = list(manifest['files'].keys())
            current_backup_id = await self.backup_current_config(current_files)
            rollback_result['current_backup_id'] = current_backup_id
            
            # Restore files from backup
            for config_file, backup_file_path in manifest['files'].items():
                try:
                    source_path = Path(backup_file_path)
                    dest_path = self.config_dir / config_file
                    
                    if source_path.exists():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                        rollback_result['files_restored'].append(config_file)
                        logger.info(f"Restored configuration file: {config_file}")
                    else:
                        # Remove file if it didn't exist in backup
                        if dest_path.exists():
                            dest_path.unlink()
                            rollback_result['files_restored'].append(f"{config_file} (removed)")
                
                except Exception as e:
                    error_msg = f"Failed to restore {config_file}: {e}"
                    logger.error(error_msg)
                    rollback_result['errors'].append(error_msg)
                    rollback_result['success'] = False
            
            # Log rollback
            await self.log_deployment(rollback_result)
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Configuration rollback failed: {e}")
            rollback_result['success'] = False
            rollback_result['error'] = str(e)
            return rollback_result
    
    async def validate_config_updates(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration updates before deployment."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        for config_file, updates in config_updates.items():
            try:
                # Check file extension
                if not any(config_file.endswith(ext) for ext in ['.json', '.yaml', '.yml']):
                    validation_result['errors'].append(f"Unsupported config file type: {config_file}")
                    continue
                
                # Validate JSON/YAML structure
                if isinstance(updates, dict):
                    # Check for required fields based on config type
                    if 'auth' in config_file.lower():
                        await self.validate_auth_config(updates, validation_result)
                    elif 'extension' in config_file.lower():
                        await self.validate_extension_config(updates, validation_result)
                else:
                    validation_result['errors'].append(f"Invalid config format for {config_file}")
            
            except Exception as e:
                validation_result['errors'].append(f"Validation error for {config_file}: {e}")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    async def validate_auth_config(self, config: Dict[str, Any], result: Dict[str, Any]):
        """Validate authentication configuration."""
        required_fields = ['jwt_secret_key', 'token_expiry_minutes']
        
        for field in required_fields:
            if field not in config:
                result['errors'].append(f"Missing required auth config field: {field}")
        
        # Validate JWT secret key strength
        if 'jwt_secret_key' in config:
            secret = config['jwt_secret_key']
            if len(secret) < 32:
                result['warnings'].append("JWT secret key should be at least 32 characters")
        
        # Validate token expiry
        if 'token_expiry_minutes' in config:
            expiry = config['token_expiry_minutes']
            if not isinstance(expiry, int) or expiry <= 0:
                result['errors'].append("token_expiry_minutes must be a positive integer")
    
    async def validate_extension_config(self, config: Dict[str, Any], result: Dict[str, Any]):
        """Validate extension configuration."""
        if 'extensions' in config:
            extensions = config['extensions']
            if not isinstance(extensions, dict):
                result['errors'].append("extensions must be a dictionary")
                return
            
            for ext_name, ext_config in extensions.items():
                if not isinstance(ext_config, dict):
                    result['errors'].append(f"Extension {ext_name} config must be a dictionary")
                    continue
                
                # Check for required extension fields
                if 'enabled' not in ext_config:
                    result['warnings'].append(f"Extension {ext_name} missing 'enabled' field")
    
    async def validate_deployed_config(self, environment: str) -> Dict[str, Any]:
        """Validate configuration after deployment."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if configuration files are readable
            config_files = list(self.config_dir.glob("*.json")) + list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
            
            for config_file in config_files:
                try:
                    if config_file.suffix.lower() in ['.yaml', '.yml']:
                        async with aiofiles.open(config_file, 'r') as f:
                            content = await f.read()
                        yaml.safe_load(content)
                    else:
                        async with aiofiles.open(config_file, 'r') as f:
                            content = await f.read()
                        json.loads(content)
                
                except Exception as e:
                    validation_result['errors'].append(f"Invalid config file {config_file.name}: {e}")
            
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['errors'].append(f"Post-deployment validation failed: {e}")
            validation_result['valid'] = False
        
        return validation_result
    
    async def log_deployment(self, deployment_result: Dict[str, Any]):
        """Log deployment/rollback operation."""
        try:
            # Load existing log
            if self.deployment_log_file.exists():
                async with aiofiles.open(self.deployment_log_file, 'r') as f:
                    content = await f.read()
                log_data = json.loads(content) if content.strip() else {'deployments': []}
            else:
                log_data = {'deployments': []}
            
            # Add new deployment
            log_data['deployments'].append(deployment_result)
            
            # Keep only last 100 deployments
            log_data['deployments'] = log_data['deployments'][-100:]
            
            # Save log
            async with aiofiles.open(self.deployment_log_file, 'w') as f:
                await f.write(json.dumps(log_data, indent=2))
        
        except Exception as e:
            logger.error(f"Failed to log deployment: {e}")
    
    async def get_deployment_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get deployment history."""
        try:
            if not self.deployment_log_file.exists():
                return []
            
            async with aiofiles.open(self.deployment_log_file, 'r') as f:
                content = await f.read()
            
            log_data = json.loads(content) if content.strip() else {'deployments': []}
            deployments = log_data.get('deployments', [])
            
            # Return most recent deployments
            return deployments[-limit:] if deployments else []
        
        except Exception as e:
            logger.error(f"Failed to get deployment history: {e}")
            return []
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available configuration backups."""
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                    manifest_path = backup_dir / "manifest.json"
                    
                    if manifest_path.exists():
                        async with aiofiles.open(manifest_path, 'r') as f:
                            content = await f.read()
                        manifest = json.loads(content)
                        
                        backups.append({
                            'backup_id': manifest['backup_id'],
                            'timestamp': manifest['timestamp'],
                            'files_count': len(manifest['files']),
                            'path': str(backup_dir)
                        })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups


async def main():
    """CLI interface for configuration deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuration Deployment Tool')
    parser.add_argument('command', choices=['deploy', 'rollback', 'status', 'list-backups'], 
                       help='Deployment command')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--backup-id', help='Backup ID for rollback')
    parser.add_argument('--environment', default='production', help='Target environment')
    parser.add_argument('--config-file', help='Configuration file to deploy')
    
    args = parser.parse_args()
    
    deployer = ConfigDeployer(Path(args.config_dir))
    
    try:
        if args.command == 'deploy':
            if not args.config_file:
                print("Config file required for deployment")
                return
            
            # Load configuration updates from file
            config_path = Path(args.config_file)
            if not config_path.exists():
                print(f"Configuration file not found: {config_path}")
                return
            
            with open(config_path) as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_updates = {config_path.name: yaml.safe_load(f)}
                else:
                    config_updates = {config_path.name: json.load(f)}
            
            result = await deployer.deploy_config(config_updates, args.environment)
            
            if result['success']:
                print(f"Deployment successful: {result['deployment_id']}")
                print(f"Backup created: {result['backup_id']}")
            else:
                print(f"Deployment failed: {result.get('error', 'Unknown error')}")
        
        elif args.command == 'rollback':
            if not args.backup_id:
                print("Backup ID required for rollback")
                return
            
            result = await deployer.rollback_config(args.backup_id)
            
            if result['success']:
                print(f"Rollback successful: {result['rollback_id']}")
            else:
                print(f"Rollback failed: {result.get('error', 'Unknown error')}")
        
        elif args.command == 'status':
            history = await deployer.get_deployment_history(10)
            
            if history:
                print("Recent deployments:")
                for deployment in reversed(history):
                    status = "✓" if deployment.get('success', False) else "✗"
                    print(f"  {status} {deployment.get('deployment_id', 'unknown')} - {deployment.get('timestamp', 'unknown')}")
            else:
                print("No deployment history found")
        
        elif args.command == 'list-backups':
            backups = await deployer.list_backups()
            
            if backups:
                print("Available backups:")
                for backup in backups:
                    print(f"  {backup['backup_id']} - {backup['timestamp']} ({backup['files_count']} files)")
            else:
                print("No backups found")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())