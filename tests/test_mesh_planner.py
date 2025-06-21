from core.mesh_planner import MeshPlanner


def test_load_and_route(tmp_path, monkeypatch):
    # copy devops capsule into tmp directory
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
