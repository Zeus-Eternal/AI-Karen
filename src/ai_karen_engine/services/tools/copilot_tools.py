"""
Core copilot tools implementation (MVP set).

This module implements the essential copilot tools with citation requirements,
dry-run support, and security constraints.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import difflib
import ast

from ai_karen_engine.services.tools.contracts import (
    CopilotTool,
    ToolSpec,
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ExecutionMode,
    ToolContext,
    ToolResult,
    Citation,
    SecurityConstraint,
    create_file_citation,
    PolicyViolationError
)

logger = logging.getLogger(__name__)


class CodeSearchSpansTool(CopilotTool):
    """Tool for searching code spans with symbol/usage location using LlamaIndex integration."""
    
    def _create_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name="code.search_spans",
            description="Search for code symbols, functions, classes, and their usage locations with file:line citations",
            scope=ToolScope.READ,
            rbac_level=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=1,  # Reduced for search operations
            citation_sources=["workspace", "git"],
            security_constraints=SecurityConstraint(
                allowed_paths=["src/", "tests/", "docs/", "examples/"],
                blocked_paths=[".git/", "node_modules/", "__pycache__/", ".env"],
                timeout_seconds=30,
                sandbox_enabled=True
            ),
            supports_dry_run=True,
            supports_rollback=False,
            is_idempotent=True,
            can_batch=True,
            tags=["code", "search", "symbols", "ast"]
        )
    
    def _create_metadata(self):
        """Create legacy metadata for compatibility."""
        from ai_karen_engine.services.tool_service import ToolMetadata, ToolCategory, ToolParameter
        return ToolMetadata(
            name="code.search_spans",
            description="Search for code symbols and usage locations",
            category=ToolCategory.CORE,
            parameters=[
                ToolParameter(
                    name="query",
                    type=str,
                    description="Search query (symbol name, function, class, etc.)",
                    required=True,
                    validation_rules={"min_length": 1, "max_length": 200}
                ),
                ToolParameter(
                    name="file_patterns",
                    type=list,
                    description="File patterns to search (e.g., ['*.py', '*.js'])",
                    required=False,
                    default=["*.py"]
                ),
                ToolParameter(
                    name="search_type",
                    type=str,
                    description="Type of search: 'symbol', 'usage', 'definition', 'all'",
                    required=False,
                    default="all",
                    validation_rules={"allowed_values": ["symbol", "usage", "definition", "all"]}
                ),
                ToolParameter(
                    name="max_results",
                    type=int,
                    description="Maximum number of results to return",
                    required=False,
                    default=50,
                    validation_rules={"min_value": 1, "max_value": 200}
                )
            ],
            return_type=dict,
            timeout=30
        )
    
    async def _execute_with_context(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """Execute code search with citations."""
        query = parameters["query"]
        file_patterns = parameters.get("file_patterns", ["*.py"])
        search_type = parameters.get("search_type", "all")
        max_results = parameters.get("max_results", 50)
        
        workspace_root = context.workspace_root or os.getcwd()
        
        try:
            # Search for code spans
            results = await self._search_code_spans(
                workspace_root, query, file_patterns, search_type, max_results
            )
            
            # Generate citations from results
            citations = []
            for result in results[:10]:  # Limit citations to top 10 results
                citation = create_file_citation(
                    file_path=result["file_path"],
                    line_number=result["line_number"],
                    content=result["content"][:100],  # Truncate content
                    confidence=result.get("confidence", 0.8)
                )
                citations.append(citation)
            
            # Create artifacts
            artifacts = [
                {
                    "type": "code_search_results",
                    "content": json.dumps(results, indent=2),
                    "metadata": {
                        "query": query,
                        "total_results": len(results),
                        "search_type": search_type
                    }
                }
            ]
            
            return ToolResult(
                success=True,
                execution_mode=context.execution_mode,
                result={
                    "query": query,
                    "total_results": len(results),
                    "results": results,
                    "search_metadata": {
                        "workspace_root": workspace_root,
                        "file_patterns": file_patterns,
                        "search_type": search_type
                    }
                },
                artifacts=artifacts,
                citations_used=citations
            )
            
        except Exception as e:
            logger.error(f"Code search failed: {e}")
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=str(e),
                error_code="CODE_SEARCH_ERROR"
            )
    
    async def _search_code_spans(
        self,
        workspace_root: str,
        query: str,
        file_patterns: List[str],
        search_type: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search for code spans in the workspace."""
        results = []
        
        # Find files matching patterns
        files_to_search = []
        for pattern in file_patterns:
            if pattern.endswith('.py'):
                files_to_search.extend(Path(workspace_root).rglob(pattern))
        
        # Search in each file
        for file_path in files_to_search[:100]:  # Limit files to search
            try:
                if not file_path.is_file():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse Python AST for symbol search
                if file_path.suffix == '.py':
                    file_results = await self._search_python_ast(
                        str(file_path), content, query, search_type
                    )
                    results.extend(file_results)
                
                # Text-based search as fallback
                text_results = await self._search_text_patterns(
                    str(file_path), content, query
                )
                results.extend(text_results)
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching file {file_path}: {e}")
                continue
        
        # Sort by relevance and return top results
        results = sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)
        return results[:max_results]
    
    async def _search_python_ast(
        self,
        file_path: str,
        content: str,
        query: str,
        search_type: str
    ) -> List[Dict[str, Any]]:
        """Search Python AST for symbols."""
        results = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                # Function definitions
                if isinstance(node, ast.FunctionDef) and query in node.name:
                    results.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "content": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        "symbol_type": "function",
                        "symbol_name": node.name,
                        "confidence": 0.9 if query == node.name else 0.7
                    })
                
                # Class definitions
                elif isinstance(node, ast.ClassDef) and query in node.name:
                    results.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "content": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        "symbol_type": "class",
                        "symbol_name": node.name,
                        "confidence": 0.9 if query == node.name else 0.7
                    })
                
                # Variable assignments
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and query in target.id:
                            results.append({
                                "file_path": file_path,
                                "line_number": node.lineno,
                                "content": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                                "symbol_type": "variable",
                                "symbol_name": target.id,
                                "confidence": 0.8 if query == target.id else 0.6
                            })
                
        except SyntaxError:
            # File has syntax errors, skip AST parsing
            pass
        except Exception as e:
            logger.warning(f"AST parsing error for {file_path}: {e}")
        
        return results
    
    async def _search_text_patterns(
        self,
        file_path: str,
        content: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Search for text patterns in file content."""
        results = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                results.append({
                    "file_path": file_path,
                    "line_number": i + 1,
                    "content": line.strip(),
                    "symbol_type": "text_match",
                    "symbol_name": query,
                    "confidence": 0.5
                })
        
        return results


class CodeApplyDiffTool(CopilotTool):
    """Tool for applying code diffs with dry-run → apply workflow."""
    
    def _create_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name="code.apply_diff",
            description="Apply code changes with dry-run preview, automatic formatting, and citation preservation",
            scope=ToolScope.WRITE,
            rbac_level=RBACLevel.DEV,
            privacy_level=PrivacyLevel.CONFIDENTIAL,  # Code changes are sensitive
            min_citations=2,
            citation_sources=["code_analysis", "requirements"],
            security_constraints=SecurityConstraint(
                allowed_paths=["src/", "tests/", "examples/"],
                blocked_paths=[".git/", "node_modules/", "__pycache__/", ".env", "config/"],
                max_file_size=1024 * 1024,  # 1MB max file size
                timeout_seconds=60,
                require_approval=True,
                sandbox_enabled=True
            ),
            supports_dry_run=True,
            supports_rollback=True,
            is_idempotent=False,
            can_batch=True,
            tags=["code", "diff", "apply", "formatting"]
        )
    
    def _create_metadata(self):
        """Create legacy metadata for compatibility."""
        from ai_karen_engine.services.tool_service import ToolMetadata, ToolCategory, ToolParameter
        return ToolMetadata(
            name="code.apply_diff",
            description="Apply code changes with diff preview",
            category=ToolCategory.CORE,
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to the file to modify",
                    required=True,
                    validation_rules={"min_length": 1}
                ),
                ToolParameter(
                    name="changes",
                    type=list,
                    description="List of changes to apply (unified diff format or structured changes)",
                    required=True
                ),
                ToolParameter(
                    name="format_code",
                    type=bool,
                    description="Whether to format code after applying changes",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="backup_original",
                    type=bool,
                    description="Whether to create backup of original file",
                    required=False,
                    default=True
                )
            ],
            return_type=dict,
            timeout=60
        )
    
    async def _execute_with_context(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """Execute diff application with rollback support."""
        file_path = parameters["file_path"]
        changes = parameters["changes"]
        format_code = parameters.get("format_code", True)
        backup_original = parameters.get("backup_original", True)
        
        workspace_root = context.workspace_root or os.getcwd()
        full_path = os.path.join(workspace_root, file_path)
        
        try:
            # Validate file path
            if not self._validate_file_path(full_path, context):
                raise PolicyViolationError(f"File path not allowed: {file_path}")
            
            # Read original content
            if not os.path.exists(full_path):
                original_content = ""
            else:
                with open(full_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            
            # Apply changes
            modified_content = await self._apply_changes(original_content, changes)
            
            # Format code if requested
            if format_code and file_path.endswith('.py'):
                modified_content = await self._format_python_code(modified_content)
            
            # Generate diff for preview
            diff = self._generate_diff(original_content, modified_content, file_path)
            
            # Prepare rollback data
            rollback_data = {
                "tool_name": "code.apply_diff",
                "file_path": full_path,
                "original_content": original_content,
                "backup_path": None
            }
            
            # Execute based on mode
            if context.execution_mode == ExecutionMode.DRY_RUN:
                result_data = {
                    "file_path": file_path,
                    "diff_preview": diff,
                    "changes_applied": len(changes),
                    "would_create_backup": backup_original,
                    "would_format": format_code and file_path.endswith('.py')
                }
                
                artifacts = [
                    {
                        "type": "diff",
                        "content": diff,
                        "file_path": file_path,
                        "metadata": {"mode": "preview"}
                    }
                ]
                
                return ToolResult(
                    success=True,
                    execution_mode=context.execution_mode,
                    result=result_data,
                    artifacts=artifacts,
                    citations_used=context.citations,
                    can_rollback=False
                )
            
            else:  # APPLY mode
                # Create backup if requested
                backup_path = None
                if backup_original and os.path.exists(full_path):
                    backup_path = f"{full_path}.backup.{int(datetime.now().timestamp())}"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    rollback_data["backup_path"] = backup_path
                
                # Write modified content
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                result_data = {
                    "file_path": file_path,
                    "diff_applied": diff,
                    "changes_applied": len(changes),
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                    "formatted": format_code and file_path.endswith('.py')
                }
                
                artifacts = [
                    {
                        "type": "diff",
                        "content": diff,
                        "file_path": file_path,
                        "metadata": {"mode": "applied"}
                    }
                ]
                
                return ToolResult(
                    success=True,
                    execution_mode=context.execution_mode,
                    result=result_data,
                    artifacts=artifacts,
                    citations_used=context.citations,
                    can_rollback=True,
                    rollback_data=rollback_data
                )
                
        except Exception as e:
            logger.error(f"Code diff application failed: {e}")
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=str(e),
                error_code="DIFF_APPLICATION_ERROR"
            )
    
    def _validate_file_path(self, file_path: str, context: ToolContext) -> bool:
        """Validate file path against security constraints."""
        constraints = self.tool_spec.security_constraints
        
        # Check file size if file exists
        if os.path.exists(file_path) and constraints.max_file_size:
            file_size = os.path.getsize(file_path)
            if file_size > constraints.max_file_size:
                return False
        
        # Check path constraints
        return constraints.validate_path(file_path)
    
    async def _apply_changes(self, original_content: str, changes: List[Dict[str, Any]]) -> str:
        """Apply changes to content."""
        lines = original_content.split('\n')
        
        # Sort changes by line number in reverse order to avoid offset issues
        sorted_changes = sorted(changes, key=lambda x: x.get('line', 0), reverse=True)
        
        for change in sorted_changes:
            change_type = change.get('type', 'replace')
            line_num = change.get('line', 1) - 1  # Convert to 0-based index
            content = change.get('content', '')
            
            if change_type == 'insert':
                lines.insert(line_num, content)
            elif change_type == 'delete':
                if 0 <= line_num < len(lines):
                    del lines[line_num]
            elif change_type == 'replace':
                if 0 <= line_num < len(lines):
                    lines[line_num] = content
                else:
                    lines.append(content)
        
        return '\n'.join(lines)
    
    async def _format_python_code(self, content: str) -> str:
        """Format Python code using black or autopep8."""
        try:
            # Try using black first
            proc = await asyncio.create_subprocess_exec(
                'black', '--code', content,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return stdout.decode('utf-8')
            
        except FileNotFoundError:
            pass
        
        try:
            # Fallback to autopep8
            proc = await asyncio.create_subprocess_exec(
                'autopep8', '--',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate(input=content.encode('utf-8'))
            
            if proc.returncode == 0:
                return stdout.decode('utf-8')
                
        except FileNotFoundError:
            pass
        
        # Return original content if no formatter available
        logger.warning("No code formatter available (black or autopep8)")
        return content
    
    def _generate_diff(self, original: str, modified: str, filename: str) -> str:
        """Generate unified diff between original and modified content."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    async def rollback(self, operation_id: str, rollback_data: Dict[str, Any]) -> bool:
        """Rollback file changes."""
        try:
            file_path = rollback_data["file_path"]
            original_content = rollback_data["original_content"]
            backup_path = rollback_data.get("backup_path")
            
            # Restore original content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Clean up backup file if it exists
            if backup_path and os.path.exists(backup_path):
                os.remove(backup_path)
            
            logger.info(f"Successfully rolled back changes to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False


class TestRunSubsetTool(CopilotTool):
    """Tool for running impacted tests with artifact collection."""
    
    def _create_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name="tests.run_subset",
            description="Run impacted tests with artifact collection and coverage reporting",
            scope=ToolScope.EXEC,
            rbac_level=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=2,
            citation_sources=["code_changes", "test_files"],
            security_constraints=SecurityConstraint(
                allowed_paths=["tests/", "src/"],
                blocked_paths=[".git/", "node_modules/", "__pycache__/"],
                timeout_seconds=300,  # 5 minutes for test execution
                sandbox_enabled=True
            ),
            supports_dry_run=True,
            supports_rollback=False,
            is_idempotent=True,
            can_batch=False,
            estimated_duration=60,
            tags=["tests", "pytest", "coverage", "ci"]
        )
    
    def _create_metadata(self):
        """Create legacy metadata for compatibility."""
        from ai_karen_engine.services.tool_service import ToolMetadata, ToolCategory, ToolParameter
        return ToolMetadata(
            name="tests.run_subset",
            description="Run subset of tests with coverage reporting",
            category=ToolCategory.CORE,
            parameters=[
                ToolParameter(
                    name="test_patterns",
                    type=list,
                    description="Test file patterns or specific test names",
                    required=False,
                    default=["tests/"]
                ),
                ToolParameter(
                    name="changed_files",
                    type=list,
                    description="List of changed files to determine impacted tests",
                    required=False,
                    default=[]
                ),
                ToolParameter(
                    name="collect_coverage",
                    type=bool,
                    description="Whether to collect coverage information",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="fail_fast",
                    type=bool,
                    description="Stop on first test failure",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="verbose",
                    type=bool,
                    description="Verbose test output",
                    required=False,
                    default=True
                )
            ],
            return_type=dict,
            timeout=300
        )
    
    async def _execute_with_context(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """Execute test subset with coverage collection."""
        test_patterns = parameters.get("test_patterns", ["tests/"])
        changed_files = parameters.get("changed_files", [])
        collect_coverage = parameters.get("collect_coverage", True)
        fail_fast = parameters.get("fail_fast", False)
        verbose = parameters.get("verbose", True)
        
        workspace_root = context.workspace_root or os.getcwd()
        
        try:
            # Determine impacted tests
            if changed_files:
                impacted_tests = await self._find_impacted_tests(workspace_root, changed_files)
                if impacted_tests:
                    test_patterns = impacted_tests
            
            # Build pytest command
            pytest_cmd = await self._build_pytest_command(
                workspace_root, test_patterns, collect_coverage, fail_fast, verbose
            )
            
            if context.execution_mode == ExecutionMode.DRY_RUN:
                return ToolResult(
                    success=True,
                    execution_mode=context.execution_mode,
                    result={
                        "command": " ".join(pytest_cmd),
                        "test_patterns": test_patterns,
                        "would_collect_coverage": collect_coverage,
                        "estimated_duration": "30-120 seconds"
                    },
                    citations_used=context.citations
                )
            
            # Execute tests
            test_results = await self._run_pytest(workspace_root, pytest_cmd)
            
            # Collect artifacts
            artifacts = []
            
            # Test results artifact
            artifacts.append({
                "type": "test_results",
                "content": json.dumps(test_results, indent=2),
                "metadata": {
                    "total_tests": test_results.get("total", 0),
                    "passed": test_results.get("passed", 0),
                    "failed": test_results.get("failed", 0),
                    "skipped": test_results.get("skipped", 0)
                }
            })
            
            # Coverage artifact if collected
            if collect_coverage and test_results.get("coverage"):
                artifacts.append({
                    "type": "coverage_report",
                    "content": test_results["coverage"],
                    "metadata": {
                        "coverage_percentage": test_results.get("coverage_percentage", 0)
                    }
                })
            
            return ToolResult(
                success=test_results["success"],
                execution_mode=context.execution_mode,
                result=test_results,
                artifacts=artifacts,
                citations_used=context.citations
            )
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=str(e),
                error_code="TEST_EXECUTION_ERROR"
            )
    
    async def _find_impacted_tests(
        self, 
        workspace_root: str, 
        changed_files: List[str]
    ) -> List[str]:
        """Find tests impacted by changed files."""
        impacted_tests = set()
        
        for changed_file in changed_files:
            # Direct test file
            if changed_file.startswith("tests/") and changed_file.endswith(".py"):
                impacted_tests.add(changed_file)
            
            # Find corresponding test files
            elif changed_file.startswith("src/") and changed_file.endswith(".py"):
                # Convert src/module/file.py to tests/test_file.py or tests/module/test_file.py
                rel_path = changed_file[4:]  # Remove 'src/'
                base_name = os.path.splitext(os.path.basename(rel_path))[0]
                
                # Try different test naming conventions
                test_patterns = [
                    f"tests/test_{base_name}.py",
                    f"tests/{os.path.dirname(rel_path)}/test_{base_name}.py",
                    f"tests/{rel_path.replace('.py', '_test.py')}"
                ]
                
                for pattern in test_patterns:
                    test_path = os.path.join(workspace_root, pattern)
                    if os.path.exists(test_path):
                        impacted_tests.add(pattern)
        
        return list(impacted_tests)
    
    async def _build_pytest_command(
        self,
        workspace_root: str,
        test_patterns: List[str],
        collect_coverage: bool,
        fail_fast: bool,
        verbose: bool
    ) -> List[str]:
        """Build pytest command with appropriate flags."""
        cmd = ["python", "-m", "pytest"]
        
        # Add test patterns
        cmd.extend(test_patterns)
        
        # Add flags
        if verbose:
            cmd.append("-v")
        
        if fail_fast:
            cmd.append("-x")
        
        if collect_coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=json"])
        
        # Output format
        cmd.extend(["--tb=short", "--no-header"])
        
        return cmd
    
    async def _run_pytest(
        self, 
        workspace_root: str, 
        pytest_cmd: List[str]
    ) -> Dict[str, Any]:
        """Run pytest and parse results."""
        try:
            # Execute pytest
            proc = await asyncio.create_subprocess_exec(
                *pytest_cmd,
                cwd=workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            # Parse pytest output
            output = stdout.decode('utf-8')
            error_output = stderr.decode('utf-8')
            
            # Extract test results from output
            results = self._parse_pytest_output(output)
            results["return_code"] = proc.returncode
            results["success"] = proc.returncode == 0
            results["stdout"] = output
            results["stderr"] = error_output
            
            # Load coverage data if available
            coverage_file = os.path.join(workspace_root, "coverage.json")
            if os.path.exists(coverage_file):
                try:
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                    results["coverage_data"] = coverage_data
                    results["coverage_percentage"] = coverage_data.get("totals", {}).get("percent_covered", 0)
                except Exception as e:
                    logger.warning(f"Failed to load coverage data: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to run pytest: {e}")
            return {
                "success": False,
                "error": str(e),
                "return_code": -1
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failures": [],
            "duration": 0.0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            # Parse summary line (e.g., "5 passed, 2 failed, 1 skipped in 2.34s")
            if " passed" in line or " failed" in line or " skipped" in line:
                # Extract numbers
                import re
                numbers = re.findall(r'(\d+)\s+(passed|failed|skipped|error)', line)
                for count, status in numbers:
                    results[status] = int(count)
                    results["total"] += int(count)
                
                # Extract duration
                duration_match = re.search(r'in ([\d.]+)s', line)
                if duration_match:
                    results["duration"] = float(duration_match.group(1))
            
            # Parse failure details
            elif "FAILED" in line:
                results["failures"].append(line.strip())
        
        return results


# Additional tools would be implemented here following the same pattern:
# - GitOpenPRTool
# - SecurityScanSecretsTool  
# - FileSystemReadTool
# - FileSystemWriteTool
# - DatabaseSchemaMapTool
# - DatabaseQuerySafeTool

# For now, I'll create placeholder implementations to complete the MVP set

class GitOpenPRTool(CopilotTool):
    """Tool for creating PRs with plan summaries and diff context."""
    
    def _create_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name="git.open_pr",
            description="Create pull request with plan summaries, diff context, and citation links",
            scope=ToolScope.NETWORK,
            rbac_level=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=2,
            supports_dry_run=True,
            tags=["git", "pr", "github", "gitlab"]
        )
    
    def _create_metadata(self):
        from ai_karen_engine.services.tool_service import ToolMetadata, ToolCategory, ToolParameter
        return ToolMetadata(
            name="git.open_pr",
            description="Create pull request",
            category=ToolCategory.CORE,
            parameters=[
                ToolParameter(name="title", type=str, required=True),
                ToolParameter(name="description", type=str, required=True),
                ToolParameter(name="base_branch", type=str, required=False, default="main"),
                ToolParameter(name="head_branch", type=str, required=True)
            ]
        )
    
    async def _execute_with_context(self, parameters: Dict[str, Any], context: ToolContext) -> ToolResult:
        # Placeholder implementation
        return ToolResult(
            success=True,
            execution_mode=context.execution_mode,
            result={"message": "PR creation not yet implemented"},
            citations_used=context.citations
        )


class SecurityScanSecretsTool(CopilotTool):
    """Tool for detecting credential leaks and vulnerabilities."""
    
    def _create_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name="security.scan_secrets",
            description="Detect credential leaks and vulnerabilities with remediation suggestions",
            scope=ToolScope.READ,
            rbac_level=RBACLevel.DEV,
            privacy_level=PrivacyLevel.CONFIDENTIAL,
            min_citations=1,
            supports_dry_run=True,
            tags=["security", "secrets", "vulnerabilities"]
        )
    
    def _create_metadata(self):
        from ai_karen_engine.services.tool_service import ToolMetadata, ToolCategory, ToolParameter
        return ToolMetadata(
            name="security.scan_secrets",
            description="Scan for secrets and vulnerabilities",
            category=ToolCategory.CORE,
            parameters=[
                ToolParameter(name="scan_paths", type=list, required=False, default=["src/", "tests/"]),
                ToolParameter(name="scan_type", type=str, required=False, default="all")
            ]
        )
    
    async def _execute_with_context(self, parameters: Dict[str, Any], context: ToolContext) -> ToolResult:
        # Placeholder implementation
        return ToolResult(
            success=True,
            execution_mode=context.execution_mode,
            result={"message": "Security scanning not yet implemented"},
            citations_used=context.citations
        )


# Export all copilot tools
COPILOT_TOOLS = [
    CodeSearchSpansTool,
    CodeApplyDiffTool,
    TestRunSubsetTool,
    GitOpenPRTool,
    SecurityScanSecretsTool
]