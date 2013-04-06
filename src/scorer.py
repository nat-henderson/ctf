from scoreboard import db, Team, Problem, ProblemCheckout, Instance
import subprocess, os, random, string
from threading import Timer
session = db.session
TIME = 60.0

t = None

def callback():
    teams = session.query(Team).all()
    for team in teams:
        try:
            run_tests(team.id)
        except Exception as e:
            print e
            continue
    t = Timer(TIME, callback)
    t.start()

def run_tests(teamid):
    team = session.query(Team).filter(Team.id == teamid).first()
    if not team:
        raise Exception("Team does not exist")
    for checkout in session.query(ProblemCheckout).filter(ProblemCheckout.team == teamid).filter(
            ProblemCheckout.state != 'down').all():
        try:
            run_test(teamid, checkout.problem)
        except Exception as e:
            print e
            continue

def run_test(teamid, pid):
    team = session.query(Team).filter(Team.id == teamid).first()
    if not team:
        raise Exception("No such team.")
    instance = session.query(Instance).filter(Instance.iid == team.instance).first()
    problem = session.query(Problem).filter(Problem.problem_id == pid).first()
    if not instance or not problem:
        raise Exception("No such instance or no such problem")
    checkout = session.query(ProblemCheckout).filter(ProblemCheckout.problem == problem.problem_id).filter(
            ProblemCheckout.team == team.id).first()
    if not checkout or checkout.state == 'down':
        raise Exception("Problem is not up!")
    local_test = './testscript-' + str(problem.problem_id)
    if not os.path.exists(local_test):
        remote_f = urlopen(problem.problem_testing_script_location)
        f = open(local_test,'w')
        f.write(remote_f.read())
        f.close()
        os.chmod(local_test, 0755)
    test_pass = (subprocess.call([local_test, 'get', instance.ip, checkout.secret]) == 0)
    if checkout.state == 'compromised':
        team.score -= 20
    elif test_pass:
        checkout.state = 'correct'
        team.score += 1
    else:
        checkout.state = 'incorrect'
        team.score -= 1
    checkout.secret = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(64))
    output = subprocess.call([local_test, 'put', instance.ip, checkout.secret])
    print output
    session.add(checkout)
    session.add(team)
    session.commit()


if __name__ == "__main__":
    t = Timer(TIME, callback)
    t.start()
