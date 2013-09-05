from fabric.api import local, env, run, cd

env.hosts = ['gitspatial@gitspatial.com']


def deploy(environment='production'):
    app_dir = '~/apps/gitspatial'
    activate_venv = 'source venv/bin/activate && source .env && '
    run_tests = 'python manage.py test gitspatial api user geojson'

    local(run_tests)

    with cd(app_dir):
        run('git fetch')
        run('git reset --hard origin/master')
        run(activate_venv + run_tests)
        run('sudo supervisorctl restart gitspatial_web')
        run('sudo supervisorctl restart gitspatial_celery')
