"""Recency metadata does not mutate geometry or lose saved/draft models."""
import os
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
SOURCE='import build123d as bd\ndef build(params):\n    return {"body":bd.Box(10,8,4)}'
def test_saved_and_draft_models_expose_actual_save_time(tmp_path):
 s=ProjectService(tmp_path);r=s.build(SOURCE,{},name='Saved model');key=r['model_id'];os.utime(s.path(key),(1000,1000))
 draft=FeatureService(s).requirements(None,{'source_text':'New sketch draft'},name='Draft')
 listing={r['model_id']:r for r in s.list()}
 assert listing[key]['updated_at']==1000 and listing[key]['revision']==1
 assert listing[draft['model_id']]['draft'] and listing[draft['model_id']]['updated_at']>1000
 assert s.load(key)['spec']['revision']==1
