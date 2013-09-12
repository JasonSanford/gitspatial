from fabric.api import local, env, run, cd

env.hosts = ['gitspatial@gitspatial.com']
run_tests_command = 'python manage.py test gitspatial api user geojson'


def deploy(environment='production'):
    app_dir = '~/apps/gitspatial'
    activate_venv = 'source venv/bin/activate && source .env && '

    local(run_tests_command)

    with cd(app_dir):
        run('git fetch')
        run('git reset --hard origin/master')
        run(activate_venv + 'pip install -r requirements.txt')
        run(activate_venv + run_tests_command)
        run('sudo supervisorctl restart gitspatial_web')
        run('sudo supervisorctl restart gitspatial_celery')

def test():
    local(run_tests_command)