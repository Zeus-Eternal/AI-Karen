"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Copy,
  CheckCircle2,
  AlertCircle,
  Info,
  Key,
  Download,
  Settings,
  Terminal,
  FileText,
  Globe,
  Shield
} from 'lucide-react';
import { useToast } from "@/hooks/use-toast";

interface ConfigurationStep {
  id: string;
  title: string;
  description: string;
  type: 'api_key' | 'installation' | 'configuration' | 'verification';
  required: boolean;
  completed?: boolean;
  instructions: string[];
  code_snippets?: { language: string; code: string; description?: string }[];
  links?: { title: string; url: string; description?: string }[];
  troubleshooting?: string[];
}

interface ProviderGuide {
  provider_name: string;
  provider_type: 'remote' | 'local' | 'hybrid';
  description: string;
  prerequisites: string[];
  steps: ConfigurationStep[];
  common_issues: { issue: string; solution: string }[];
  additional_resources: { title: string; url: string; type: 'documentation' | 'tutorial' | 'community' }[];
}

interface ProviderConfigurationGuideProps {
  providerName: string;
  onStepComplete?: (stepId: string) => void;
  onConfigurationComplete?: () => void;
}

const PROVIDER_GUIDES: Record<string, ProviderGuide> = {
  openai: {
    provider_name: 'OpenAI',
    provider_type: 'remote',
    description: 'Configure OpenAI API access for GPT models',
    prerequisites: [
      'OpenAI account with API access',
      'Valid payment method (for paid usage)',
      'Internet connection'
    ],
    steps: [
      {
        id: 'create_account',
        title: 'Create OpenAI Account',
        description: 'Sign up for an OpenAI account and verify your email',
        type: 'api_key',
        required: true,
        instructions: [
          'Go to https://platform.openai.com',
          'Click "Sign up" and create your account',
          'Verify your email address',
          'Complete any required verification steps'
        ],
        links: [
          { title: 'OpenAI Platform', url: 'https://platform.openai.com', description: 'Main platform page' }
        ]
      },
      {
        id: 'get_api_key',
        title: 'Generate API Key',
        description: 'Create an API key for authentication',
        type: 'api_key',
        required: true,
        instructions: [
          'Log in to your OpenAI account',
          'Navigate to API Keys section',
          'Click "Create new secret key"',
          'Copy the key immediately (it won\'t be shown again)',
          'Store the key securely'
        ],
        links: [
          { title: 'API Keys Management', url: 'https://platform.openai.com/api-keys', description: 'Manage your API keys' }
        ],
        troubleshooting: [
          'If you can\'t see API Keys section, ensure your account is verified',
          'API keys are only shown once - copy immediately',
          'Keep your API key secure and never share it publicly'
        ]
      },
      {
        id: 'configure_key',
        title: 'Configure API Key',
        description: 'Add your API key to the system',
        type: 'configuration',
        required: true,
        instructions: [
          'Paste your API key in the provider settings',
          'The system will automatically validate the key',
          'Wait for the green checkmark indicating successful validation'
        ]
      },
      {
        id: 'test_connection',
        title: 'Test Connection',
        description: 'Verify the provider is working correctly',
        type: 'verification',
        required: true,
        instructions: [
          'Click the "Test" button in provider settings',
          'Wait for the connection test to complete',
          'Verify that models are discovered successfully'
        ]
      }
    ],
    common_issues: [
      {
        issue: 'API key validation fails',
        solution: 'Ensure the API key is copied correctly without extra spaces. Check that your OpenAI account has API access enabled.'
      },
      {
        issue: 'Rate limit errors',
        solution: 'You may have exceeded your rate limits. Check your OpenAI dashboard for usage limits and consider upgrading your plan.'
      },
      {
        issue: 'Insufficient quota',
        solution: 'Add a payment method to your OpenAI account or check your usage limits in the billing section.'
      }
    ],
    additional_resources: [
      { title: 'OpenAI API Documentation', url: 'https://platform.openai.com/docs', type: 'documentation' },
      { title: 'Rate Limits Guide', url: 'https://platform.openai.com/docs/guides/rate-limits', type: 'documentation' },
      { title: 'OpenAI Community', url: 'https://community.openai.com', type: 'community' }
    ]
  },
  gemini: {
    provider_name: 'Google Gemini',
    provider_type: 'remote',
    description: 'Configure Google Gemini API access',
    prerequisites: [
      'Google account',
      'Google Cloud Console access',
      'Internet connection'
    ],
    steps: [
      {
        id: 'enable_api',
        title: 'Enable Gemini API',
        description: 'Enable the Gemini API in Google Cloud Console',
        type: 'api_key',
        required: true,
        instructions: [
          'Go to Google AI Studio',
          'Sign in with your Google account',
          'Accept the terms of service',
          'Enable the Gemini API'
        ],
        links: [
          { title: 'Google AI Studio', url: 'https://aistudio.google.com', description: 'Main AI Studio page' }
        ]
      },
      {
        id: 'create_api_key',
        title: 'Create API Key',
        description: 'Generate an API key for Gemini access',
        type: 'api_key',
        required: true,
        instructions: [
          'In Google AI Studio, go to API Keys',
          'Click "Create API Key"',
          'Copy the generated key',
          'Store the key securely'
        ]
      },
      {
        id: 'configure_key',
        title: 'Configure API Key',
        description: 'Add your API key to the system',
        type: 'configuration',
        required: true,
        instructions: [
          'Paste your API key in the Gemini provider settings',
          'The system will validate the key automatically',
          'Wait for successful validation'
        ]
      }
    ],
    common_issues: [
      {
        issue: 'API not enabled',
        solution: 'Ensure you have enabled the Gemini API in Google AI Studio and accepted all terms of service.'
      },
      {
        issue: 'Quota exceeded',
        solution: 'Check your API usage in Google AI Studio. You may need to request higher quotas or wait for the quota to reset.'
      }
    ],
    additional_resources: [
      { title: 'Gemini API Documentation', url: 'https://ai.google.dev/docs', type: 'documentation' },
      { title: 'Google AI Studio', url: 'https://aistudio.google.com', type: 'documentation' }
    ]
  },
  local: {
    provider_name: 'Local Models',
    provider_type: 'local',
    description: 'Configure local model execution with llama.cpp or transformers',
    prerequisites: [
      'Sufficient disk space (2GB+ per model)',
      'Adequate RAM (8GB+ recommended)',
      'Python environment'
    ],
    steps: [
      {
        id: 'install_dependencies',
        title: 'Install Dependencies',
        description: 'Install required packages for local model execution',
        type: 'installation',
        required: true,
        instructions: [
          'Ensure Python 3.8+ is installed',
          'Install required packages using pip',
          'Verify installation was successful'
        ],
        code_snippets: [
          {
            language: 'bash',
            code: 'pip install llama-cpp-python transformers torch',
            description: 'Install core dependencies'
          },
          {
            language: 'bash',
            code: 'python -c "import llama_cpp; print(\'llama-cpp-python installed successfully\')"',
            description: 'Verify installation'
          }
        ]
      },
      {
        id: 'download_models',
        title: 'Download Models',
        description: 'Download compatible model files',
        type: 'configuration',
        required: true,
        instructions: [
          'Choose models compatible with your hardware',
          'Download GGUF files for llama.cpp',
          'Place models in the models directory',
          'Verify model files are accessible'
        ],
        links: [
          { title: 'Hugging Face Models', url: 'https://huggingface.co/models', description: 'Browse available models' }
        ]
      },
      {
        id: 'configure_paths',
        title: 'Configure Model Paths',
        description: 'Set up model file paths and configurations',
        type: 'configuration',
        required: true,
        instructions: [
          'Update model registry with your model paths',
          'Configure model parameters (context length, etc.)',
          'Test model loading'
        ]
      }
    ],
    common_issues: [
      {
        issue: 'Model loading fails',
        solution: 'Check that model files are in the correct format (GGUF for llama.cpp) and paths are configured correctly.'
      },
      {
        issue: 'Out of memory errors',
        solution: 'Try smaller models or reduce context length. Ensure you have sufficient RAM for the model size.'
      },
      {
        issue: 'Slow inference',
        solution: 'Consider using quantized models, enabling GPU acceleration, or reducing model size.'
      }
    ],
    additional_resources: [
      { title: 'llama.cpp Documentation', url: 'https://github.com/ggerganov/llama.cpp', type: 'documentation' },
      { title: 'Transformers Documentation', url: 'https://huggingface.co/docs/transformers', type: 'documentation' }
    ]
  }
};

export function ProviderConfigurationGuide({
  providerName,
  onStepComplete,
  onConfigurationComplete
}: ProviderConfigurationGuideProps) {
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const guide = PROVIDER_GUIDES[providerName.toLowerCase()];

  if (!guide) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Configuration Guide Not Available</AlertTitle>
        <AlertDescription>
          No configuration guide is available for {providerName}. Please refer to the provider's documentation.
        </AlertDescription>
      </Alert>
    );
  }

  const handleStepComplete = (stepId: string) => {
    const newCompleted = new Set(completedSteps);
    newCompleted.add(stepId);
    setCompletedSteps(newCompleted);
    onStepComplete?.(stepId);

    // Check if all required steps are completed
    const requiredSteps = guide.steps.filter(step => step.required);
    const allRequiredCompleted = requiredSteps.every(step => newCompleted.has(step.id));
    
    if (allRequiredCompleted) {
      onConfigurationComplete?.();
      toast({
        title: "Configuration Complete",
        description: `${guide.provider_name} has been successfully configured!`,
      });
    }
  };

  const toggleStepExpansion = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to Clipboard",
      description: "Code snippet copied successfully.",
    });
  };

  const getStepIcon = (step: ConfigurationStep) => {
    switch (step.type) {
      case 'api_key':
        return <Key className="h-4 w-4" />;
      case 'installation':
        return <Download className="h-4 w-4" />;
      case 'configuration':
        return <Settings className="h-4 w-4" />;
      case 'verification':
        return <CheckCircle2 className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const progress = (completedSteps.size / guide.steps.filter(s => s.required).length) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {guide.provider_name} Configuration Guide
          </CardTitle>
          <CardDescription>{guide.description}</CardDescription>
          
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Configuration Progress</span>
              <span>{Math.round(progress)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="setup" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Setup Steps</TabsTrigger>
          <TabsTrigger value="troubleshooting">Troubleshooting</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-4">
          {/* Prerequisites */}
          {guide.prerequisites.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Prerequisites</CardTitle>
                <CardDescription>
                  Ensure you have the following before starting:
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {guide.prerequisites.map((prereq, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <span className="text-sm">{prereq}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Configuration Steps */}
          <div className="space-y-4">
            {guide.steps.map((step, index) => (
              <Card key={step.id} className="transition-all hover:shadow-md">
                <Collapsible
                  open={expandedSteps.has(step.id)}
                  onOpenChange={() => toggleStepExpansion(step.id)}
                >
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-muted/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                              {index + 1}
                            </span>
                            {getStepIcon(step)}
                          </div>
                          <div>
                            <CardTitle className="text-base">{step.title}</CardTitle>
                            <CardDescription>{step.description}</CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {step.required && (
                            <Badge variant="outline" className="text-xs">Required</Badge>
                          )}
                          {completedSteps.has(step.id) ? (
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-gray-400" />
                          )}
                          {expandedSteps.has(step.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <CardContent className="pt-0 space-y-4">
                      {/* Instructions */}
                      <div className="space-y-2">
                        <h4 className="font-medium">Instructions:</h4>
                        <ol className="list-decimal list-inside space-y-1 text-sm">
                          {step.instructions.map((instruction, idx) => (
                            <li key={idx}>{instruction}</li>
                          ))}
                        </ol>
                      </div>

                      {/* Code Snippets */}
                      {step.code_snippets && step.code_snippets.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Code Examples:</h4>
                          {step.code_snippets.map((snippet, idx) => (
                            <div key={idx} className="space-y-2">
                              {snippet.description && (
                                <p className="text-sm text-muted-foreground">{snippet.description}</p>
                              )}
                              <div className="relative">
                                <pre className="bg-muted p-3 rounded-lg text-sm overflow-x-auto">
                                  <code>{snippet.code}</code>
                                </pre>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="absolute top-2 right-2"
                                  onClick={() => copyToClipboard(snippet.code)}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Links */}
                      {step.links && step.links.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Helpful Links:</h4>
                          <div className="space-y-1">
                            {step.links.map((link, idx) => (
                              <div key={idx} className="flex items-center gap-2">
                                <Button
                                  variant="link"
                                  size="sm"
                                  className="p-0 h-auto"
                                  onClick={() => window.open(link.url, '_blank')}
                                >
                                  <ExternalLink className="h-3 w-3 mr-1" />
                                  {link.title}
                                </Button>
                                {link.description && (
                                  <span className="text-xs text-muted-foreground">
                                    - {link.description}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Troubleshooting */}
                      {step.troubleshooting && step.troubleshooting.length > 0 && (
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>Common Issues</AlertTitle>
                          <AlertDescription>
                            <ul className="list-disc list-inside space-y-1 mt-2">
                              {step.troubleshooting.map((tip, idx) => (
                                <li key={idx} className="text-sm">{tip}</li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}

                      {/* Mark as Complete Button */}
                      <Button
                        onClick={() => handleStepComplete(step.id)}
                        disabled={completedSteps.has(step.id)}
                        variant={completedSteps.has(step.id) ? "outline" : "default"}
                        className="w-full"
                      >
                        {completedSteps.has(step.id) ? (
                          <>
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Step Completed
                          </>
                        ) : (
                          'Mark as Complete'
                        )}
                      </Button>
                    </CardContent>
                  </CollapsibleContent>
                </Collapsible>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="troubleshooting" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Common Issues & Solutions</CardTitle>
              <CardDescription>
                Solutions to frequently encountered problems
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {guide.common_issues.map((issue, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <h4 className="font-medium text-red-600 mb-2">{issue.issue}</h4>
                  <p className="text-sm text-muted-foreground">{issue.solution}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Additional Resources</CardTitle>
              <CardDescription>
                Helpful links and documentation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {guide.additional_resources.map((resource, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      {resource.type === 'documentation' && <FileText className="h-4 w-4" />}
                      {resource.type === 'tutorial' && <Terminal className="h-4 w-4" />}
                      {resource.type === 'community' && <Globe className="h-4 w-4" />}
                      <h4 className="font-medium">{resource.title}</h4>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(resource.url, '_blank')}
                      className="w-full"
                    >
                      <ExternalLink className="h-3 w-3 mr-2" />
                      Open Resource
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ProviderConfigurationGuide;