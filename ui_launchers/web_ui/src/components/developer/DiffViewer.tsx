import React, { useState, useEffect, useMemo } from "react";
import { 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
"use client";



  FileText, 
  Eye, 
  EyeOff, 
  Download, 
  Upload, 
  Check, 
  X, 
  RotateCcw,
  Copy,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Search,
  Filter,
  GitBranch,
  Plus,
  Minus
} from "lucide-react";








  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";



export type ChangeType = "added" | "removed" | "modified" | "renamed" | "unchanged";
export type DiffMode = "side-by-side" | "unified" | "split";

export interface DiffLine {
  lineNumber: number;
  content: string;
  type: ChangeType;
  oldLineNumber?: number;
  newLineNumber?: number;
}

export interface FileDiff {
  id: string;
  filePath: string;
  oldFilePath?: string; // for renamed files
  changeType: ChangeType;
  additions: number;
  deletions: number;
  oldContent: string;
  newContent: string;
  lines: DiffLine[];
  binary: boolean;
  selected: boolean; // for selective application
  applied: boolean;
  metadata?: {
    size: number;
    lastModified: Date;
    permissions?: string;
    encoding?: string;
  };
}

export interface DiffViewerProps {
  diffs: FileDiff[];
  mode?: DiffMode;
  onFileSelect?: (fileId: string, selected: boolean) => void;
  onFileApply?: (fileId: string) => Promise<void>;
  onFileRevert?: (fileId: string) => Promise<void>;
  onApplySelected?: () => Promise<void>;
  onRevertAll?: () => Promise<void>;
  onFileOpen?: (filePath: string) => void;
  readonly?: boolean;
  showLineNumbers?: boolean;
  showWhitespace?: boolean;
  contextLines?: number;
}

export default function DiffViewer({
  diffs,
  mode = "side-by-side",
  onFileSelect,
  onFileApply,
  onFileRevert,
  onApplySelected,
  onRevertAll,
  onFileOpen,
  readonly = false,
  showLineNumbers = true,
  showWhitespace = false,
  contextLines = 3
}: DiffViewerProps) {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<ChangeType | "all">("all");
  const [diffMode, setDiffMode] = useState<DiffMode>(mode);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  
  const { toast } = useToast();

  const filteredDiffs = useMemo(() => {
    let filtered = diffs;
    
    // Filter by change type
    if (filterType !== "all") {
      filtered = filtered.filter(diff => diff.changeType === filterType);
    }
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(diff => 
        diff.filePath.toLowerCase().includes(query) ||
        diff.oldFilePath?.toLowerCase().includes(query) ||
        diff.newContent.toLowerCase().includes(query) ||
        diff.oldContent.toLowerCase().includes(query)
      );
    }
    
    return filtered;
  }, [diffs, filterType, searchQuery]);

  const selectedDiffs = useMemo(() => {
    return diffs.filter(diff => diff.selected);
  }, [diffs]);

  const appliedDiffs = useMemo(() => {
    return diffs.filter(diff => diff.applied);
  }, [diffs]);

  const getChangeTypeColor = (type: ChangeType) => {
    switch (type) {
      case "added": return "text-green-600 bg-green-50 border-green-200";
      case "removed": return "text-red-600 bg-red-50 border-red-200";
      case "modified": return "text-blue-600 bg-blue-50 border-blue-200";
      case "renamed": return "text-purple-600 bg-purple-50 border-purple-200";
      case "unchanged": return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getChangeTypeIcon = (type: ChangeType) => {
    switch (type) {
      case "added": return <Plus className="h-3 w-3 sm:w-auto md:w-full" />;
      case "removed": return <Minus className="h-3 w-3 sm:w-auto md:w-full" />;
      case "modified": return <FileText className="h-3 w-3 sm:w-auto md:w-full" />;
      case "renamed": return <GitBranch className="h-3 w-3 sm:w-auto md:w-full" />;
      case "unchanged": return <Check className="h-3 w-3 sm:w-auto md:w-full" />;
    }
  };

  const handleFileSelect = (fileId: string, selected: boolean) => {
    if (onFileSelect) {
      onFileSelect(fileId, selected);
    }
  };

  const handleFileApply = async (fileId: string) => {
    if (!onFileApply) return;
    
    try {
      await onFileApply(fileId);
      toast({
        title: "Changes Applied",
        description: "File changes have been applied successfully",
      });
    } catch (error) {
      toast({
        title: "Apply Failed",
        description: `Failed to apply changes: ${error}`,
        variant: "destructive",
      });
    }
  };

  const handleFileRevert = async (fileId: string) => {
    if (!onFileRevert) return;
    
    try {
      await onFileRevert(fileId);
      toast({
        title: "Changes Reverted",
        description: "File changes have been reverted",
      });
    } catch (error) {
      toast({
        title: "Revert Failed",
        description: `Failed to revert changes: ${error}`,
        variant: "destructive",
      });
    }
  };

  const handleApplySelected = async () => {
    if (!onApplySelected) return;
    
    try {
      await onApplySelected();
      toast({
        title: "Selected Changes Applied",
        description: `Applied changes to ${selectedDiffs.length} files`,
      });
    } catch (error) {
      toast({
        title: "Apply Failed",
        description: `Failed to apply selected changes: ${error}`,
        variant: "destructive",
      });
    }
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({
      title: "Copied",
      description: "Content copied to clipboard",
    });
  };

  const toggleFileExpansion = (fileId: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(fileId)) {
      newExpanded.delete(fileId);
    } else {
      newExpanded.add(fileId);
    }
    setExpandedFiles(newExpanded);
  };

  const renderDiffLine = (line: DiffLine, isOld: boolean = false) => {
    const lineClass = `font-mono text-sm px-3 py-1 ${
      line.type === "added" ? "bg-green-50 text-green-800" :
      line.type === "removed" ? "bg-red-50 text-red-800" :
      "bg-white"
    }`;
    
    const lineNumber = isOld ? line.oldLineNumber : line.newLineNumber;
    
    return (
      <div key={`${line.lineNumber}-${isOld}`} className={lineClass}>
        <div className="flex">
          {showLineNumbers && (
            <span className="w-12 text-right text-gray-400 mr-3 select-none sm:w-auto md:w-full">
              {lineNumber || ""}
            </span>
          )}
          <span className="flex-1">
            {showWhitespace ? line.content.replace(/ /g, "·").replace(/\t/g, "→") : line.content}
          </span>
        </div>
      </div>
    );
  };

  const renderSideBySideDiff = (diff: FileDiff) => {
    const oldLines = diff.lines.filter(line => line.type !== "added");
    const newLines = diff.lines.filter(line => line.type !== "removed");
    
    return (
      <div className="grid grid-cols-2 gap-1 border rounded">
        {/* Old Content */}
        <div className="border-r">
          <div className="bg-red-50 px-3 py-2 text-sm font-medium text-red-800 border-b md:text-base lg:text-lg">
            Original ({diff.oldFilePath || diff.filePath})
          </div>
          <ScrollArea className="h-96">
            {oldLines.map(line => renderDiffLine(line, true))}
          </ScrollArea>
        </div>
        
        {/* New Content */}
        <div>
          <div className="bg-green-50 px-3 py-2 text-sm font-medium text-green-800 border-b md:text-base lg:text-lg">
            Modified ({diff.filePath})
          </div>
          <ScrollArea className="h-96">
            {newLines.map(line => renderDiffLine(line, false))}
          </ScrollArea>
        </div>
      </div>
    );
  };

  const renderUnifiedDiff = (diff: FileDiff) => {
    return (
      <div className="border rounded">
        <div className="bg-gray-50 px-3 py-2 text-sm font-medium border-b md:text-base lg:text-lg">
          {diff.filePath}
        </div>
        <ScrollArea className="h-96">
          {diff.lines.map(line => renderDiffLine(line))}
        </ScrollArea>
      </div>
    );
  };

  const getTotalChanges = () => {
    const additions = diffs.reduce((sum, diff) => sum + diff.additions, 0);
    const deletions = diffs.reduce((sum, diff) => sum + diff.deletions, 0);
    return { additions, deletions };
  };

  const { additions, deletions } = getTotalChanges();

  if (diffs.length === 0) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
          <h3 className="text-lg font-semibold mb-2">No Changes</h3>
          <p className="text-muted-foreground">
            No file differences to display. All files are up to date.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 sm:w-auto md:w-full" />
            File Changes
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-green-600">
              +{additions}
            </Badge>
            <Badge variant="outline" className="text-red-600">
              -{deletions}
            </Badge>
            <Badge variant="outline">
              {diffs.length} files
            </Badge>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            <input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
              className="w-48 sm:w-auto md:w-full"
            />
          </div>
          
          <select value={filterType} onValueChange={(value: ChangeType | "all") = aria-label="Select option"> setFilterType(value)}>
            <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="all" aria-label="Select option">All Changes</SelectItem>
              <selectItem value="added" aria-label="Select option">Added</SelectItem>
              <selectItem value="removed" aria-label="Select option">Removed</SelectItem>
              <selectItem value="modified" aria-label="Select option">Modified</SelectItem>
              <selectItem value="renamed" aria-label="Select option">Renamed</SelectItem>
            </SelectContent>
          </Select>
          
          <select value={diffMode} onValueChange={(value: DiffMode) = aria-label="Select option"> setDiffMode(value)}>
            <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="side-by-side" aria-label="Select option">Side by Side</SelectItem>
              <selectItem value="unified" aria-label="Select option">Unified</SelectItem>
              <selectItem value="split" aria-label="Select option">Split</SelectItem>
            </SelectContent>
          </Select>

          {!readonly && (
            <>
              <Separator orientation="vertical" className="h-6" />
              
              <button
                onClick={handleApplySelected}
                disabled={selectedDiffs.length === 0}
                size="sm"
                className="bg-green-600 hover:bg-green-700"
               aria-label="Button">
                <Check className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                Apply Selected ({selectedDiffs.length})
              </Button>
              
              <button
                onClick={onRevertAll}
                variant="outline"
                size="sm"
               aria-label="Button">
                <RotateCcw className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                Revert All
              </Button>
            </>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0 sm:p-4 md:p-6">
        <div className="flex h-full">
          {/* File List */}
          <div className="w-80 border-r bg-muted/30 sm:w-auto md:w-full">
            <div className="p-3 border-b bg-background sm:p-4 md:p-6">
              <h4 className="font-medium text-sm md:text-base lg:text-lg">Files ({filteredDiffs.length})</h4>
            </div>
            <ScrollArea className="h-full">
              <div className="p-2 space-y-1 sm:p-4 md:p-6">
                {filteredDiffs.map((diff) => (
                  <Card 
                    key={diff.id}
                    className={`cursor-pointer transition-colors ${
                      selectedFileId === diff.id ? "ring-2 ring-blue-500" : ""
                    }`}
                    onClick={() => setSelectedFileId(diff.id)}
                  >
                    <CardContent className="p-3 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2">
                        {!readonly && (
                          <Checkbox
                            checked={diff.selected}
                            onCheckedChange={(checked) => 
                              handleFileSelect(diff.id, checked as boolean)
                            }
                            onClick={(e) => e.stopPropagation()}
                          />
                        )}
                        
                        <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                          <div className="flex items-center gap-1">
                            {getChangeTypeIcon(diff.changeType)}
                            <span className="text-sm font-medium truncate md:text-base lg:text-lg">
                              {diff.filePath.split('/').pop()}
                            </span>
                            {diff.applied && (
                              <Check className="h-3 w-3 text-green-500 sm:w-auto md:w-full" />
                            )}
                          </div>
                          
                          <div className="text-xs text-muted-foreground truncate sm:text-sm md:text-base">
                            {diff.filePath}
                          </div>
                          
                          <div className="flex items-center gap-2 mt-1">
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${getChangeTypeColor(diff.changeType)}`}
                            >
                              {diff.changeType}
                            </Badge>
                            
                            {diff.additions > 0 && (
                              <span className="text-xs text-green-600 sm:text-sm md:text-base">+{diff.additions}</span>
                            )}
                            
                            {diff.deletions > 0 && (
                              <span className="text-xs text-red-600 sm:text-sm md:text-base">-{diff.deletions}</span>
                            )}
                          </div>
                        </div>
                        
                        {!readonly && (
                          <div className="flex flex-col gap-1">
                            {!diff.applied && (
                              <button
                                onClick={(e) = aria-label="Button"> {
                                  e.stopPropagation();
                                  handleFileApply(diff.id);
                                }}
                                size="sm"
                                variant="outline"
                                className="h-6 px-2"
                              >
                                <Check className="h-3 w-3 sm:w-auto md:w-full" />
                              </Button>
                            )}
                            
                            {diff.applied && (
                              <button
                                onClick={(e) = aria-label="Button"> {
                                  e.stopPropagation();
                                  handleFileRevert(diff.id);
                                }}
                                size="sm"
                                variant="outline"
                                className="h-6 px-2"
                              >
                                <RotateCcw className="h-3 w-3 sm:w-auto md:w-full" />
                              </Button>
                            )}
                            
                            <button
                              onClick={(e) = aria-label="Button"> {
                                e.stopPropagation();
                                onFileOpen?.(diff.filePath);
                              }}
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2"
                            >
                              <ExternalLink className="h-3 w-3 sm:w-auto md:w-full" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Diff Content */}
          <div className="flex-1 overflow-hidden">
            {selectedFileId ? (
              (() => {
                const selectedDiff = diffs.find(d => d.id === selectedFileId);
                if (!selectedDiff) return null;

                return (
                  <div className="h-full flex flex-col">
                    <div className="p-3 border-b bg-background sm:p-4 md:p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{selectedDiff.filePath}</h4>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            {selectedDiff.additions} additions, {selectedDiff.deletions} deletions
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() = aria-label="Button"> copyToClipboard(selectedDiff.newContent)}
                            size="sm"
                            variant="outline"
                          >
                            <Copy className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                            Copy
                          </Button>
                          
                          {!readonly && !selectedDiff.applied && (
                            <button
                              onClick={() = aria-label="Button"> handleFileApply(selectedDiff.id)}
                              size="sm"
                              className="bg-green-600 hover:bg-green-700"
                            >
                              <Check className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                              Apply
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex-1 overflow-hidden p-3 sm:p-4 md:p-6">
                      {selectedDiff.binary ? (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
                            <p className="text-muted-foreground">Binary file - cannot show diff</p>
                          </div>
                        </div>
                      ) : (
                        <>
                          {diffMode === "side-by-side" && renderSideBySideDiff(selectedDiff)}
                          {diffMode === "unified" && renderUnifiedDiff(selectedDiff)}
                          {diffMode === "split" && renderSideBySideDiff(selectedDiff)}
                        </>
                      )}
                    </div>
                  </div>
                );
              })()
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
                  <h3 className="text-lg font-semibold mb-2">Select a File</h3>
                  <p className="text-muted-foreground">
                    Choose a file from the list to view its changes.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}