import pytest
import sys
import types
from ai_karen_engine.mcp.registry import ServiceRegistry
from ai_karen_engine.mcp.base import MCP_CALLS_TOTAL, MCP_AUTH_FAILURES, AuthorizationError


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, k, v):
        self.store[k] = v

    def get(self, k):
        return self.store.get(k)

    def delete(self, k):
        self.store.pop(k, None)

    def keys(self, pattern):
        prefix = pattern.rstrip('*')
        return [k for k in self.store if k.startswith(prefix)]


def test_registry():
    r = FakeRedis()
    reg = ServiceRegistry(redis_client=r)
    reg.register('svc', 'http://x', 'jsonrpc', roles=['user'])
    assert reg.lookup('svc')['endpoint'] == 'http://x'
    assert 'svc' in reg.list()
    reg.deregister('svc')
    assert reg.lookup('svc') is None


def test_jsonrpc_client_auth(monkeypatch):
    r = FakeRedis()
    reg = ServiceRegistry(redis_client=r)
    reg.register('svc', 'http://test', 'jsonrpc', roles=['user'])
    calls = {}

    fake_httpx = types.ModuleType('httpx')
    def fake_post(url, json=None, timeout=10):
        calls['called'] = True
        return types.SimpleNamespace(status_code=200, json=lambda: {'result': 1}, raise_for_status=lambda: None)
    fake_httpx.post = fake_post
    monkeypatch.setitem(sys.modules, 'httpx', fake_httpx)

    import importlib
    JSONRPCClient = importlib.reload(importlib.import_module('ai_karen_engine.mcp.json_rpc_client')).JSONRPCClient
    client = JSONRPCClient(reg, token='secret', role='user')

    result = client.call('svc', 'sum', {'a': 1}, token='secret')
    assert result == 1
    assert MCP_CALLS_TOTAL.labels(service='svc', success='true')

    with pytest.raises(AuthorizationError):
        client.call('svc', 'sum', {}, token='bad')
    assert MCP_AUTH_FAILURES.labels(service='svc')

