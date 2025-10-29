#!/usr/bin/env python3
"""
Main deployment script for authentication system.
Orchestrates database migrations, configuration deployment, and zero-downtime updates.
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from migration_runner import MigrationRunner
from config_deployer import ConfigDeployer
from zero_downtime_updater import ZeroDowntimeUpdater
from auth_monitoring import initialize_auth_monitor

logger = logging.getLogger(__name__)

class AuthSystemDeployer:
    """Main deployer for authentication system components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config.get('database', {})
        self.deployment_config = config.get('deployment', {})
        
        # Initialize components
        self.migration_runner = MigrationRunner(self.db_config)
        self.config_deployer = ConfigDeployer(
            Path(config.get('config_dir', 'config'))
        )
        self.zero_downtime_updater = ZeroDowntimeUpdater(
            self.deployment_config
        )
        
        # Initialize monitoring
        if config.get('monitoring', {}).get('enabled', True):
            self.auth_monitor = initialize_auth_monitor(
                config.get('monitoring', {})
            )
        else:
            self.auth_monitor = None
    
    async def deploy_full_system(self, environment: str = "production") -> Dict[str, Any]:
        """Deploy the complete authentication system."""
        deployment_result = {
            'environment': environment,
            'started_at': asyncio.get_event_loop().time(),
            'steps': {},
            'success': True,
            'errors': []
        }
        
        try:
            logger.info(f"Starting full authentication system deployment for {environment}")
            
            # Step 1: Run database migrations
            logger.info("Step 1: Running database migrations")
            migration_result = await self.migration_runner.run_migrations()
            deployment_result['steps']['migrations'] = migration_result
            
            if migration_result.get('errors'):
                raise RuntimeError(f"Database migrations failed: {migration_result['errors']}")
            
            # Step 2: Deploy configuration
            logger.info("Step 2: Deploying configuration")
            config_updates = self.get_config_updates_for_environment(environment)
            
            if config_updates:
                config_result = await self.config_deployer.deploy_config(
                    config_updates, environment
                )
                deployment_result['steps']['configuration'] = config_result
                
                if not config_result.get('success', False):
                    raise RuntimeError(f"Configuration deployment failed: {config_result.get('error')}")
            else:
                deployment_result['steps']['configuration'] = {'message': 'No configuration updates needed'}
            
            # Step 3: Zero-downtime service update
            logger.info("Step 3: Performing zero-downtime service update")
            
            async with self.zero_downtime_updater.update_context(f'auth_system_deploy_{environment}'):
                # Add health checks
                self.setup_health_checks()
                
                # Update services
                service_result = await self.update_services(environment)
                deployment_result['steps']['services'] = service_result
                
                if not service_result.get('success', False):
                    raise RuntimeError(f"Service update failed: {service_result.get('error')}")
            
            # Step 4: Start monitoring
            if self.auth_monitor:
                logger.info("Step 4: Starting authentication monitoring")
                asyncio.create_task(self.auth_monitor.start_monitoring())
                deployment_result['steps']['monitoring'] = {'status': 'started'}
            
            deployment_result['completed_at'] = asyncio.get_event_loop().time()
            deployment_result['duration_seconds'] = (
                deployment_result['completed_at'] - deployment_result['started_at']
            )
            
            logger.info(f"Authentication system deployment completed successfully in {deployment_result['duration_seconds']:.1f}s")
            
        except Exception as e:
            deployment_result['success'] = False
            deployment_result['errors'].append(str(e))
            deployment_result['failed_at'] = asyncio.get_event_loop().time()
            
            logger.error(f"Authentication system deployment failed: {e}")
            
            # Attempt rollback
            await self.rollback_deployment(deployment_result)
        
        return deployment_result
    
    def get_config_updates_for_environment(self, environment: str) -> Dict[str, Any]:
        """Get configuration updates for specific environment."""
        config_updates = {}
        
        # Auth configuration
        auth_config = {
            'environment': environment,
            'jwt_secret_key': self.config.get('jwt_secret_key', 'change-me-in-production'),
            'token_expiry_minutes': 60 if environment == 'production' else 1440,
            'refresh_token_expiry_days': 30,
            'rate_limiting': {
                'enabled': environment == 'production',
                'requests_per_minute': 100 if environment == 'production' else 1000
            },
            'logging': {
                'level': 'INFO' if environment == 'production' else 'DEBUG',
                'audit_enabled': True
            }
        }
        
        config_updates['auth.json'] = auth_config
        
        # Extension configuration
        extension_config = {
            'environment': environment,
            'authentication': {
                'required': True,
                'bypass_dev_mode': environment != 'production'
            },
            'permissions': {
                'default_permissions': ['read'] if environment == 'production' else ['read', 'write'],
                'admin_permissions': ['read', 'write', 'admin', 'background_tasks']
            },
            'health_checks': {
                'enabled': True,
                'interval_seconds': 30 if environment == 'production' else 60
            }
        }
        
        config_updates['extensions.json'] = extension_config
        
        return config_updates
    
    def setup_health_checks(self):
        """Setup health checks for zero-downtime updates."""
        async def check_database():
            try:
                status = await self.migration_runner.get_migration_status()
                return status.get('total_migrations', 0) > 0
            except Exception:
                return False
        
        async def check_auth_endpoints():
            # This would typically make HTTP requests to auth endpoints
            # For now, simulate a health check
            await asyncio.sleep(0.1)
            return True
        
        async def check_extension_apis():
            # This would typically test extension API endpoints
            await asyncio.sleep(0.1)
            return True
        
        self.zero_downtime_updater.add_health_check('database', check_database)
        self.zero_downtime_updater.add_health_check('auth_endpoints', check_auth_endpoints)
        self.zero_downtime_updater.add_health_check('extension_apis', check_extension_apis)
    
    async def update_services(self, environment: str) -> Dict[str, Any]:
        """Update services during deployment."""
        try:
            # This would typically restart or reload services
            # For now, simulate service updates
            
            services_to_update = [
                'auth_service',
                'extension_api',
                'background_tasks'
            ]
            
            async def restart_service(service_name: str):
                logger.info(f"Restarting service: {service_name}")
                await asyncio.sleep(1)  # Simulate restart time
                logger.info(f"Service {service_name} restarted successfully")
            
            # Perform rolling restart
            success = await self.zero_downtime_updater.rolling_restart_services(
                services_to_update, restart_service
            )
            
            return {
                'success': success,
                'services_updated': services_to_update if success else [],
                'message': 'Services updated successfully' if success else 'Service update failed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def rollback_deployment(self, deployment_result: Dict[str, Any]):
        """Rollback deployment in case of failure."""
        logger.info("Attempting deployment rollback")
        
        try:
            # Rollback configuration if it was deployed
            config_step = deployment_result.get('steps', {}).get('configuration')
            if config_step and config_step.get('backup_id'):
                logger.info("Rolling back configuration")
                await self.config_deployer.rollback_config(config_step['backup_id'])
            
            # Rollback migrations if they were applied
            migration_step = deployment_result.get('steps', {}).get('migrations')
            if migration_step and migration_step.get('applied'):
                logger.info("Rolling back database migrations")
                # Rollback the last applied migration
                for migration in reversed(migration_step['applied']):
                    await self.migration_runner.rollback_migration(
                        migration['migration_id']
                    )
            
            logger.info("Deployment rollback completed")
            
        except Exception as e:
            logger.error(f"Deployment rollback failed: {e}")
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        status = {
            'migrations': await self.migration_runner.get_migration_status(),
            'configuration': await self.config_deployer.get_deployment_history(5),
            'monitoring': None
        }
        
        if self.auth_monitor:
            status['monitoring'] = self.auth_monitor.get_monitoring_status()
        
        return status


async def main():
    """CLI interface for authentication system deployment."""
    parser = argparse.ArgumentParser(description='Authentication System Deployer')
    parser.add_argument('command', choices=['deploy', 'status', 'rollback'], 
                       help='Deployment command')
    parser.add_argument('--environment', default='production', 
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--backup-id', help='Backup ID for rollback')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path(__file__).parent / "deployment_config.json"
    
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': '',
                'database': 'kari'
            },
            'config_dir': 'config',
            'deployment': {
                'max_update_time_minutes': 30,
                'health_check_interval_seconds': 10,
                'rollback_threshold_failures': 3,
                'grace_period_seconds': 30
            },
            'monitoring': {
                'enabled': True,
                'success_rate_threshold': 0.95,
                'response_time_threshold_ms': 1000,
                'error_rate_threshold': 0.05
            },
            'jwt_secret_key': 'your-secret-key-change-in-production'
        }
    
    deployer = AuthSystemDeployer(config)
    
    try:
        if args.command == 'deploy':
            result = await deployer.deploy_full_system(args.environment)
            
            if result['success']:
                print(f"Deployment successful in {result.get('duration_seconds', 0):.1f}s")
                print(f"Steps completed: {list(result['steps'].keys())}")
            else:
                print(f"Deployment failed: {result.get('errors', [])}")
                return 1
        
        elif args.command == 'status':
            status = await deployer.get_deployment_status()
            print(json.dumps(status, indent=2, default=str))
        
        elif args.command == 'rollback':
            if not args.backup_id:
                print("Backup ID required for rollback")
                return 1
            
            await deployer.config_deployer.rollback_config(args.backup_id)
            print(f"Rollback completed for backup: {args.backup_id}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Deployment command failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)