"""
Contract Testing for Unified API Routes - Phase 4.1.a
Ensures schema consistency across all endpoints and validates request/response contracts.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

# Import the unified schemas and routes
from src.ai_karen_engine.api_routes.unified_schemas import (
    ErrorHandler,
    ErrorResponse,
    ErrorType,
    FieldError,
    SuccessResponse,
    ValidationUtils,
)


# Mock the FastAPI app with our routes
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for testing"""
    from fastapi import FastAPI

    from src.ai_karen_engine.api_routes.copilot_routes import router as copilot_router
    from src.ai_karen_engine.api_routes.memory_routes import router as memory_router

    app = FastAPI()
    app.include_router(copilot_router, prefix="/copilot")
    app.include_router(memory_router, prefix="/memory")

    return app


@pytest.fixture
def client(mock_app):
    """Create test client"""
    return TestClient(mock_app)


class TestCopilotContracts:
    """Test copilot endpoint contracts"""

    def test_copilot_assist_valid_request(self, client):
        """Test valid copilot assist request schema"""
        valid_request = {
            "user_id": "test_user_123",
            "org_id": "test_org_456",
            "message": "Help me understand this code",
            "top_k": 5,
            "context": {"session_id": "test_session"},
        }

        # Mock the dependencies to avoid actual service calls
        with patch(
            "src.ai_karen_engine.api_routes.copilot_routes.check_rbac_scope",
            return_value=True,
        ), patch(
            "src.ai_karen_engine.api_routes.copilot_routes.get_memory_service",
            return_value=None,
        ), patch(
            "src.ai_karen_engine.api_routes.copilot_routes.get_llm_provider",
            return_value=None,
        ):
            response = client.post("/copilot/assist", json=valid_request)

            # Should succeed (200) or fail gracefully with proper error format
            assert response.status_code in [200, 500, 503]

            data = response.json()

            if response.status_code == 200:
                # Validate successful response schema
                required_fields = {
                    "answer",
                    "context",
                    "actions",
                    "timings",
                    "correlation_id",
                }
                assert required_fields <= set(data.keys())

                # Validate context structure
                assert isinstance(data["context"], list)
                for hit in data["context"]:
                    required_hit_fields = {
                        "id",
                        "text",
                        "score",
                        "tags",
                        "importance",
                        "decay_tier",
                        "created_at",
                        "user_id",
                    }
                    assert required_hit_fields <= set(hit.keys())
                    assert isinstance(hit["score"], (int, float))
                    assert 0.0 <= hit["score"] <= 1.0
                    assert 1 <= hit["importance"] <= 10
                    assert hit["decay_tier"] in ["short", "medium", "long", "pinned"]

                # Validate actions structure
                assert isinstance(data["actions"], list)
                for action in data["actions"]:
                    required_action_fields = {"type", "params", "confidence"}
                    assert required_action_fields <= set(action.keys())
                    assert action["type"] in [
                        "add_task",
                        "pin_memory",
                        "open_doc",
                        "export_note",
                    ]
                    assert 0.0 <= action["confidence"] <= 1.0

                # Validate timings
                assert "total_ms" in data["timings"]
                assert isinstance(data["timings"]["total_ms"], (int, float))
                assert data["timings"]["total_ms"] >= 0
            else:
                # Validate error response schema
                self._validate_error_response(data)

    def test_copilot_assist_invalid_request(self, client):
        """Test invalid copilot assist request validation"""
        invalid_requests = [
            # Missing required fields
            {},
            {"user_id": "test"},  # Missing message
            {"message": "test"},  # Missing user_id
            # Invalid field values
            {"user_id": "", "message": "test"},  # Empty user_id
            {"user_id": "test", "message": ""},  # Empty message
            {"user_id": "test", "message": "x" * 9000},  # Message too long
            {"user_id": "test", "message": "test", "top_k": 0},  # Invalid top_k
            {"user_id": "test", "message": "test", "top_k": 100},  # top_k too large
        ]

        for invalid_request in invalid_requests:
            response = client.post("/copilot/assist", json=invalid_request)
            assert response.status_code == 422

            data = response.json()
            self._validate_error_response(data)
            assert data["error"] == "validation_error"
            assert "field_errors" in data
            assert isinstance(data["field_errors"], list)

    def test_copilot_assist_oversized_input(self, client):
        """Test handling of oversized inputs"""
        oversized_request = {
            "user_id": "test_user",
            "message": "x" * 10000,  # Exceeds max_length
            "context": {
                f"key_{i}": f"value_{i}" * 100 for i in range(100)
            },  # Large context
        }

        response = client.post("/copilot/assist", json=oversized_request)
        assert response.status_code == 422

        data = response.json()
        self._validate_error_response(data)

    def test_copilot_assist_unknown_fields(self, client):
        """Test handling of unknown fields in request"""
        request_with_unknown_fields = {
            "user_id": "test_user",
            "message": "test message",
            "unknown_field": "should be ignored",
            "another_unknown": {"nested": "data"},
        }

        with patch(
            "src.ai_karen_engine.api_routes.copilot_routes.check_rbac_scope",
            return_value=True,
        ):
            response = client.post("/copilot/assist", json=request_with_unknown_fields)

            # Should either succeed or fail gracefully, but not due to unknown fields
            assert response.status_code in [200, 500, 503]

    def _validate_error_response(self, data: Dict[str, Any]):
        """Validate error response schema"""
        required_fields = {
            "error",
            "message",
            "correlation_id",
            "timestamp",
            "path",
            "status_code",
        }
        assert required_fields <= set(data.keys())

        # Validate error type
        valid_error_types = [e.value for e in ErrorType]
        assert data["error"] in valid_error_types

        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Validate status code
        assert isinstance(data["status_code"], int)
        assert 400 <= data["status_code"] < 600


class TestMemoryContracts:
    """Test memory endpoint contracts"""

    def test_memory_search_valid_request(self, client):
        """Test valid memory search request schema"""
        valid_request = {
            "user_id": "test_user_123",
            "org_id": "test_org_456",
            "query": "search for relevant memories",
            "top_k": 10,
        }

        with patch(
            "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
            return_value=True,
        ), patch(
            "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
            return_value=None,
        ):
            response = client.post("/memory/search", json=valid_request)

            assert response.status_code in [200, 500, 503]

            data = response.json()

            if response.status_code == 200:
                # Validate successful response schema
                required_fields = {
                    "hits",
                    "total_found",
                    "query_time_ms",
                    "correlation_id",
                }
                assert required_fields <= set(data.keys())

                # Validate hits structure
                assert isinstance(data["hits"], list)
                assert isinstance(data["total_found"], int)
                assert isinstance(data["query_time_ms"], (int, float))
                assert data["query_time_ms"] >= 0

                for hit in data["hits"]:
                    self._validate_context_hit(hit)
            else:
                self._validate_error_response(data)

    def test_memory_commit_valid_request(self, client):
        """Test valid memory commit request schema"""
        valid_request = {
            "user_id": "test_user_123",
            "org_id": "test_org_456",
            "text": "This is important information to remember",
            "tags": ["important", "work", "project"],
            "importance": 8,
            "decay": "long",
        }

        with patch(
            "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
            return_value=True,
        ), patch(
            "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
            return_value=None,
        ):
            response = client.post("/memory/commit", json=valid_request)

            assert response.status_code in [200, 500, 503]

            data = response.json()

            if response.status_code == 200:
                # Validate successful response schema
                required_fields = {"id", "success", "message", "correlation_id"}
                assert required_fields <= set(data.keys())

                assert isinstance(data["success"], bool)
                assert isinstance(data["message"], str)
                if data["success"]:
                    assert data["id"]  # Should have an ID if successful
            else:
                self._validate_error_response(data)

    def test_memory_update_valid_request(self, client):
        """Test valid memory update request schema"""
        memory_id = "test_memory_123"
        valid_request = {
            "text": "Updated memory content",
            "tags": ["updated", "modified"],
            "importance": 7,
            "decay": "medium",
        }

        with patch(
            "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
            return_value=True,
        ), patch(
            "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
            return_value=None,
        ):
            response = client.put(f"/memory/{memory_id}", json=valid_request)

            assert response.status_code in [200, 404, 500, 503]

            data = response.json()

            if response.status_code == 200:
                # Validate successful response schema
                required_fields = {"success", "message", "correlation_id"}
                assert required_fields <= set(data.keys())

                assert isinstance(data["success"], bool)
                assert isinstance(data["message"], str)
            else:
                self._validate_error_response(data)

    def test_memory_delete_valid_request(self, client):
        """Test valid memory delete request"""
        memory_id = "test_memory_123"

        with patch(
            "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
            return_value=True,
        ), patch(
            "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
            return_value=None,
        ):
            response = client.delete(f"/memory/{memory_id}")

            assert response.status_code in [200, 404, 500, 503]

            data = response.json()

            if response.status_code == 200:
                # Validate successful response schema
                required_fields = {"success", "message", "correlation_id"}
                assert required_fields <= set(data.keys())

                assert isinstance(data["success"], bool)
                assert isinstance(data["message"], str)
            else:
                self._validate_error_response(data)

    def test_memory_search_invalid_request(self, client):
        """Test invalid memory search request validation"""
        invalid_requests = [
            # Missing required fields
            {},
            {"user_id": "test"},  # Missing query
            {"query": "test"},  # Missing user_id
            # Invalid field values
            {"user_id": "", "query": "test"},  # Empty user_id
            {"user_id": "test", "query": ""},  # Empty query
            {"user_id": "test", "query": "x" * 5000},  # Query too long
            {"user_id": "test", "query": "test", "top_k": 0},  # Invalid top_k
            {"user_id": "test", "query": "test", "top_k": 100},  # top_k too large
        ]

        for invalid_request in invalid_requests:
            response = client.post("/memory/search", json=invalid_request)
            assert response.status_code == 422

            data = response.json()
            self._validate_error_response(data)
            assert data["error"] == "validation_error"

    def test_memory_commit_invalid_request(self, client):
        """Test invalid memory commit request validation"""
        invalid_requests = [
            # Missing required fields
            {},
            {"user_id": "test"},  # Missing text
            {"text": "test"},  # Missing user_id
            # Invalid field values
            {"user_id": "", "text": "test"},  # Empty user_id
            {"user_id": "test", "text": ""},  # Empty text
            {"user_id": "test", "text": "x" * 20000},  # Text too long
            {"user_id": "test", "text": "test", "importance": 0},  # Invalid importance
            {"user_id": "test", "text": "test", "importance": 11},  # Invalid importance
            {"user_id": "test", "text": "test", "decay": "invalid"},  # Invalid decay
        ]

        for invalid_request in invalid_requests:
            response = client.post("/memory/commit", json=invalid_request)
            assert response.status_code == 422

            data = response.json()
            self._validate_error_response(data)
            assert data["error"] == "validation_error"

    @pytest.mark.asyncio
    async def test_memory_commit_field_validations(self):
        """Ensure commit handler performs field-level validation"""
        test_cases = [
            ({"user_id": "test", "text": "   "}, "text"),
            (
                {"user_id": "test", "text": "valid text", "tags": ["good", "bad tag"]},
                "tags",
            ),
        ]

        from types import SimpleNamespace

        from src.ai_karen_engine.api_routes.memory_routes import (
            MemCommit,
            memory_commit,
        )
        from src.ai_karen_engine.fastapi_stub import Request

        for payload, field in test_cases:
            with patch(
                "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
                return_value=True,
            ), patch(
                "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
                return_value=None,
            ):
                req_model = MemCommit(**payload)
                http_req = Request()
                http_req.url = SimpleNamespace(path="/memory/commit")
                with pytest.raises(HTTPException) as exc:
                    await memory_commit(req_model, http_req)
                data = exc.value.detail
                field_errors = data.get("field_errors", [])
                names = [
                    fe.field if hasattr(fe, "field") else fe.get("field")
                    for fe in field_errors
                ]
                assert field in names

    @pytest.mark.asyncio
    async def test_memory_update_field_validations(self):
        """Ensure update handler performs field-level validation"""
        test_cases = [
            ({"text": "   "}, "text"),
            ({"tags": ["good", "bad tag"]}, "tags"),
        ]

        from types import SimpleNamespace

        from src.ai_karen_engine.api_routes.memory_routes import (
            MemUpdateRequest,
            memory_update,
        )
        from src.ai_karen_engine.fastapi_stub import Request

        for payload, field in test_cases:
            with patch(
                "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
                return_value=True,
            ), patch(
                "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
                return_value=None,
            ):
                req_model = MemUpdateRequest(**payload)
                http_req = Request()
                http_req.url = SimpleNamespace(path=f"/memory/mem1")
                with pytest.raises(HTTPException) as exc:
                    await memory_update("mem1", req_model, http_req)
                data = exc.value.detail
                field_errors = data.get("field_errors", [])
                names = [
                    fe.field if hasattr(fe, "field") else fe.get("field")
                    for fe in field_errors
                ]
                assert field in names

    def _validate_context_hit(self, hit: Dict[str, Any]):
        """Validate ContextHit schema"""
        required_fields = {
            "id",
            "text",
            "score",
            "tags",
            "importance",
            "decay_tier",
            "created_at",
            "user_id",
        }
        assert required_fields <= set(hit.keys())

        assert isinstance(hit["score"], (int, float))
        assert 0.0 <= hit["score"] <= 1.0
        assert isinstance(hit["tags"], list)
        assert isinstance(hit["importance"], int)
        assert 1 <= hit["importance"] <= 10
        assert hit["decay_tier"] in ["short", "medium", "long", "pinned"]

        # Validate timestamp format
        datetime.fromisoformat(hit["created_at"].replace("Z", "+00:00"))
        if "preview" in hit:
            assert isinstance(hit["preview"], str)

    def _validate_error_response(self, data: Dict[str, Any]):
        """Validate error response schema"""
        required_fields = {
            "error",
            "message",
            "correlation_id",
            "timestamp",
            "path",
            "status_code",
        }
        assert required_fields <= set(data.keys())

        # Validate error type
        valid_error_types = [e.value for e in ErrorType]
        assert data["error"] in valid_error_types

        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Validate status code
        assert isinstance(data["status_code"], int)
        assert 400 <= data["status_code"] < 600


class TestValidationUtils:
    """Test validation utility functions"""

    def test_validate_user_id(self):
        """Test user ID validation"""
        # Valid user IDs
        assert ValidationUtils.validate_user_id("user123") == "user123"
        assert ValidationUtils.validate_user_id("user_123") == "user_123"
        assert ValidationUtils.validate_user_id("user-123") == "user-123"
        assert ValidationUtils.validate_user_id("  user123  ") == "user123"

        # Invalid user IDs
        with pytest.raises(ValueError):
            ValidationUtils.validate_user_id("")
        with pytest.raises(ValueError):
            ValidationUtils.validate_user_id("   ")
        with pytest.raises(ValueError):
            ValidationUtils.validate_user_id("x" * 256)
        with pytest.raises(ValueError):
            ValidationUtils.validate_user_id("user@123")  # Invalid character

    def test_validate_text_content(self):
        """Test text content validation"""
        # Valid text
        assert ValidationUtils.validate_text_content("Hello world") == "Hello world"
        assert ValidationUtils.validate_text_content("  Hello world  ") == "Hello world"

        # Invalid text
        with pytest.raises(ValueError):
            ValidationUtils.validate_text_content("")
        with pytest.raises(ValueError):
            ValidationUtils.validate_text_content("   ")
        with pytest.raises(ValueError):
            ValidationUtils.validate_text_content("x" * 20000)

    def test_validate_tags(self):
        """Test tags validation"""
        # Valid tags
        assert ValidationUtils.validate_tags([]) == []
        assert ValidationUtils.validate_tags(["tag1", "tag2"]) == ["tag1", "tag2"]
        assert ValidationUtils.validate_tags(["TAG1", "tag1"]) == [
            "tag1"
        ]  # Deduplication and lowercase
        assert ValidationUtils.validate_tags(["  tag1  ", "tag2"]) == [
            "tag1",
            "tag2",
        ]  # Trimming

        # Invalid tags
        with pytest.raises(ValueError):
            ValidationUtils.validate_tags([123])  # Non-string
        with pytest.raises(ValueError):
            ValidationUtils.validate_tags(["x" * 51])  # Too long
        with pytest.raises(ValueError):
            ValidationUtils.validate_tags(["tag@1"])  # Invalid character
        with pytest.raises(ValueError):
            ValidationUtils.validate_tags(
                [f"tag{i}" for i in range(25)]
            )  # Too many tags

    def test_validate_importance(self):
        """Test importance validation"""
        # Valid importance
        for i in range(1, 11):
            assert ValidationUtils.validate_importance(i) == i

        # Invalid importance
        with pytest.raises(ValueError):
            ValidationUtils.validate_importance(0)
        with pytest.raises(ValueError):
            ValidationUtils.validate_importance(11)
        with pytest.raises(ValueError):
            ValidationUtils.validate_importance("5")  # Wrong type

    def test_validate_decay_tier(self):
        """Test decay tier validation"""
        # Valid decay tiers
        for tier in ["short", "medium", "long", "pinned"]:
            assert ValidationUtils.validate_decay_tier(tier) == tier

        # Invalid decay tier
        with pytest.raises(ValueError):
            ValidationUtils.validate_decay_tier("invalid")

    def test_validate_top_k(self):
        """Test top_k validation"""
        # Valid top_k
        assert ValidationUtils.validate_top_k(1) == 1
        assert ValidationUtils.validate_top_k(25) == 25
        assert ValidationUtils.validate_top_k(50) == 50

        # Invalid top_k
        with pytest.raises(ValueError):
            ValidationUtils.validate_top_k(0)
        with pytest.raises(ValueError):
            ValidationUtils.validate_top_k(51)
        with pytest.raises(ValueError):
            ValidationUtils.validate_top_k("10")  # Wrong type


class TestErrorHandler:
    """Test error handling utilities"""

    def test_create_error_response(self):
        """Test error response creation"""
        error_response = ErrorHandler.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            correlation_id="test-123",
            path="/test/path",
            status_code=422,
        )

        assert error_response.error == ErrorType.VALIDATION_ERROR
        assert error_response.message == "Test error"
        assert error_response.correlation_id == "test-123"
        assert error_response.path == "/test/path"
        assert error_response.status_code == 422
        assert isinstance(error_response.timestamp, datetime)

    def test_create_validation_error_response(self):
        """Test validation error response creation"""
        validation_errors = [
            {
                "loc": ["user_id"],
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ["importance"],
                "msg": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt",
                "input": 0,
            },
        ]

        error_response = ErrorHandler.create_validation_error_response(
            validation_errors=validation_errors,
            correlation_id="test-123",
            path="/test/path",
        )

        assert error_response.error == ErrorType.VALIDATION_ERROR
        assert error_response.status_code == 422
        assert len(error_response.field_errors) == 2

        # Check first field error
        field_error = error_response.field_errors[0]
        assert field_error.field == "user_id"
        assert field_error.message == "field required"
        assert field_error.code == "value_error.missing"

        # Check second field error
        field_error = error_response.field_errors[1]
        assert field_error.field == "importance"
        assert field_error.invalid_value == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
