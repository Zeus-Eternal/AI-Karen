"""
Organizational Hierarchy and Context Routing

This module implements the organizational hierarchy system that mirrors human
organizational cognition with Department → Team routing and context-aware
knowledge retrieval with precise citation tracking.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import asyncio

from .index_hub import Department, Team, KnowledgeQuery, KnowledgeResult, Citation


class IntentType(Enum):
    """Types of user intents for routing."""
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    BUSINESS_LOGIC = "business_logic"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class ContextRoute:
    """Represents a routing decision with confidence."""
    department: Department
    team: Optional[Team]
    intent_type: IntentType
    confidence: float
    reasoning: str


@dataclass
class GroundingContext:
    """Context for grounding AI requests with precise citations."""
    file_spans: List[Tuple[str, int, int]]  # (file_path, start_line, end_line)
    schema_objects: List[Tuple[str, str]]   # (table_name, column_name)
    code_symbols: List[Tuple[str, str]]     # (symbol_name, symbol_type)
    documentation_refs: List[str]           # documentation references
    confidence_score: float = 0.0


class OrganizationalHierarchy:
    """
    Implements organizational hierarchy routing and context-aware retrieval
    that mirrors human organizational cognition patterns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Intent classification patterns
        self.intent_patterns = self._build_intent_patterns()
        
        # Department/Team routing rules
        self.routing_rules = self._build_routing_rules()
        
        # Context grounding patterns
        self.grounding_patterns = self._build_grounding_patterns()
    
    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build regex patterns for intent classification."""
        return {
            IntentType.CODE_REVIEW: [
                r'\b(review|analyze|check|audit|quality)\b.*\b(code|function|class|method)\b',
                r'\b(refactor|improve|optimize)\b.*\b(code|implementation)\b',
                r'\b(bug|error|issue|problem)\b.*\b(fix|solve|resolve)\b'
            ],
            IntentType.DEBUGGING: [
                r'\b(debug|troubleshoot|diagnose)\b',
                r'\b(error|exception|crash|failure)\b',
                r'\b(stack trace|log|console)\b',
                r'\b(why.*not working|what.*wrong)\b'
            ],
            IntentType.ARCHITECTURE: [
                r'\b(architecture|design|structure|pattern)\b',
                r'\b(system|component|module|service)\b.*\b(design|structure)\b',
                r'\b(scalability|performance|maintainability)\b'
            ],
            IntentType.DEPLOYMENT: [
                r'\b(deploy|deployment|release|publish)\b',
                r'\b(docker|kubernetes|container)\b',
                r'\b(ci/cd|pipeline|build)\b',
                r'\b(environment|staging|production)\b'
            ],
            IntentType.MONITORING: [
                r'\b(monitor|metrics|alerts|logs)\b',
                r'\b(performance|health|status)\b',
                r'\b(prometheus|grafana|observability)\b'
            ],
            IntentType.BUSINESS_LOGIC: [
                r'\b(business|logic|rules|requirements)\b',
                r'\b(workflow|process|procedure)\b',
                r'\b(validation|calculation|algorithm)\b'
            ],
            IntentType.DOCUMENTATION: [
                r'\b(document|documentation|docs|readme)\b',
                r'\b(explain|describe|how to)\b',
                r'\b(api|reference|guide|tutorial)\b'
            ],
            IntentType.TESTING: [
                r'\b(test|testing|spec|unit test|integration test)\b',
                r'\b(coverage|assertion|mock)\b',
                r'\b(pytest|jest|junit)\b'
            ]
        }
    
    def _build_routing_rules(self) -> Dict[IntentType, List[Tuple[Department, Optional[Team], float]]]:
        """Build routing rules mapping intents to departments/teams with confidence scores."""
        return {
            IntentType.CODE_REVIEW: [
                (Department.ENGINEERING, Team.BACKEND, 0.9),
                (Department.ENGINEERING, Team.FRONTEND, 0.8),
                (Department.ENGINEERING, Team.QA, 0.7)
            ],
            IntentType.DEBUGGING: [
                (Department.ENGINEERING, Team.BACKEND, 0.9),
                (Department.ENGINEERING, Team.FRONTEND, 0.8),
                (Department.OPERATIONS, Team.MONITORING, 0.6)
            ],
            IntentType.ARCHITECTURE: [
                (Department.ENGINEERING, Team.BACKEND, 0.9),
                (Department.ENGINEERING, None, 0.8),
                (Department.OPERATIONS, Team.INFRASTRUCTURE, 0.6)
            ],
            IntentType.DEPLOYMENT: [
                (Department.OPERATIONS, Team.DEVOPS, 0.9),
                (Department.OPERATIONS, Team.INFRASTRUCTURE, 0.8),
                (Department.ENGINEERING, Team.BACKEND, 0.6)
            ],
            IntentType.MONITORING: [
                (Department.OPERATIONS, Team.MONITORING, 0.9),
                (Department.OPERATIONS, Team.INFRASTRUCTURE, 0.7),
                (Department.OPERATIONS, Team.DEVOPS, 0.6)
            ],
            IntentType.BUSINESS_LOGIC: [
                (Department.BUSINESS, Team.PRODUCT, 0.9),
                (Department.ENGINEERING, Team.BACKEND, 0.7),
                (Department.BUSINESS, None, 0.6)
            ],
            IntentType.DOCUMENTATION: [
                (Department.ENGINEERING, None, 0.8),
                (Department.BUSINESS, Team.PRODUCT, 0.7),
                (Department.OPERATIONS, None, 0.6)
            ],
            IntentType.TESTING: [
                (Department.ENGINEERING, Team.QA, 0.9),
                (Department.ENGINEERING, Team.BACKEND, 0.8),
                (Department.ENGINEERING, Team.FRONTEND, 0.7)
            ]
        }
    
    def _build_grounding_patterns(self) -> Dict[str, str]:
        """Build patterns for extracting grounding context."""
        return {
            'file_reference': r'(?:file:|in\s+)([^\s:]+\.(?:py|js|ts|java|cpp|h|sql|md|json|yaml|yml))(?::(\d+)(?:-(\d+))?)?',
            'table_reference': r'\b(?:table|from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'column_reference': r'\b(?:column|field)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'function_reference': r'\b(?:function|method|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'class_reference': r'\b(?:class)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'variable_reference': r'\b(?:variable|var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b'
        }
    
    async def classify_intent(self, query_text: str) -> Tuple[IntentType, float]:
        """
        Classify user intent from query text using pattern matching.
        Returns the most likely intent with confidence score.
        """
        query_lower = query_text.lower()
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    matches += 1
                    score += 1.0 / len(patterns)  # Normalize by pattern count
            
            if matches > 0:
                # Boost score based on number of matching patterns
                intent_scores[intent_type] = score * (1 + 0.1 * matches)
        
        if not intent_scores:
            # Default to documentation if no clear intent
            return IntentType.DOCUMENTATION, 0.3
        
        # Return intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], min(best_intent[1], 1.0)
    
    async def route_to_department_team(self, intent: IntentType, query_text: str) -> ContextRoute:
        """
        Route intent to appropriate department and team based on routing rules.
        """
        if intent not in self.routing_rules:
            # Default routing
            return ContextRoute(
                department=Department.ENGINEERING,
                team=None,
                intent_type=intent,
                confidence=0.3,
                reasoning="Default routing - no specific rules found"
            )
        
        # Get routing options for this intent
        routing_options = self.routing_rules[intent]
        
        # Apply context-specific boosting
        boosted_options = []
        for dept, team, base_confidence in routing_options:
            # Boost confidence based on query context
            boost = self._calculate_context_boost(query_text, dept, team)
            final_confidence = min(base_confidence + boost, 1.0)
            boosted_options.append((dept, team, final_confidence))
        
        # Select best option
        best_option = max(boosted_options, key=lambda x: x[2])
        dept, team, confidence = best_option
        
        reasoning = f"Intent '{intent.value}' routed to {dept.value}"
        if team:
            reasoning += f"/{team.value}"
        reasoning += f" with confidence {confidence:.2f}"
        
        return ContextRoute(
            department=dept,
            team=team,
            intent_type=intent,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _calculate_context_boost(self, query_text: str, dept: Department, team: Optional[Team]) -> float:
        """Calculate confidence boost based on query context."""
        boost = 0.0
        query_lower = query_text.lower()
        
        # Department-specific keywords
        dept_keywords = {
            Department.ENGINEERING: ['code', 'function', 'class', 'api', 'algorithm', 'implementation'],
            Department.OPERATIONS: ['deploy', 'server', 'infrastructure', 'monitoring', 'performance'],
            Department.BUSINESS: ['requirement', 'feature', 'user', 'business', 'product', 'workflow']
        }
        
        # Team-specific keywords
        team_keywords = {
            Team.FRONTEND: ['ui', 'frontend', 'react', 'vue', 'angular', 'css', 'html', 'javascript'],
            Team.BACKEND: ['api', 'database', 'server', 'backend', 'python', 'java', 'sql'],
            Team.DEVOPS: ['docker', 'kubernetes', 'ci/cd', 'pipeline', 'deployment', 'infrastructure'],
            Team.QA: ['test', 'testing', 'quality', 'bug', 'validation', 'coverage'],
            Team.INFRASTRUCTURE: ['server', 'network', 'cloud', 'aws', 'azure', 'infrastructure'],
            Team.SECURITY: ['security', 'auth', 'encryption', 'vulnerability', 'compliance'],
            Team.MONITORING: ['metrics', 'logs', 'alerts', 'monitoring', 'observability', 'prometheus'],
            Team.PRODUCT: ['feature', 'requirement', 'user story', 'product', 'roadmap'],
            Team.MARKETING: ['campaign', 'marketing', 'analytics', 'conversion', 'engagement'],
            Team.SALES: ['sales', 'customer', 'revenue', 'pipeline', 'crm']
        }
        
        # Check department keywords
        if dept in dept_keywords:
            for keyword in dept_keywords[dept]:
                if keyword in query_lower:
                    boost += 0.1
        
        # Check team keywords
        if team and team in team_keywords:
            for keyword in team_keywords[team]:
                if keyword in query_lower:
                    boost += 0.15
        
        return min(boost, 0.5)  # Cap boost at 0.5
    
    async def extract_grounding_context(self, query_text: str) -> GroundingContext:
        """
        Extract grounding context from query text for precise citations.
        """
        context = GroundingContext(
            file_spans=[],
            schema_objects=[],
            code_symbols=[],
            documentation_refs=[]
        )
        
        # Extract file references
        file_matches = re.finditer(self.grounding_patterns['file_reference'], query_text)
        for match in file_matches:
            file_path = match.group(1)
            start_line = int(match.group(2)) if match.group(2) else None
            end_line = int(match.group(3)) if match.group(3) else start_line
            
            if start_line:
                context.file_spans.append((file_path, start_line, end_line))
        
        # Extract table references
        table_matches = re.finditer(self.grounding_patterns['table_reference'], query_text)
        for match in table_matches:
            table_name = match.group(1)
            context.schema_objects.append((table_name, None))
        
        # Extract column references
        column_matches = re.finditer(self.grounding_patterns['column_reference'], query_text)
        for match in column_matches:
            column_name = match.group(1)
            # Try to associate with nearby table reference
            context.schema_objects.append((None, column_name))
        
        # Extract code symbols
        for symbol_type in ['function', 'class', 'variable']:
            pattern = self.grounding_patterns[f'{symbol_type}_reference']
            matches = re.finditer(pattern, query_text)
            for match in matches:
                symbol_name = match.group(1)
                context.code_symbols.append((symbol_name, symbol_type))
        
        # Calculate confidence based on extracted context
        context_items = (
            len(context.file_spans) + 
            len(context.schema_objects) + 
            len(context.code_symbols) + 
            len(context.documentation_refs)
        )
        context.confidence_score = min(context_items * 0.2, 1.0)
        
        return context
    
    async def create_contextual_query(
        self, 
        original_query: str, 
        route: ContextRoute, 
        grounding: GroundingContext
    ) -> KnowledgeQuery:
        """
        Create a contextual knowledge query based on routing and grounding information.
        """
        # Enhance query with context
        enhanced_query = original_query
        
        # Add department/team context to query
        if route.team:
            enhanced_query += f" [Context: {route.department.value}/{route.team.value}]"
        else:
            enhanced_query += f" [Context: {route.department.value}]"
        
        # Add grounding context
        if grounding.file_spans:
            file_refs = ", ".join([f"{fs[0]}:{fs[1]}" for fs in grounding.file_spans])
            enhanced_query += f" [Files: {file_refs}]"
        
        if grounding.code_symbols:
            symbols = ", ".join([f"{cs[0]}({cs[1]})" for cs in grounding.code_symbols])
            enhanced_query += f" [Symbols: {symbols}]"
        
        return KnowledgeQuery(
            text=enhanced_query,
            department=route.department,
            team=route.team,
            max_results=10,
            min_confidence=0.5,
            require_citations=True
        )
    
    async def enhance_results_with_citations(
        self, 
        results: List[KnowledgeResult], 
        grounding: GroundingContext
    ) -> List[KnowledgeResult]:
        """
        Enhance knowledge results with precise citations from grounding context.
        """
        enhanced_results = []
        
        for result in results:
            # Create enhanced citations
            enhanced_citations = list(result.citations)
            
            # Add file span citations if relevant
            for file_path, start_line, end_line in grounding.file_spans:
                if file_path in result.content or any(file_path in c.file_path or '' for c in result.citations):
                    citation = Citation(
                        source_id=f"grounding_{file_path}",
                        file_path=file_path,
                        line_start=start_line,
                        line_end=end_line,
                        confidence_score=grounding.confidence_score,
                        context_snippet=f"Referenced in query: {file_path}:{start_line}"
                    )
                    enhanced_citations.append(citation)
            
            # Add schema object citations
            for table_name, column_name in grounding.schema_objects:
                if table_name and (table_name in result.content):
                    citation = Citation(
                        source_id=f"schema_{table_name}",
                        table_name=table_name,
                        column_name=column_name,
                        confidence_score=grounding.confidence_score,
                        context_snippet=f"Schema reference: {table_name}.{column_name or '*'}"
                    )
                    enhanced_citations.append(citation)
            
            # Create enhanced result
            enhanced_result = KnowledgeResult(
                content=result.content,
                citations=enhanced_citations,
                confidence_score=max(result.confidence_score, grounding.confidence_score),
                source_metadata=result.source_metadata,
                conceptual_relationships=result.conceptual_relationships
            )
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    async def process_query_with_routing(
        self, 
        query_text: str, 
        index_hub
    ) -> Tuple[ContextRoute, List[KnowledgeResult]]:
        """
        Complete query processing with intent classification, routing, and retrieval.
        """
        try:
            # Step 1: Classify intent
            intent, intent_confidence = await self.classify_intent(query_text)
            self.logger.info(f"Classified intent: {intent.value} (confidence: {intent_confidence:.2f})")
            
            # Step 2: Route to department/team
            route = await self.route_to_department_team(intent, query_text)
            self.logger.info(f"Routing: {route.reasoning}")
            
            # Step 3: Extract grounding context
            grounding = await self.extract_grounding_context(query_text)
            self.logger.info(f"Grounding context: {len(grounding.file_spans)} files, {len(grounding.code_symbols)} symbols")
            
            # Step 4: Create contextual query
            contextual_query = await self.create_contextual_query(query_text, route, grounding)
            
            # Step 5: Query knowledge base
            results = await index_hub.query_knowledge(contextual_query)
            
            # Step 6: Enhance results with citations
            enhanced_results = await self.enhance_results_with_citations(results, grounding)
            
            return route, enhanced_results
        
        except Exception as e:
            self.logger.error(f"Error processing query with routing: {e}")
            # Return default route and empty results
            default_route = ContextRoute(
                department=Department.ENGINEERING,
                team=None,
                intent_type=IntentType.DOCUMENTATION,
                confidence=0.1,
                reasoning="Error in processing - using default route"
            )
            return default_route, []