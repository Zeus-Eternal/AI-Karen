# CoPilot Architecture Rollback Plan

## Overview

This document outlines the rollback plan for the CoPilot Architecture deployment. The rollback plan ensures that we can quickly and safely revert to a previous stable version in case of issues with a new deployment.

## Rollback Triggers

### Critical Triggers (Immediate Rollback Required)
- Complete service outage affecting all users
- Data corruption or loss
- Critical security vulnerabilities
- Performance degradation impacting core functionality (>50% response time increase)
- Authentication/authorization failures preventing user access

### Major Triggers (Rollback Within 1 Hour)
- Significant feature breakage affecting core user workflows
- High error rates (>10% of requests failing)
- Memory leaks causing service instability
- Database connection failures

### Minor Triggers (Rollback Within 24 Hours)
- UI/UX issues affecting user experience
- Non-critical feature failures
- Performance degradation not impacting core functionality
- Integration issues with external systems

## Pre-Rollback Checklist

Before initiating a rollback, complete the following checks:

1. **Identify the Issue**
   - [ ] Document the specific issue or failure
   - [ ] Determine the scope of impact (users, features, systems)
   - [ ] Collect relevant logs and metrics
   - [ ] Identify when the issue started (correlate with deployment)

2. **Assess Rollback Necessity**
   - [ ] Confirm the issue is caused by the new deployment
   - [ ] Determine if a hotfix is possible instead of rollback
   - [ ] Estimate time required for rollback vs. fix
   - [ ] Get approval from stakeholders for rollback

3. **Prepare for Rollback**
   - [ ] Identify the target version to rollback to
   - [ ] Verify backup availability and integrity
   - [ ] Notify all stakeholders about planned rollback
   - [ ] Prepare communication for users
   - [ ] Schedule maintenance window if needed

## Rollback Procedures

### 1. Quick Rollback (Using Scripts)

This is the preferred method for most rollback scenarios.

#### Steps:
1. **Stop Current Services**
   ```bash
   ./scripts/stop-copilot.sh --remove-containers
   ```

2. **Restore from Backup**
   ```bash
   ./scripts/restore-copilot.sh
   ```
   - Select the appropriate backup from the list
   - Confirm the restore operation

3. **Start Services**
   ```bash
   ./scripts/deploy-copilot.sh
   ```

4. **Verify Rollback**
   - Check service health
   - Verify functionality
   - Monitor metrics

### 2. Manual Rollback (Docker Compose)

Use this method if automated scripts fail or for more control.

#### Steps:
1. **Stop All Services**
   ```bash
   docker-compose -f docker-compose-copilot.yml down
   ```

2. **Restore Configuration**
   ```bash
   # Restore previous configuration files
   cp -r config.backup.<timestamp>/* config/
   cp docker-compose-copilot.backup.<timestamp> docker-compose-copilot.yml
   ```

3. **Restore Database**
   ```bash
   # Start PostgreSQL
   docker-compose -f docker-compose-copilot.yml up -d postgres-copilot
   
   # Wait for PostgreSQL to be ready
   sleep 30
   
   # Restore database
   gunzip -c backups/copilot-backup-<timestamp>/database/postgres.sql.gz | docker-compose -f docker-compose-copilot.yml exec -T postgres-copilot psql -U karen_user -d ai_karen_copilot
   ```

4. **Restore Redis**
   ```bash
   # Start Redis
   docker-compose -f docker-compose-copilot.yml up -d redis-copilot
   
   # Wait for Redis to be ready
   sleep 10
   
   # Get Redis container ID
   REDIS_CONTAINER=$(docker-compose -f docker-compose-copilot.yml ps -q redis-copilot)
   
   # Copy RDB file to container
   docker cp backups/copilot-backup-<timestamp>/redis/dump.rdb $REDIS_CONTAINER:/data/dump.rdb
   
   # Restart Redis to load the new data
   docker-compose -f docker-compose-copilot.yml restart redis-copilot
   ```

5. **Restore Other Services**
   ```bash
   # Start remaining services
   docker-compose -f docker-compose-copilot.yml up -d
   ```

6. **Verify Rollback**
   ```bash
   # Check service status
   docker-compose -f docker-compose-copilot.yml ps
   
   # Check health endpoints
   curl http://localhost:8000/health
   curl http://localhost:8010
   ```

### 3. Git-Based Rollback

Use this method if the issue is in the codebase.

#### Steps:
1. **Identify Last Known Good Commit**
   ```bash
   git log --oneline -10
   ```

2. **Rollback Code**
   ```bash
   git checkout <commit-hash>
   ```

3. **Rebuild and Deploy**
   ```bash
   ./scripts/deploy-copilot.sh
   ```

## Post-Rollback Procedures

### 1. Verification
- [ ] All services are running and healthy
- [ ] Core functionality is working
- [ ] Error rates are back to normal
- [ ] Performance metrics are within acceptable ranges
- [ ] Data integrity is maintained
- [ ] Authentication and authorization are working

### 2. Monitoring
- [ ] Monitor system metrics for at least 1 hour after rollback
- [ ] Check for any error spikes or unusual behavior
- [ ] Verify user activity and engagement levels
- [ ] Monitor database performance and connection counts

### 3. Communication
- [ ] Notify all stakeholders that rollback is complete
- [ ] Communicate with users about service restoration
- [ ] Document the rollback and root cause
- [ ] Schedule post-mortem meeting if needed

### 4. Investigation
- [ ] Analyze what caused the rollback
- [ ] Document lessons learned
- [ ] Update deployment procedures to prevent recurrence
- [ ] Create fixes for the issues that caused the rollback

## Rollback Time Estimates

| Scenario | Estimated Time | Downtime |
|----------|----------------|-----------|
| Quick Rollback (Scripts) | 15-30 minutes | 10-20 minutes |
| Manual Rollback (Docker) | 30-60 minutes | 20-40 minutes |
| Git-Based Rollback | 45-90 minutes | 30-60 minutes |

## Rollback Testing

### Testing Procedure
1. **Test in Staging Environment**
   - Perform rollback in staging first
   - Verify all functionality works
   - Measure performance metrics
   - Check for any data issues

2. **Test Critical Paths**
   - User authentication and authorization
   - Core CoPilot functionality
   - Agent integration
   - Thread and session management
   - Response formatting
   - Extension loading and execution

3. **Performance Testing**
   - Response times for critical endpoints
   - Database query performance
   - Memory and CPU usage
   - Concurrent user handling

## Rollback Fail-Safe

### If Rollback Fails
1. **Stop All Services**
   ```bash
   docker-compose -f docker-compose-copilot.yml down
   ```

2. **Restore from Older Backup**
   ```bash
   # Try the previous backup
   ./scripts/restore-copilot.sh
   # Select an older backup
   ```

3. **Manual Recovery**
   - If all automated methods fail, use the manual recovery procedure
   - Rebuild services from scratch using known good configuration

### Emergency Contacts
- **Primary Contact**: DevOps Lead
- **Secondary Contact**: Engineering Manager
- **Tertiary Contact**: CTO

## Rollback Documentation

### Log Locations
- **Application Logs**: `/var/log/ai-karen-copilot/`
- **Database Logs**: PostgreSQL container logs
- **System Logs**: Docker container logs
- **Metrics**: Prometheus and Grafana

### Backup Locations
- **Automated Backups**: `backups/` directory
- **Manual Backups**: `backups/manual/` directory
- **Configuration Backups**: `config.backup.<timestamp>/`

### Documentation Updates
- Update this document after each rollback
- Document any changes to rollback procedures
- Record lessons learned and improvements

## Prevention Measures

### Pre-Deployment Checks
1. **Automated Testing**
   - Run all unit and integration tests
   - Perform load testing
   - Check security vulnerabilities

2. **Staging Deployment**
   - Deploy to staging environment first
   - Verify all functionality
   - Test with production-like data

3. **Canary Releases**
   - Deploy to a subset of users first
   - Monitor metrics closely
   - Gradually roll out to all users

### Monitoring and Alerting
1. **Deploy-Time Monitoring**
   - Monitor error rates during deployment
   - Set up alerts for critical metrics
   - Have rollback scripts ready to execute

2. **Post-Deployment Monitoring**
   - Monitor system for at least 1 hour after deployment
   - Check for any unusual behavior
   - Be prepared to rollback if issues arise

## Conclusion

This rollback plan provides a structured approach to reverting the CoPilot Architecture deployment in case of issues. By following this plan, we can ensure minimal downtime and maintain system stability even when deployments encounter problems.

Regular testing of the rollback procedures is recommended to ensure they work correctly when needed.