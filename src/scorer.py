from models import Team, Problem, Solution, Session

def callback():
    session = Session()
    teams = session.query(Team).all()
    for team in teams:
        manifest = urllib2.urlopen('http://' + team.instance_ip + '/manifest.xml')
        manifest = manifest.read()
