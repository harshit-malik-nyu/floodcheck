import json
from floodcheck.cli import main

def test_signals_json_is_a_single_parseable_document(capsys):
 assert main(['--json','signals','--size','20','--seeds','1'])==0
 rows=json.loads(capsys.readouterr().out)
 assert len(rows)==3

def test_cost_and_ceiling_cli(capsys):
 for command in [['--json','cost'],['--json','ceiling'],['cost'],['ceiling']]:
  assert main(command)==0
  out=capsys.readouterr().out
  if command[0]=='--json':assert json.loads(out)
  else:assert out.strip()

def test_impossible_and_invalid_budgets_are_explicit(capsys):
 import pytest
 with pytest.raises(SystemExit):main(['ceiling','--hours','0'])
 assert main(['ceiling','--hours','0.00001'])==0
 assert 'no campaign meets' in capsys.readouterr().out
