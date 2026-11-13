"""Catch actual directory archive limits before recommending an upload."""
import importlib.util
import os
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('plugin_archive_limits',Path(__file__).resolve().parents[2]/'scripts/plugin_archive_limits.py')
limits=importlib.util.module_from_spec(spec);spec.loader.exec_module(limits)

def test_entry_count_and_member_size_are_bounded():
    assert any('entries exceeds' in error for error in limits.check_inventory([(f'f{i}',1) for i in range(5001)]))
    assert any('Member exceeds' in error for error in limits.check_inventory([('large.bin',101*limits.MIB)]))

def test_extracted_limit_is_independent_of_individual_member_limits():
    errors=limits.check_inventory([(f'f{i}',90*limits.MIB) for i in range(6)])
    assert any('extracted bytes exceeds' in error for error in errors)
    assert not any('Member exceeds' in error for error in errors)

def test_unsafe_and_colliding_names_are_refused():
    errors=limits.check_inventory([('../private',1),('mcp.json',1),('MCP.JSON',1)])
    assert any('Unsafe' in error for error in errors) and any('collision' in error for error in errors)

def test_portable_launcher_matches_host_command_restrictions():
    assert not limits.check_stdio_command('./bin/uv.exe')
    assert not limits.check_stdio_command('uvx')
    for command in ('C:/Users/User/uv.exe','${PLUGIN_ROOT}/bin/uv.exe','./../uv.exe','./bin\\uv.exe'):
        assert limits.check_stdio_command(command)

def test_actual_connector_archive_obeys_all_limits():
    path=os.environ.get('INTACT_TEST_CONNECTOR_ZIP')
    if not path:pytest.skip('Set INTACT_TEST_CONNECTOR_ZIP to inspect a built connector')
    result=limits.validate_archive(path)
    assert result['compressed_bytes']<=100*limits.MIB
    assert result['extracted_bytes']<=512*limits.MIB and result['entries']<=5000

def test_actual_offline_runtime_is_rejected_as_an_upload():
    path=os.environ.get('INTACT_TEST_OFFLINE_ZIP')
    if not path:pytest.skip('Set INTACT_TEST_OFFLINE_ZIP to inspect an offline engine')
    with pytest.raises(ValueError,match='compressed bytes exceeds'):limits.validate_archive(path)
