import React, { useState, useEffect, useCallback, useMemo } from "react";
import { 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useDebounce } from "@/hooks/use-debounce";
"use client";


  Search, 
  Filter, 
  History, 
  BookOpen, 
  FileText, 
  Database, 
  Code, 
  ExternalLink,
  ChevronRight,
  Star,
  Clock,
  Tag,
  Lightbulb,
  X,
  RefreshCw
} from "lucide-react";







  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";



interface Citation {
  source_id: string;
  file_path?: string;
  line_start?: number;
  line_end?: number;
  table_name?: string;
  column_name?: string;
  confidence_score: number;
  context_snippet?: string;
}
interface KnowledgeResult {
  content: string;
  citations: Citation[];
  confidence_score: number;
  source_metadata: Record<string, any>;
  conceptual_relationships: string[];
}
interface SearchResponse {
  results: KnowledgeResult[];
  total_count: number;
  query_info: {
    original_query: string;
    processed_query: string;
    department?: string;
    team?: string;
  };
  routing_info?: {
    routed_department: string;
    routed_team?: string;
    intent_type: string;
    confidence: number;
    reasoning: string;
  };
}
interface KnowledgeStats {
  total_indices: number;
  total_sources: number;
  departments: Record<string, number>;
  teams: Record<string, number>;
}
interface KnowledgePanelProps {
  currentFile?: string;
  currentOperation?: string;
  onCitationClick?: (citation: Citation) => void;
  onResultSelect?: (result: KnowledgeResult) => void;
}
export default function KnowledgePanel({ 
  currentFile, 
  currentOperation, 
  onCitationClick,
  onResultSelect 
}: KnowledgePanelProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState<string>("");
  const [selectedTeam, setSelectedTeam] = useState<string>("");
  const [searchResults, setSearchResults] = useState<KnowledgeResult[]>([]);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [savedQueries, setSavedQueries] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [routingInfo, setRoutingInfo] = useState<SearchResponse['routing_info'] | null>(null);
  const { toast } = useToast();
  // Debounce search query to avoid excessive API calls
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  // Load initial data
  useEffect(() => {
    loadDepartments();
    loadStats();
    loadSuggestions();
    loadSearchHistory();
    loadSavedQueries();
  }, []);
  // Load teams when department changes
  useEffect(() => {
    if (selectedDepartment) {
      loadTeams(selectedDepartment);
    } else {
      setTeams([]);
    }
  }, [selectedDepartment]);
  // Perform search when query changes
  useEffect(() => {
    if (debouncedSearchQuery.trim()) {
      performSearch(debouncedSearchQuery);
    } else {
      setSearchResults([]);
      setRoutingInfo(null);
    }
  }, [debouncedSearchQuery, selectedDepartment, selectedTeam]);
  // Update suggestions when context changes
  useEffect(() => {
    if (currentFile || currentOperation) {
      loadContextualSuggestions();
    }
  }, [currentFile, currentOperation]);
  const loadDepartments = async () => {
    try {
      const response = await fetch("/api/knowledge/departments");
      if (response.ok) {
        const data = await response.json();
        setDepartments(data);
      }
    } catch (error) {
    }
  };
  const loadTeams = async (department: string) => {
    try {
      const response = await fetch(`/api/knowledge/teams?department=${department}`);
      if (response.ok) {
        const data = await response.json();
        setTeams(data);
      }
    } catch (error) {
    }
  };
  const loadStats = async () => {
    try {
      const response = await fetch("/api/knowledge/stats");
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
    }
  };
  const loadSuggestions = async () => {
    try {
      const response = await fetch("/api/knowledge/suggest");
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
    }
  };
  const loadContextualSuggestions = async () => {
    try {
      const params = new URLSearchParams();
      if (currentFile) params.append("current_file", currentFile);
      if (currentOperation) params.append("current_operation", currentOperation);
      const response = await fetch(`/api/knowledge/suggest?${params}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
    }
  };
  const performSearch = async (query: string) => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const requestBody = {
        query: query.trim(),
        department: selectedDepartment || undefined,
        team: selectedTeam || undefined,
        max_results: 10,
        min_confidence: 0.5
      };
      const response = await fetch("/api/knowledge/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });
      if (response.ok) {
        const data: SearchResponse = await response.json();
        setSearchResults(data.results);
        setRoutingInfo(data.routing_info);
        // Add to search history
        addToSearchHistory(query);
      } else {
        toast({
          title: "Search Failed",
          description: "Failed to search knowledge base",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Search Error",
        description: "An error occurred while searching",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  const addToSearchHistory = (query: string) => {
    setSearchHistory(prev => {
      const updated = [query, ...prev.filter(q => q !== query)].slice(0, 10);
      localStorage.setItem("knowledge_search_history", JSON.stringify(updated));
      return updated;
    });
  };
  const loadSearchHistory = () => {
    try {
      const stored = localStorage.getItem("knowledge_search_history");
      if (stored) {
        setSearchHistory(JSON.parse(stored));
      }
    } catch (error) {
    }
  };
  const loadSavedQueries = () => {
    try {
      const stored = localStorage.getItem("knowledge_saved_queries");
      if (stored) {
        setSavedQueries(JSON.parse(stored));
      }
    } catch (error) {
    }
  };
  const saveQuery = (query: string) => {
    setSavedQueries(prev => {
      const updated = [query, ...prev.filter(q => q !== query)].slice(0, 20);
      localStorage.setItem("knowledge_saved_queries", JSON.stringify(updated));
      return updated;
    });
    toast({
      title: "Query Saved",
      description: "Query added to saved queries",
    });
  };
  const removeSavedQuery = (query: string) => {
    setSavedQueries(prev => {
      const updated = prev.filter(q => q !== query);
      localStorage.setItem("knowledge_saved_queries", JSON.stringify(updated));
      return updated;
    });
  };
  const handleCitationClick = (citation: Citation) => {
    if (onCitationClick) {
      onCitationClick(citation);
    } else {
      // Default behavior - show citation details
      toast({
        title: "Citation",
        description: `${citation.file_path || citation.table_name || citation.source_id}${
          citation.line_start ? `:${citation.line_start}` : ""
        }`,
      });
    }
  };
  const handleResultSelect = (result: KnowledgeResult) => {
    if (onResultSelect) {
      onResultSelect(result);
    }
  };
  const getCitationIcon = (citation: Citation) => {
    if (citation.file_path) return <FileText className="h-3 w-3 sm:w-auto md:w-full" />;
    if (citation.table_name) return <Database className="h-3 w-3 sm:w-auto md:w-full" />;
    return <Code className="h-3 w-3 sm:w-auto md:w-full" />;
  };
  const getCitationLabel = (citation: Citation) => {
    if (citation.file_path) {
      return `${citation.file_path}${citation.line_start ? `:${citation.line_start}` : ""}`;
    }
    if (citation.table_name) {
      return `${citation.table_name}${citation.column_name ? `.${citation.column_name}` : ""}`;
    }
    return citation.source_id;
  };
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };
  const clearFilters = () => {
    setSelectedDepartment("");
    setSelectedTeam("");
  };
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <BookOpen className="h-5 w-5 sm:w-auto md:w-full" />
          Knowledge Search
        </CardTitle>
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
          <input
            placeholder="Search knowledge base..."
            value={searchQuery}
            onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
            className="pl-10 pr-10"
          />
          {loading && (
            <RefreshCw className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground sm:w-auto md:w-full" />
          )}
        </div>
        {/* Filters */}
        <div className="flex gap-2">
          <select value={selectedDepartment} onValueChange={setSelectedDepartment} aria-label="Select option">
            <selectTrigger className="flex-1" aria-label="Select option">
              <selectValue placeholder="Department" />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="" aria-label="Select option">All Departments</SelectItem>
              {departments.map(dept => (
                <selectItem key={dept} value={dept} aria-label="Select option">
                  {dept.charAt(0).toUpperCase() + dept.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <select value={selectedTeam} onValueChange={setSelectedTeam} disabled={!selectedDepartment} aria-label="Select option">
            <selectTrigger className="flex-1" aria-label="Select option">
              <selectValue placeholder="Team" />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="" aria-label="Select option">All Teams</SelectItem>
              {teams.map(team => (
                <selectItem key={team} value={team} aria-label="Select option">
                  {team.charAt(0).toUpperCase() + team.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {(selectedDepartment || selectedTeam) && (
            <button variant="outline" size="sm" onClick={clearFilters} aria-label="Button">
              <X className="h-4 w-4 sm:w-auto md:w-full" />
            </Button>
          )}
        </div>
        {/* Routing Info */}
        {routingInfo && (
          <div className="text-xs text-muted-foreground bg-muted p-2 rounded sm:text-sm md:text-base">
            <div className="flex items-center gap-1">
              <Tag className="h-3 w-3 sm:w-auto md:w-full" />
              Routed to: {routingInfo.routed_department}
              {routingInfo.routed_team && `/${routingInfo.routed_team}`}
              <Badge variant="outline" className="ml-2 text-xs sm:text-sm md:text-base">
                {routingInfo.intent_type}
              </Badge>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0 sm:p-4 md:p-6">
        <Tabs defaultValue="results" className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-4 mx-4">
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="stats">Stats</TabsTrigger>
          </TabsList>
          <div className="flex-1 overflow-hidden">
            <TabsContent value="results" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                {searchResults.length > 0 ? (
                  <div className="space-y-3 pb-4">
                    {searchResults.map((result, index) => (
                      <Card 
                        key={index} 
                        className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => handleResultSelect(result)}
                      >
                        <CardContent className="p-3 sm:p-4 md:p-6">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge 
                                variant="outline" 
                                className={`text-xs ${getConfidenceColor(result.confidence_score)}`}
                              >
                                {(result.confidence_score * 100).toFixed(0)}%
                              </Badge>
                              {result.conceptual_relationships.length > 0 && (
                                <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                                  +{result.conceptual_relationships.length} related
                                </Badge>
                              )}
                            </div>
                            <button
                              variant="ghost"
                              size="sm"
                              onClick={(e) = aria-label="Button"> {
                                e.stopPropagation();
                                saveQuery(searchQuery);
                              }}
                            >
                              <Star className="h-3 w-3 sm:w-auto md:w-full" />
                            </Button>
                          </div>
                          <p className="text-sm mb-3 line-clamp-3 md:text-base lg:text-lg">
                            {result.content}
                          </p>
                          {/* Citations */}
                          <div className="space-y-1">
                            {result.citations.slice(0, 3).map((citation, citIndex) => (
                              <div 
                                key={citIndex}
                                className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground cursor-pointer sm:text-sm md:text-base"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCitationClick(citation);
                                }}
                              >
                                {getCitationIcon(citation)}
                                <span className="flex-1 truncate">
                                  {getCitationLabel(citation)}
                                </span>
                                <ExternalLink className="h-3 w-3 sm:w-auto md:w-full" />
                              </div>
                            ))}
                            {result.citations.length > 3 && (
                              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                +{result.citations.length - 3} more citations
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : searchQuery && !loading ? (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <Search className="h-8 w-8 mb-2 sm:w-auto md:w-full" />
                    <p>No results found</p>
                  </div>
                ) : !searchQuery ? (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <BookOpen className="h-8 w-8 mb-2 sm:w-auto md:w-full" />
                    <p>Enter a search query to get started</p>
                  </div>
                ) : null}
              </ScrollArea>
            </TabsContent>
            <TabsContent value="suggestions" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-2 pb-4">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      variant="ghost"
                      className="w-full justify-start text-left h-auto p-3 sm:p-4 md:p-6"
                      onClick={() = aria-label="Button"> setSearchQuery(suggestion)}
                    >
                      <div className="flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-yellow-500 sm:w-auto md:w-full" />
                        <span className="text-sm md:text-base lg:text-lg">{suggestion}</span>
                      </div>
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="history" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-4 pb-4">
                  {/* Search History */}
                  <div>
                    <h4 className="text-sm font-medium mb-2 flex items-center gap-2 md:text-base lg:text-lg">
                      <History className="h-4 w-4 sm:w-auto md:w-full" />
                      Recent Searches
                    </h4>
                    <div className="space-y-1">
                      {searchHistory.map((query, index) => (
                        <button
                          key={index}
                          variant="ghost"
                          className="w-full justify-start text-left h-auto p-2 sm:p-4 md:p-6"
                          onClick={() = aria-label="Button"> setSearchQuery(query)}
                        >
                          <div className="flex items-center gap-2">
                            <Clock className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
                            <span className="text-sm truncate md:text-base lg:text-lg">{query}</span>
                          </div>
                        </Button>
                      ))}
                    </div>
                  </div>
                  <Separator />
                  {/* Saved Queries */}
                  <div>
                    <h4 className="text-sm font-medium mb-2 flex items-center gap-2 md:text-base lg:text-lg">
                      <Star className="h-4 w-4 sm:w-auto md:w-full" />
                      Saved Queries
                    </h4>
                    <div className="space-y-1">
                      {savedQueries.map((query, index) => (
                        <div key={index} className="flex items-center gap-1">
                          <button
                            variant="ghost"
                            className="flex-1 justify-start text-left h-auto p-2 sm:p-4 md:p-6"
                            onClick={() = aria-label="Button"> setSearchQuery(query)}
                          >
                            <span className="text-sm truncate md:text-base lg:text-lg">{query}</span>
                          </Button>
                          <button
                            variant="ghost"
                            size="sm"
                            onClick={() = aria-label="Button"> removeSavedQuery(query)}
                          >
                            <X className="h-3 w-3 sm:w-auto md:w-full" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="stats" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                {stats && (
                  <div className="space-y-4 pb-4">
                    <div className="grid grid-cols-2 gap-4">
                      <Card>
                        <CardContent className="p-3 text-center sm:p-4 md:p-6">
                          <div className="text-2xl font-bold">{stats.total_indices}</div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Indices</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-3 text-center sm:p-4 md:p-6">
                          <div className="text-2xl font-bold">{stats.total_sources}</div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Sources</div>
                        </CardContent>
                      </Card>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Departments</h4>
                      <div className="space-y-1">
                        {Object.entries(stats.departments).map(([dept, count]) => (
                          <div key={dept} className="flex justify-between text-sm md:text-base lg:text-lg">
                            <span className="capitalize">{dept}</span>
                            <Badge variant="outline">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Teams</h4>
                      <div className="space-y-1">
                        {Object.entries(stats.teams).map(([team, count]) => (
                          <div key={team} className="flex justify-between text-sm md:text-base lg:text-lg">
                            <span className="capitalize">{team}</span>
                            <Badge variant="outline">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
}
