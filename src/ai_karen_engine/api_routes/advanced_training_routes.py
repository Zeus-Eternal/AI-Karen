"""
API Routes for Advanced Training Configuration System

Provides REST endpoints for sophisticated hyperparameter optimization, training logic editing,
AI-assisted training strategy suggestions, A/B testing capabilities, and comprehensive
training monitoring with gradient analysis and loss curves.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field
from ai_karen_engine.core.response.advanced_training_config import (
    AdvancedTrainingConfigManager,
    AdvancedTrainingConfig,
    HyperparameterSweepConfig,
    ABTestConfig,
    TrainingLogicConfig,
    OptimizationConfig,
    MonitoringConfig,
    HyperparameterRange,
    OptimizationAlgorithm,
    LossFunction,
    SchedulerType
)
from ai_karen_engine.auth.rbac_middleware import (
    get_current_user, check_training_access, check_admin_access
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.training_audit_logger import get_training_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training/advanced", tags=["advanced-training"])

# Global manager instance
training_manager = AdvancedTrainingConfigManager()

# Initialize audit logger
training_audit_logger = get_training_audit_logger()


async def require_training_user(current_user: UserData = Depends(get_current_user)) -> UserData:
    """Require user with training permissions."""
    if not check_training_access(current_user, "write"):
        training_audit_logger.log_permission_denied(
            user=current_user,
            resource_type="training",
            resource_id="advanced",
            permission_required="training:write"
        )
        raise HTTPException(status_code=403, detail="TRAINING_WRITE permission required")
    return current_user


# Pydantic models for API requests/responses
class HyperparameterRangeModel(BaseModel):
    min_value: float
    max_value: float
    step: Optional[float] = None
    log_scale: bool = False
    discrete_values: Optional[List[Any]] = None


class TrainingLogicConfigModel(BaseModel):
    custom_loss_function: Optional[str] = None
    gradient_accumulation_steps: int = 1
    gradient_clipping: Optional[float] = None
    mixed_precision: bool = False
    checkpoint_frequency: int = 100
    validation_frequency: int = 50
    early_stopping_patience: int = 10
    early_stopping_threshold: float = 1e-4


class OptimizationConfigModel(BaseModel):
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.ADAMW
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    momentum: float = 0.9
    scheduler_type: SchedulerType = SchedulerType.COSINE
    scheduler_params: Dict[str, Any] = Field(default_factory=dict)


class MonitoringConfigModel(BaseModel):
    track_gradients: bool = True
    track_weights: bool = True
    track_activations: bool = False
    gradient_histogram_frequency: int = 10
    weight_histogram_frequency: int = 50
    loss_curve_smoothing: float = 0.1
    metrics_logging_frequency: int = 1
    tensorboard_logging: bool = True
    wandb_logging: bool = False


class HyperparameterSweepConfigModel(BaseModel):
    parameters: Dict[str, HyperparameterRangeModel] = Field(default_factory=dict)
    search_strategy: str = "grid"
    max_trials: int = 50
    max_concurrent_trials: int = 3
    objective_metric: str = "validation_loss"
    objective_direction: str = "minimize"
    early_termination: bool = True
    early_termination_patience: int = 5


class ABTestConfigModel(BaseModel):
    test_name: str
    control_config: Dict[str, Any]
    treatment_configs: List[Dict[str, Any]]
    traffic_split: List[float]
    success_metric: str = "validation_accuracy"
    minimum_sample_size: int = 100
    statistical_significance_threshold: float = 0.05


# RBAC-protected endpoints

@router.get("/configs")
async def list_training_configs(
    current_user: UserData = Depends(get_current_user)
) -> Dict[str, Any]:
    """List advanced training configurations (requires TRAINING_READ permission)."""
    # Check permissions
    if not check_training_access(current_user, "read"):
        training_audit_logger.log_permission_denied(
            user=current_user,
            resource_type="training_config",
            resource_id="list",
            permission_required="training:read"
        )
        raise HTTPException(status_code=403, detail="TRAINING_READ permission required")
    
    try:
        configs = await training_manager.list_configs(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id
        )
        
        return {
            "configs": [config.to_dict() for config in configs],
            "total": len(configs)
        }
        
    except Exception as e:
        logger.error(f"Failed to list training configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configs")
async def create_training_config(
    config_data: Dict[str, Any],
    current_user: UserData = Depends(require_training_user)
) -> Dict[str, Any]:
    """Create advanced training configuration (requires TRAINING_WRITE permission)."""
    try:
        config_id = await training_manager.create_config(
            config_data=config_data,
            created_by=current_user.user_id,
            tenant_id=current_user.tenant_id
        )
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="advanced_training_config",
            config_changes={
                "config_id": config_id,
                "action": "created",
                "config_data": config_data
            }
        )
        
        return {
            "config_id": config_id,
            "message": "Advanced training configuration created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create training config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{config_id}")
async def update_training_config(
    config_id: str,
    config_data: Dict[str, Any],
    current_user: UserData = Depends(require_training_user)
) -> Dict[str, str]:
    """Update advanced training configuration (requires TRAINING_WRITE permission)."""
    try:
        success = await training_manager.update_config(
            config_id=config_id,
            config_data=config_data,
            updated_by=current_user.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="advanced_training_config",
            config_changes={
                "config_id": config_id,
                "action": "updated",
                "config_data": config_data
            }
        )
        
        return {"message": f"Configuration {config_id} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update training config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/configs/{config_id}")
async def delete_training_config(
    config_id: str,
    current_user: UserData = Depends(require_training_user)
) -> Dict[str, str]:
    """Delete advanced training configuration (requires TRAINING_WRITE permission)."""
    try:
        success = await training_manager.delete_config(
            config_id=config_id,
            deleted_by=current_user.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="advanced_training_config",
            config_changes={
                "config_id": config_id,
                "action": "deleted"
            }
        )
        
        return {"message": f"Configuration {config_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete training config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hyperparameter-sweep")
async def start_hyperparameter_sweep(
    sweep_config: HyperparameterSweepConfigModel,
    current_user: UserData = Depends(require_training_user)
) -> Dict[str, Any]:
    """Start hyperparameter sweep (requires TRAINING_EXECUTE permission)."""
    # Check execute permission
    if not check_training_access(current_user, "execute"):
        training_audit_logger.log_permission_denied(
            user=current_user,
            resource_type="training",
            resource_id="hyperparameter_sweep",
            permission_required="training:execute"
        )
        raise HTTPException(status_code=403, detail="TRAINING_EXECUTE permission required")
    
    try:
        sweep_id = await training_manager.start_hyperparameter_sweep(
            sweep_config=sweep_config.dict(),
            started_by=current_user.user_id
        )
        
        # Audit log
        training_audit_logger.log_training_started(
            user=current_user,
            training_job_id=sweep_id,
            training_config={
                "type": "hyperparameter_sweep",
                "parameters": sweep_config.parameters,
                "max_trials": sweep_config.max_trials
            }
        )
        
        return {
            "sweep_id": sweep_id,
            "message": "Hyperparameter sweep started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start hyperparameter sweep: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    test_duration_hours: int = 24


class AdvancedTrainingConfigModel(BaseModel):
    model_id: str
    dataset_id: str
    training_logic: TrainingLogicConfigModel = Field(default_factory=TrainingLogicConfigModel)
    optimization: OptimizationConfigModel = Field(default_factory=OptimizationConfigModel)
    hyperparameter_sweep: Optional[HyperparameterSweepConfigModel] = None
    ab_test: Optional[ABTestConfigModel] = None
    monitoring: MonitoringConfigModel = Field(default_factory=MonitoringConfigModel)
    max_epochs: int = 100
    batch_size: int = 32
    validation_split: float = 0.2
    random_seed: int = 42
    device: str = "auto"
    distributed_training: bool = False
    num_workers: int = 4


class AIAssistanceRequest(BaseModel):
    model_type: str
    dataset_size: int
    hardware_specs: Dict[str, Any]


class TrainingMetricsUpdate(BaseModel):
    epoch: int
    metrics: Dict[str, Any]


class ABTestResultRequest(BaseModel):
    user_id: str
    treatment: str
    metric_value: float
    additional_metrics: Optional[Dict[str, Any]] = None


@router.post("/config", response_model=Dict[str, str])
async def create_advanced_config(config_data: AdvancedTrainingConfigModel):
    """Create and save an advanced training configuration."""
    try:
        # Convert Pydantic model to dict and create config
        config_dict = config_data.dict()
        config = training_manager.create_advanced_config(config_dict)
        
        # Save configuration
        config_id = training_manager.save_config(config)
        
        return {
            "config_id": config_id,
            "status": "created",
            "message": f"Advanced training configuration created with ID: {config_id}"
        }
    
    except Exception as e:
        logger.error(f"Error creating advanced config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")


@router.get("/config/{config_id}")
async def get_advanced_config(config_id: str):
    """Retrieve an advanced training configuration."""
    try:
        config = training_manager.load_config(config_id)
        return config
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
    except Exception as e:
        logger.error(f"Error loading config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load configuration: {str(e)}")


@router.post("/ai-suggestions")
async def get_ai_suggestions(request: AIAssistanceRequest):
    """Get AI-assisted training strategy suggestions."""
    try:
        suggestions = training_manager.get_ai_suggestions(
            request.model_type,
            request.dataset_size,
            request.hardware_specs
        )
        
        return {
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat(),
            "model_type": request.model_type,
            "dataset_size": request.dataset_size
        }
    
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.post("/hyperparameter-sweep/start")
async def start_hyperparameter_sweep(config_data: AdvancedTrainingConfigModel):
    """Start a hyperparameter sweep."""
    try:
        if not config_data.hyperparameter_sweep:
            raise HTTPException(status_code=400, detail="No hyperparameter sweep configuration provided")
        
        # Convert to internal config format
        config_dict = config_data.dict()
        config = training_manager.create_advanced_config(config_dict)
        
        # Start sweep
        sweep_id = training_manager.start_hyperparameter_sweep(config)
        
        return {
            "sweep_id": sweep_id,
            "status": "started",
            "search_strategy": config_data.hyperparameter_sweep.search_strategy,
            "max_trials": config_data.hyperparameter_sweep.max_trials,
            "message": f"Hyperparameter sweep started with ID: {sweep_id}"
        }
    
    except Exception as e:
        logger.error(f"Error starting hyperparameter sweep: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sweep: {str(e)}")


@router.get("/hyperparameter-sweep/{sweep_id}/suggestion/{trial_number}")
async def get_sweep_suggestion(sweep_id: str, trial_number: int):
    """Get parameter suggestion for next trial in hyperparameter sweep."""
    try:
        suggestion = training_manager.get_sweep_suggestion(sweep_id, trial_number)
        
        return {
            "sweep_id": sweep_id,
            "trial_number": trial_number,
            "parameters": suggestion,
            "suggested_at": datetime.now().isoformat()
        }
    
    except StopIteration:
        raise HTTPException(status_code=404, detail="All parameter combinations have been tried")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting sweep suggestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")


@router.post("/hyperparameter-sweep/{sweep_id}/result")
async def report_sweep_result(
    sweep_id: str,
    trial_number: int,
    parameters: Dict[str, Any],
    objective_value: float,
    metrics: Dict[str, Any]
):
    """Report result for a hyperparameter sweep trial."""
    try:
        training_manager.report_sweep_result(sweep_id, trial_number, parameters, objective_value, metrics)
        
        return {
            "sweep_id": sweep_id,
            "trial_number": trial_number,
            "status": "recorded",
            "objective_value": objective_value,
            "message": "Trial result recorded successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reporting sweep result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record result: {str(e)}")


@router.get("/hyperparameter-sweep/{sweep_id}/best")
async def get_sweep_best_params(sweep_id: str):
    """Get best parameters from hyperparameter sweep."""
    try:
        best_params, best_score = training_manager.get_sweep_best_params(sweep_id)
        
        return {
            "sweep_id": sweep_id,
            "best_parameters": best_params,
            "best_score": best_score,
            "retrieved_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting best parameters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get best parameters: {str(e)}")


@router.post("/ab-test/create")
async def create_ab_test(config: ABTestConfigModel):
    """Create an A/B test for training strategies."""
    try:
        # Convert to internal config format
        ab_config = ABTestConfig(**config.dict())
        
        test_id = training_manager.create_ab_test(ab_config)
        
        return {
            "test_id": test_id,
            "status": "created",
            "test_name": config.test_name,
            "treatments": len(config.treatment_configs),
            "message": f"A/B test created with ID: {test_id}"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create A/B test: {str(e)}")


@router.get("/ab-test/{test_id}/assignment/{user_id}")
async def get_ab_test_assignment(test_id: str, user_id: str):
    """Get A/B test treatment assignment for a user."""
    try:
        treatment, config = training_manager.get_ab_test_assignment(test_id, user_id)
        
        return {
            "test_id": test_id,
            "user_id": user_id,
            "treatment": treatment,
            "config": config,
            "assigned_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting A/B test assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assignment: {str(e)}")


@router.post("/ab-test/{test_id}/result")
async def record_ab_test_result(test_id: str, result: ABTestResultRequest):
    """Record a result for an A/B test."""
    try:
        training_manager.record_ab_test_result(
            test_id,
            result.user_id,
            result.treatment,
            result.metric_value,
            result.additional_metrics
        )
        
        return {
            "test_id": test_id,
            "user_id": result.user_id,
            "status": "recorded",
            "metric_value": result.metric_value,
            "message": "A/B test result recorded successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording A/B test result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record result: {str(e)}")


@router.get("/ab-test/{test_id}/analysis")
async def analyze_ab_test(test_id: str):
    """Analyze A/B test results for statistical significance."""
    try:
        analysis = training_manager.analyze_ab_test(test_id)
        
        return {
            "test_id": test_id,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze test: {str(e)}")


@router.post("/training/{training_id}/metrics/initialize")
async def initialize_training_metrics(training_id: str):
    """Initialize metrics tracking for a training session."""
    try:
        metrics = training_manager.initialize_training_metrics(training_id)
        
        return {
            "training_id": training_id,
            "status": "initialized",
            "message": "Training metrics tracking initialized"
        }
    
    except Exception as e:
        logger.error(f"Error initializing training metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize metrics: {str(e)}")


@router.post("/training/{training_id}/metrics/update")
async def update_training_metrics(training_id: str, update: TrainingMetricsUpdate):
    """Update training metrics for an epoch."""
    try:
        training_manager.update_training_metrics(training_id, update.epoch, update.metrics)
        
        return {
            "training_id": training_id,
            "epoch": update.epoch,
            "status": "updated",
            "message": f"Metrics updated for epoch {update.epoch}"
        }
    
    except Exception as e:
        logger.error(f"Error updating training metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update metrics: {str(e)}")


@router.get("/training/{training_id}/analysis")
async def get_training_analysis(training_id: str):
    """Get AI analysis of training progress."""
    try:
        analysis = training_manager.get_training_analysis(training_id)
        
        return {
            "training_id": training_id,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting training analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze training: {str(e)}")


@router.get("/training/{training_id}/loss-curves")
async def get_loss_curves(training_id: str):
    """Get loss curve data for visualization."""
    try:
        loss_data = training_manager.get_loss_curve_data(training_id)
        
        return {
            "training_id": training_id,
            "loss_curves": loss_data,
            "retrieved_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting loss curves: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get loss curves: {str(e)}")


@router.get("/training/{training_id}/gradient-analysis")
async def get_gradient_analysis(training_id: str):
    """Get gradient analysis for training session."""
    try:
        gradient_analysis = training_manager.get_gradient_analysis(training_id)
        
        return {
            "training_id": training_id,
            "gradient_analysis": gradient_analysis,
            "analyzed_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting gradient analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get gradient analysis: {str(e)}")


@router.get("/training/{training_id}/report")
async def export_training_report(training_id: str):
    """Export comprehensive training report."""
    try:
        report = training_manager.export_training_report(training_id)
        
        return report
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting training report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


@router.post("/cleanup")
async def cleanup_completed_sweeps(background_tasks: BackgroundTasks, max_age_hours: int = 24):
    """Clean up completed hyperparameter sweeps."""
    try:
        background_tasks.add_task(training_manager.cleanup_completed_sweeps, max_age_hours)
        
        return {
            "status": "scheduled",
            "max_age_hours": max_age_hours,
            "message": "Cleanup task scheduled in background"
        }
    
    except Exception as e:
        logger.error(f"Error scheduling cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule cleanup: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for advanced training system."""
    try:
        return {
            "status": "healthy",
            "service": "advanced-training-config",
            "timestamp": datetime.now().isoformat(),
            "active_sweeps": len(training_manager.active_sweeps),
            "active_metrics": len(training_manager.training_metrics)
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")