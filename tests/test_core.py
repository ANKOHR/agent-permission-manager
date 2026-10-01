import copy
import pytest
from agent_permission_manager.core import evaluate, run, SchemaError
from agent_permission_manager.fixtures import records

@pytest.mark.parametrize("index,score,tier,grants", [(0,0,"low",4),(1,25,"moderate",2),(2,55,"high",1),(3,95,"critical",0)])
def test_policy(index,score,tier,grants):
    d=evaluate(records(4)[index])
    assert (d["score"],d["tier"],len(d["granted"])) == (score,tier,grants)

@pytest.mark.parametrize("field,value", [("amount",-1),("observed_on","2027-01-01"),("id","x"*257),("requested",["root"]),("synthetic",1),("signals",{})])
def test_rejects_adversarial_values(field,value):
    r=records(1)[0]; r[field]=value
    with pytest.raises(SchemaError): evaluate(r)

def test_duplicates():
    with pytest.raises(SchemaError,match="duplicate"): run(records(1)*2)

def test_handles_unicode_and_long_inputs():
    r=records(1)[0]; r["id"]="用户"; r["description"]="C:\\Users\\亨利 " + "é"*9000
    assert evaluate(r)["id"] == "用户"

def test_corrupted_fixture_changes_computation():
    rs=records(); before=run(rs)
    rs[0]["signals"]={s:True for s in rs[0]["signals"]}
    assert run(rs)["totals"]["restricted_records"] == before["totals"]["restricted_records"]+1

def test_only_requested_permissions_granted():
    r=records(1)[0]; r["requested"]=[]
    assert evaluate(r)["granted"] == []
