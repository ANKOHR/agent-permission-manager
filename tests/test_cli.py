import json
import time
from agent_permission_manager.cli import main

def test_run_completes_on_fixture(tmp_path,capsys):
    start=time.perf_counter()
    assert main(["fixtures","--out",str(tmp_path/"demo")]) == 0
    result=tmp_path/"result.json"
    assert main(["run","--input",str(tmp_path/"demo"),"--output",str(result)]) == 0
    assert main(["report","--results",str(result),"--format","md"]) == 0
    assert time.perf_counter()-start < 5

def test_empty_input_renders_without_traceback(tmp_path,capsys):
    result=tmp_path/"result.json"
    assert main(["run","--input",str(tmp_path),"--output",str(result)]) == 0
    assert main(["report","--results",str(result)]) == 0
    assert json.loads(result.read_text())["totals"]["records"] == 0

def test_malformed_input_named_error(tmp_path,capsys):
    path=tmp_path/"records.jsonl"; path.write_text('{}\n{bad')
    # First row must be valid so parsing reaches the second line.
    from agent_permission_manager.fixtures import records
    path.write_text(json.dumps(records(1)[0])+'\n{bad')
    assert main(["run","--input",str(tmp_path)]) == 2
    err=capsys.readouterr().err
    assert "ParseError" in err and "records.jsonl:2" in err
    assert "Traceback" not in err

def test_cli_smoke_all_subcommands(tmp_path,capsys):
    assert main(["fixtures","--out",str(tmp_path)]) == 0
    assert main(["policy"]) == 0
    assert main(["check","--input",str(tmp_path),"--id","case-001"]) == 0
    for cmd in ("fixtures","run","report","policy","check"):
        import pytest
        with pytest.raises(SystemExit) as ex: main([cmd,"--help"])
        assert ex.value.code == 0

def test_missing_input(tmp_path,capsys):
    assert main(["run","--input",str(tmp_path/"missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err

def test_report_write_failure_no_partial(tmp_path,capsys):
    result=tmp_path/"result.json"
    main(["run","--input",str(tmp_path),"--output",str(result)])
    before=set(tmp_path.iterdir())
    assert main(["report","--results",str(result),"--out",str(tmp_path/"missing"/"out.md")]) == 2
    assert set(tmp_path.iterdir()) == before

def test_cli_determinism(tmp_path):
    main(["fixtures","--out",str(tmp_path/"demo")])
    result=tmp_path/"result.json"
    args=["run","--input",str(tmp_path/"demo"),"--output",str(result)]
    main(args); first=result.read_bytes(); main(args)
    assert result.read_bytes() == first
