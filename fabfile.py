from fabric.api import run, env, cd
from fabric.contrib.files import append
from carreros.local_settings import HOST_IP, HOST_USER

env.hosts = [HOST_IP]
env.user = HOST_USER

def shell_plus():
    run("source /virtualenvs/carreros/bin/activate")
    with cd('/projects/carreros'):
        run("/virtualenvs/carreros/bin/python manage.py shell_plus")


def append_to_local_settings(path):
    run("source /virtualenvs/carreros/bin/activate")
    with open(path) as ls:
        content = ls.read()
    with cd('/projects/carreros'):
        append('./carreros/local_settings.py', f'\n{content}')


def loaddata(fixture):
    run("source /virtualenvs/carreros/bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run("/virtualenvs/carreros/bin/python manage.py loaddata fixtures/{}".format(fixture))


def deploy():
    run("source /virtualenvs/carreros/bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run("/virtualenvs/carreros/bin/pip install -r requirements.txt")
        run("/virtualenvs/carreros/bin/python manage.py migrate")
        run("/virtualenvs/carreros/bin/python manage.py collectstatic --noinput")
        run("supervisorctl restart carreros")