# Prompt-Driven Automation Extension

The Prompt-Driven Automation Extension is Kari's flagship automation platform that enables users to create complex workflows using natural language descriptions. This extension represents Kari's answer to traditional automation platforms like N8N, but powered by AI understanding rather than visual workflow builders.

## 🌟 Key Features

### AI-Native Workflow Creation
- **Natural Language Processing**: Describe workflows in plain English
- **Automatic Plugin Discovery**: AI discovers and configures suitable plugins
- **Self-Adapting Workflows**: Learns from execution results and user feedback
- **Template-Based Quick Start**: Pre-built templates for common automation scenarios

### Intelligent Orchestration
- **Plugin Composition**: Seamlessly orchestrate multiple plugins in workflows
- **Conditional Logic**: Smart step conditions and branching
- **Error Handling**: Automatic retry mechanisms and failure recovery
- **Parallel Execution**: Run independent steps simultaneously for better performance

### Comprehensive Monitoring
- **Real-time Dashboard**: Live monitoring of workflow executions
- **Performance Analytics**: Success rates, duration analysis, and optimization insights
- **Execution History**: Detailed logs of all workflow runs
- **Smart Alerts**: Proactive notifications for failures and performance issues

### Flexible Triggers
- **Manual Execution**: On-demand workflow execution
- **Scheduled Runs**: Cron-based scheduling
- **Webhook Triggers**: External system integration
- **Event-Driven**: React to system events and changes

## 🚀 Quick Start

### Creating Your First Workflow

1. **Open Automation Studio**: Navigate to the Automation Studio in your Kari interface
2. **Describe Your Workflow**: Use natural language to describe what you want to automate
   ```
   Example: "Monitor our GitHub repo and notify Slack when tests fail"
   ```
3. **Review AI Analysis**: The system will analyze your request and suggest plugins
4. **Create Workflow**: Click "Create Workflow" to generate your automation
5. **Test & Deploy**: Execute the workflow and activate it for production use

### Example Workflows

#### GitHub to Slack Monitoring
```
Prompt: "Monitor our GitHub repository for failed CI builds and send alerts to our #dev-alerts Slack channel"

Generated Workflow:
1. Monitor GitHub repository events
2. Filter for CI/CD pipeline failures
3. Format alert message with build details
4. Send notification to Slack channel
```

#### File Processing Pipeline
```
Prompt: "When new CSV files are uploaded to our data folder, process them and email a summary report"

Generated Workflow:
1. Monitor file system for new CSV files
2. Process and validate CSV data
3. Generate summary statistics
4. Create formatted report
5. Email report to stakeholders
```

#### Web Content Monitoring
```
Prompt: "Check our competitor's pricing page daily and alert us if prices change"

Generated Workflow:
1. Scrape competitor pricing page
2. Compare with previous data
3. Detect price changes
4. Send alert with change details
```

## 🏗️ Architecture

### Core Components

#### Workflow Engine
- **Execution Manager**: Handles workflow lifecycle and execution
- **Step Orchestrator**: Manages individual step execution and data flow
- **Condition Evaluator**: Processes conditional logic and branching
- **Error Handler**: Manages failures, retries, and recovery

#### AI Integration
- **Prompt Analyzer**: Understands natural language workflow descriptions
- **Plugin Discovery**: Automatically finds suitable plugins for tasks
- **Template Matcher**: Identifies relevant workflow templates
- **Optimization Engine**: Learns from execution patterns to improve performance

#### Data Management
- **Workflow Storage**: Persistent storage for workflow definitions
- **Execution History**: Comprehensive logging of all workflow runs
- **Configuration Management**: Settings and preferences storage
- **Metrics Collection**: Performance and usage analytics

### Plugin Integration

The extension seamlessly integrates with Kari's existing plugin ecosystem:

- **GitHub Integration**: Repository monitoring, issue management, PR automation
- **Slack Notifications**: Message sending, channel management, user interactions
- **Email Services**: Automated email sending and template management
- **File Processing**: Data transformation, format conversion, content extraction
- **Web Scraping**: Content monitoring, data extraction, change detection
- **Time Operations**: Scheduling, date calculations, timezone handling

## 📊 Monitoring & Analytics

### Real-Time Dashboard
- Live execution status for all workflows
- Success/failure rates and trends
- Performance metrics and bottlenecks
- Resource usage monitoring

### Performance Insights
- Workflow optimization recommendations
- Plugin usage analytics
- Failure pattern analysis
- Cost optimization suggestions

### Alerting System
- Workflow failure notifications
- Performance degradation alerts
- Resource usage warnings
- Weekly performance reports

## 🔧 Configuration

### Extension Settings

```json
{
  "auto_retry_failures": true,
  "parallel_execution": true,
  "smart_scheduling": true,
  "auto_optimization": true,
  "plugin_discovery": true,
  "learning_mode": true
}
```

### Webhook Configuration

The extension supports various webhook triggers:

#### Generic Webhooks
```
POST /api/extensions/prompt-driven-automation/webhook/{workflow_id}
```

#### GitHub Webhooks
```
POST /api/extensions/prompt-driven-automation/webhook/github/{workflow_id}
```

#### Slack Webhooks
```
POST /api/extensions/prompt-driven-automation/webhook/slack/{workflow_id}
```

### Environment Variables

```bash
# GitHub Integration
GITHUB_WEBHOOK_SECRET=your_github_secret

# Slack Integration
SLACK_VERIFICATION_TOKEN=your_slack_token

# General Settings
AUTOMATION_MAX_CONCURRENT_WORKFLOWS=10
AUTOMATION_EXECUTION_TIMEOUT=3600
```

## 🔌 API Reference

### Workflow Management

#### Create Workflow
```http
POST /api/extensions/prompt-driven-automation/workflows
Content-Type: application/json

{
  "prompt": "Monitor GitHub repo and notify Slack when tests fail",
  "name": "CI/CD Monitoring",
  "triggers": [{"type": "schedule", "schedule": "*/5 * * * *"}]
}
```

#### Execute Workflow
```http
POST /api/extensions/prompt-driven-automation/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input_data": {"branch": "main"},
  "dry_run": false
}
```

#### Get Execution History
```http
GET /api/extensions/prompt-driven-automation/execution-history?workflow_id={id}&limit=50
```

### Plugin Discovery

#### Discover Plugins
```http
POST /api/extensions/prompt-driven-automation/discover?task_description=Send notifications to Slack
```

### Analytics

#### Get Metrics
```http
GET /api/extensions/prompt-driven-automation/metrics
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest extensions/automation/prompt-driven/tests/

# Run specific test file
pytest extensions/automation/prompt-driven/tests/test_automation_extension.py

# Run with coverage
pytest --cov=extensions.automation.prompt_driven extensions/automation/prompt-driven/tests/
```

### Test Coverage

The test suite covers:
- Workflow creation from natural language prompts
- Plugin discovery and orchestration
- Workflow execution with success and failure scenarios
- Parameter resolution and condition evaluation
- Template matching and optimization
- API endpoint functionality

## 🚀 Deployment

### Production Considerations

1. **Resource Limits**: Configure appropriate CPU and memory limits
2. **Monitoring**: Set up comprehensive logging and alerting
3. **Security**: Implement proper authentication for webhooks
4. **Backup**: Regular backup of workflow definitions and execution history
5. **Scaling**: Consider horizontal scaling for high-volume environments

### Performance Optimization

- Enable parallel execution for independent steps
- Use workflow templates for common patterns
- Implement caching for frequently accessed data
- Monitor and optimize plugin performance
- Regular cleanup of old execution history

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up development environment
4. Run tests to ensure everything works
5. Start developing new features

### Adding New Features

1. **Plugin Integration**: Add support for new plugins
2. **Workflow Templates**: Create templates for common use cases
3. **UI Enhancements**: Improve the automation studio interface
4. **Analytics**: Add new metrics and insights
5. **Optimization**: Improve performance and reliability

## 📝 License

This extension is part of the Kari AI platform and is subject to the same licensing terms.

## 🆘 Support

For support and questions:
- Check the documentation at https://docs.kari.ai/extensions/prompt-driven-automation
- Open an issue on GitHub
- Join our community Discord
- Contact support at support@kari.ai

---

**The Prompt-Driven Automation Extension - Making automation as easy as describing what you want to achieve.**