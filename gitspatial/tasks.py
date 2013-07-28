import time

from celery import task


@task()
def wait(duration=30):
    print 'starting to wait'
    time.sleep(duration)
    print 'done waiting'
    return
