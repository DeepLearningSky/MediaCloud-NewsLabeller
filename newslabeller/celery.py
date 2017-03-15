from __future__ import absolute_import
from celery import Celery

from newslabeller import settings

app = Celery('mediacloud',
             broker=settings.get('queue','broker_url'),
             backend=settings.get('queue','backend_url'),
             include=['newslabeller.tasks'])

# expire backend results in one hour
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
