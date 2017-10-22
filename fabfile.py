from fabric.api import run, env, cd
from fabric.contrib.files import append
from carreros.local_settings import HOST_IP, HOST_USER, VENV

env.hosts = [HOST_IP]
env.user = HOST_USER


def manage(command):
    run(f"source {VENV}bin/activate")
    with cd('/projects/carreros'):
        run(f"{VENV}bin/python manage.py {command}")

def shell_plus():
    manage('shell_plus')

def dbbackup():
    manage('dbbackup -z')


def dbrestore():
    manage('dbrestore -z')


def append_to_local_settings(path):
    run(f"source {VENV}bin/activate")
    with open(path) as ls:
        content = ls.read()
    with cd('/projects/carreros'):
        append('./carreros/local_settings.py', f'\n{content}')


def rmpyc():
    with cd('/projects/carreros'):
        run("find . -type d -name \"__pycache__\" -exec rm -rf {} \;")


def loaddata(fixture):
    run(f"source {VENV}bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run("/virtualenvs/carreros/bin/python manage.py loaddata fixtures/{}".format(fixture))


def importar_actas():
    run(f"source {VENV}bin/activate")
    with cd('/projects/carreros'):
        run(f"{VENV}bin/python manage.py importar_actas --include-seen --only-images")



def deploy():
    run(f"source {VENV}bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run("supervisorctl restart carreros")


def full_deploy():
    run(f"source {VENV}bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run(f"{VENV}bin/pip install -r requirements.txt")
        run(f"{VENV}bin/python manage.py migrate")
        run(f"{VENV}bin/python manage.py collectstatic --noinput")
        run("supervisorctl restart carreros")