import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Play, 
  Square, 
  RefreshCw, 
  Save, 
  RotateCcw, 
  Clock, 
  Cpu, 
  HardDrive,
  AlertTriangle,
  CheckCircle,
  Info,
  Trash2
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
interface BasicTrainingPreset {
  name: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  training_type: string;
  num_epochs: number;
  learning_rate: number;
  batch_size: number;
  max_length: number;
  warmup_ratio: number;
  use_mixed_precision: boolean;
  gradient_checkpointing: boolean;
  recommended_for: string[];
  estimated_time: string;
  memory_requirements_gb: number;
}
interface TrainingProgress {
  job_id: string;
  model_name: string;
  status: string;
  progress_percentage: number;
  current_step: number;
  total_steps: number;
  current_epoch: number;
  total_epochs: number;
  elapsed_time: string;
  estimated_remaining: string;
  current_loss?: number;
  best_loss?: number;
  learning_rate?: number;
  memory_usage_gb?: number;
  gpu_utilization?: number;
  status_message: string;
  warnings: string[];
  recommendations: string[];
}
interface TrainingResult {
  job_id: string;
  model_name: string;
  success: boolean;
  training_time: string;
  final_loss?: number;
  improvement_percentage?: number;
  model_path?: string;
  performance_summary: string;
  recommendations: string[];
  warnings: string[];
  next_steps: string[];
}
interface SystemBackup {
  backup_id: string;
  created_at: string;
  description: string;
  backup_path: string;
  size_mb: number;
}
const BasicTrainingMode: React.FC = () => {
  const [presets, setPresets] = useState<BasicTrainingPreset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<BasicTrainingPreset | null>(null);
  const [modelId, setModelId] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const [customDescription, setCustomDescription] = useState('');
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [progress, setProgress] = useState<TrainingProgress | null>(null);
  const [result, setResult] = useState<TrainingResult | null>(null);
  const [backups, setBackups] = useState<SystemBackup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('training');
  useEffect(() => {
    loadPresets();
    loadBackups();
  }, []);
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentJob && progress?.status === 'Training in progress') {
      interval = setInterval(() => {
        loadProgress(currentJob);
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentJob, progress?.status]);
  const loadPresets = async () => {
    try {
      const response = await getKarenBackend().makeRequestPublic('/api/basic-training/presets');
      setPresets(response as BasicTrainingPreset[]);
    } catch (err) {
      setError('Failed to load training presets');
    }
  };
  const loadProgress = async (jobId: string) => {
    try {
      const response = await getKarenBackend().makeRequestPublic(`/api/basic-training/progress/${jobId}`);
      const progressData = response as any;
      setProgress(progressData);
      if (progressData.status === 'Training completed!' || progressData.status === 'Training encountered an issue') {
        loadResult(jobId);
      }
    } catch (err) {
    }
  };
  const loadResult = async (jobId: string) => {
    try {
      const response = await getKarenBackend().makeRequestPublic(`/api/basic-training/result/${jobId}`);
      setResult(response as any);
    } catch (err) {
    }
  };
  const loadBackups = async () => {
    try {
      const response = await getKarenBackend().makeRequestPublic('/api/basic-training/backups');
      setBackups(response as any[]);
    } catch (err) {
    }
  };
  const startTraining = async () => {
    if (!modelId || !datasetId || !selectedPreset) {
      setError('Please fill in all required fields and select a preset');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await getKarenBackend().makeRequestPublic('/api/basic-training/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelId,
          dataset_id: datasetId,
          preset_name: selectedPreset.name,
          custom_description: customDescription
        })
      });
      const jobData = response as any;
      setCurrentJob(jobData.job_id);
      setProgress(null);
      setResult(null);
      // Start monitoring progress
      setTimeout(() => loadProgress(jobData.job_id), 1000);
    } catch (err: any) {
      setError(err.message || 'Failed to start training');
    } finally {
      setLoading(false);
    }
  };
  const cancelTraining = async () => {
    if (!currentJob) return;
    try {
      await getKarenBackend().makeRequestPublic(`/api/basic-training/cancel/${currentJob}`, {
        method: 'POST'
      });
      setCurrentJob(null);
      setProgress(null);
    } catch (err: any) {
      setError(err.message || 'Failed to cancel training');
    }
  };
  const createBackup = async () => {
    const description = prompt('Enter backup description:') || 'Manual backup';
    try {
      await getKarenBackend().makeRequestPublic('/api/basic-training/backup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      });
      loadBackups();
    } catch (err: any) {
      setError(err.message || 'Failed to create backup');
    }
  };
  const restoreBackup = async (backupId: string) => {
    if (!confirm('Are you sure you want to restore this backup? This will overwrite current settings.')) {
      return;
    }
    try {
      await getKarenBackend().makeRequestPublic('/api/basic-training/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_id: backupId })
      });
      alert('System restored successfully');
    } catch (err: any) {
      setError(err.message || 'Failed to restore backup');
    }
  };
  const resetToDefaults = async () => {
    if (!confirm('Are you sure you want to reset to factory defaults? This action cannot be undone.')) {
      return;
    }
    const preserveUserData = confirm('Do you want to preserve user data?');
    try {
      await getKarenBackend().makeRequestPublic('/api/basic-training/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preserve_user_data: preserveUserData })
      });
      alert('System reset to factory defaults');
    } catch (err: any) {
      setError(err.message || 'Failed to reset system');
    }
  };
  const deleteBackup = async (backupId: string) => {
    if (!confirm('Are you sure you want to delete this backup?')) {
      return;
    }
    try {
      await getKarenBackend().makeRequestPublic(`/api/basic-training/backup/${backupId}`, {
        method: 'DELETE'
      });
      loadBackups();
    } catch (err: any) {
      setError(err.message || 'Failed to delete backup');
    }
  };
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  const formatFileSize = (mb: number) => {
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  };
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Basic Training Mode</h2>
        <p className="text-gray-600">
          Simplified training interface with preset configurations and user-friendly monitoring
        </p>
      </div>
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="training">Training</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
          <TabsTrigger value="system">System Reset</TabsTrigger>
        </TabsList>
        <TabsContent value="training" className="space-y-6">
          {/* Training Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Training Configuration</CardTitle>
              <CardDescription>
                Configure your training job with automatic parameter selection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Model ID</label>
                  <input
                    type="text"
                    value={modelId}
                    onChange={(e) = aria-label="Input"> setModelId(e.target.value)}
                    placeholder="e.g., microsoft/DialoGPT-medium"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Dataset ID</label>
                  <input
                    type="text"
                    value={datasetId}
                    onChange={(e) = aria-label="Input"> setDatasetId(e.target.value)}
                    placeholder="e.g., my-training-dataset"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Custom Description (Optional)</label>
                <input
                  type="text"
                  value={customDescription}
                  onChange={(e) = aria-label="Input"> setCustomDescription(e.target.value)}
                  placeholder="Describe your training goal..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </CardContent>
          </Card>
          {/* Training Presets */}
          <Card>
            <CardHeader>
              <CardTitle>Training Presets</CardTitle>
              <CardDescription>
                Choose a preset optimized for your hardware and use case
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {presets.map((preset) => (
                  <div
                    key={preset.name}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedPreset?.name === preset.name
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedPreset(preset)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">{preset.name}</h3>
                      <Badge className={getDifficultyColor(preset.difficulty)}>
                        {preset.difficulty}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-3 md:text-base lg:text-lg">{preset.description}</p>
                    <div className="space-y-2 text-xs sm:text-sm md:text-base">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3 sm:w-auto md:w-full" />
                        <span>{preset.estimated_time}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="h-3 w-3 sm:w-auto md:w-full" />
                        <span>{preset.memory_requirements_gb}GB RAM</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Cpu className="h-3 w-3 sm:w-auto md:w-full" />
                        <span>{preset.num_epochs} epochs, {preset.training_type}</span>
                      </div>
                    </div>
                    {preset.recommended_for.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-700 mb-1 sm:text-sm md:text-base">Recommended for:</p>
                        <div className="flex flex-wrap gap-1">
                          {preset.recommended_for.slice(0, 3).map((use) => (
                            <Badge key={use} variant="outline" className="text-xs sm:text-sm md:text-base">
                              {use}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <button
                  onClick={startTraining}
                  disabled={loading || !modelId || !datasetId || !selectedPreset || !!currentJob}
                  className="w-full"
                 aria-label="Button">
                  {loading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin sm:w-auto md:w-full" />
                      Starting Training...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                      Start Training
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="progress" className="space-y-6">
          {/* Training Progress */}
          {progress && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Training Progress: {progress.model_name}
                  {progress.status === 'Training completed!' && (
                    <CheckCircle className="h-5 w-5 text-green-600 sm:w-auto md:w-full" />
                  )}
                </CardTitle>
                <CardDescription>{progress.status_message}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2 md:text-base lg:text-lg">
                    <span>Progress</span>
                    <span>{progress.progress_percentage.toFixed(1)}%</span>
                  </div>
                  <Progress value={progress.progress_percentage} className="w-full" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="font-medium">Epoch</p>
                    <p>{progress.current_epoch + 1} / {progress.total_epochs}</p>
                  </div>
                  <div>
                    <p className="font-medium">Step</p>
                    <p>{progress.current_step} / {progress.total_steps}</p>
                  </div>
                  <div>
                    <p className="font-medium">Elapsed</p>
                    <p>{progress.elapsed_time}</p>
                  </div>
                  <div>
                    <p className="font-medium">Remaining</p>
                    <p>{progress.estimated_remaining}</p>
                  </div>
                </div>
                {(progress.current_loss || progress.learning_rate) && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    {progress.current_loss && (
                      <div>
                        <p className="font-medium">Current Loss</p>
                        <p>{progress.current_loss.toFixed(4)}</p>
                      </div>
                    )}
                    {progress.best_loss && (
                      <div>
                        <p className="font-medium">Best Loss</p>
                        <p>{progress.best_loss.toFixed(4)}</p>
                      </div>
                    )}
                    {progress.learning_rate && (
                      <div>
                        <p className="font-medium">Learning Rate</p>
                        <p>{progress.learning_rate.toExponential(2)}</p>
                      </div>
                    )}
                    {progress.memory_usage_gb && (
                      <div>
                        <p className="font-medium">Memory Usage</p>
                        <p>{progress.memory_usage_gb.toFixed(1)}GB</p>
                      </div>
                    )}
                  </div>
                )}
                {progress.warnings.length > 0 && (
                  <Alert className="border-yellow-200 bg-yellow-50">
                    <AlertTriangle className="h-4 w-4 text-yellow-600 sm:w-auto md:w-full" />
                    <AlertDescription>
                      <div className="space-y-1">
                        {progress.warnings.map((warning, index) => (
                          <p key={index} className="text-yellow-800">{warning}</p>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
                {progress.recommendations.length > 0 && (
                  <Alert className="border-blue-200 bg-blue-50">
                    <Info className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />
                    <AlertDescription>
                      <div className="space-y-1">
                        {progress.recommendations.map((rec, index) => (
                          <p key={index} className="text-blue-800">{rec}</p>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
                {currentJob && progress.status === 'Training in progress' && (
                  <button onClick={cancelTraining} variant="destructive" className="w-full" aria-label="Button">
                    <Square className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                    Cancel Training
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
          {/* Training Results */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Training Results: {result.model_name}
                  {result.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600 sm:w-auto md:w-full" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-red-600 sm:w-auto md:w-full" />
                  )}
                </CardTitle>
                <CardDescription>Training completed in {result.training_time}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                  <h4 className="font-medium mb-2">Performance Summary</h4>
                  <p>{result.performance_summary}</p>
                </div>
                {result.improvement_percentage !== null && (
                  <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                    {result.improvement_percentage !== undefined && (
                      <div>
                        <p className="font-medium">Improvement</p>
                        <p className={result.improvement_percentage > 0 ? 'text-green-600' : 'text-red-600'}>
                          {result.improvement_percentage > 0 ? '+' : ''}{result.improvement_percentage.toFixed(1)}%
                        </p>
                      </div>
                    )}
                    {result.final_loss && (
                      <div>
                        <p className="font-medium">Final Loss</p>
                        <p>{result.final_loss.toFixed(4)}</p>
                      </div>
                    )}
                  </div>
                )}
                {result.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Recommendations</h4>
                    <ul className="space-y-1 text-sm md:text-base lg:text-lg">
                      {result.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-blue-600">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.next_steps.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Next Steps</h4>
                    <ul className="space-y-1 text-sm md:text-base lg:text-lg">
                      {result.next_steps.map((step, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-green-600">•</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.model_path && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg sm:p-4 md:p-6">
                    <p className="text-sm font-medium text-green-800 md:text-base lg:text-lg">Model saved to:</p>
                    <p className="text-sm text-green-700 font-mono md:text-base lg:text-lg">{result.model_path}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
        <TabsContent value="system" className="space-y-6">
          {/* System Backup and Reset */}
          <Card>
            <CardHeader>
              <CardTitle>System Backup & Reset</CardTitle>
              <CardDescription>
                Create backups and restore system configurations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <button onClick={createBackup} className="flex-1" aria-label="Button">
                  <Save className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                  Create Backup
                </Button>
                <button onClick={resetToDefaults} variant="destructive" className="flex-1" aria-label="Button">
                  <RotateCcw className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                  Reset to Defaults
                </Button>
              </div>
            </CardContent>
          </Card>
          {/* Backup List */}
          <Card>
            <CardHeader>
              <CardTitle>Available Backups</CardTitle>
              <CardDescription>
                Manage your system configuration backups
              </CardDescription>
            </CardHeader>
            <CardContent>
              {backups.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No backups available</p>
              ) : (
                <div className="space-y-3">
                  {backups.map((backup) => (
                    <div key={backup.backup_id} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
                      <div>
                        <p className="font-medium">{backup.description}</p>
                        <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                          {new Date(backup.created_at).toLocaleString()} • {formatFileSize(backup.size_mb)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          size="sm"
                          onClick={() = aria-label="Button"> restoreBackup(backup.backup_id)}
                        >
                          Restore
                        </Button>
                        <button
                          size="sm"
                          variant="destructive"
                          onClick={() = aria-label="Button"> deleteBackup(backup.backup_id)}
                        >
                          <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
export default BasicTrainingMode;
