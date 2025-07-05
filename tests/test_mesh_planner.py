import asyncio
from ..src.core.mesh_planner import MeshPlanner


def test_load_and_route(tmp_path, monkeypatch):
    from pathlib import Path
    import shutil
    src = Path('capsules/devops')
    dest = tmp_path / 'devops'
    shutil.copytree(src, dest)

    planner = MeshPlanner(capsule_dir=tmp_path)
    assert 'devops' in planner.list_capsules()
    result = planner.route_intent('deploy_request', 'deploy', {'branch': 'dev'})
    assert result['capsule'] == 'devops'
    assert result['result']['branch'] == 'dev'


def test_devops_capsule_invokes_plugins(monkeypatch):
    calls = []
    monkeypatch.setattr(
        'capsules.devops.handler.router.dispatch',
        lambda intent, params, roles=None: calls.append(intent) or asyncio.sleep(0),
    )
    planner = MeshPlanner()
    result = planner.route_intent(
        'deploy_request',
        'deploy',
        {'branch': 'main', 'deployment': 'web', 'replicas': 2},
    )
    assert result['result']['deployment'] == 'web'
    assert 'git_merge_safe' in calls and 'k8s_scale' in calls
