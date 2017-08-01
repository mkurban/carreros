from fabric.api import run, env, cd
from carreros.local_settings import HOST_IP, HOST_USER

env.hosts = [HOST_IP]
env.user = HOST_USER

def deploy():
    run("source /virtualenvs/carreros/bin/activate")
    with cd('/projects/carreros'):
        run("git pull")
        run("/virtualenvs/carreros/bin/pip install -r requirements.txt")
        run("/virtualenvs/carreros/bin/python manage.py migrate")
        run("/virtualenvs/carreros/bin/python manage.py collectstatic --noinput")
        run("supervisorctl restart carreros")