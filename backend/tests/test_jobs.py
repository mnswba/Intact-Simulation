import asyncio
from intact_backend.jobs import Jobs

async def test_job_cancellation_propagates_and_preserves_status(tmp_path):
    jobs=Jobs(tmp_path/'jobs.sqlite3');started=asyncio.Event();captured={}
    async def run(progress,cancel):
        captured['cancel']=cancel;progress({'tool':'build_geometry'});started.set()
        await asyncio.Event().wait()
    job=jobs.create(run);await started.wait()
    task=jobs.tasks[job['id']]
    assert jobs.get(job['id'])['progress'][0]['tool']=='build_geometry'
    jobs.cancel(job['id']);await task
    assert captured['cancel'].is_set()
    assert jobs.get(job['id'])['status']=='cancelled'

async def test_finished_result_survives_restart_and_interrupted_job_is_marked_failed(tmp_path):
    path=tmp_path/'jobs.sqlite3';jobs=Jobs(path)
    async def run(progress,cancel):return {'message':'validated'}
    job=jobs.create(run);await jobs.tasks[job['id']]
    assert jobs.get(job['id'])['status']=='succeeded'
    jobs.save('interrupted','running',{'progress':[]})
    restarted=Jobs(path)
    assert restarted.get(job['id'])['result']['message']=='validated'
    assert restarted.get('interrupted')['status']=='failed'
