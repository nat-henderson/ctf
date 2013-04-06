from scoreboard import db, Team, Problem, ProblemCheckout, Instance

session = db.session


def callback():
    teams = session.query(Team).all()
    for team in teams:
        try:
            run_tests(team.id)
        except Exception as e:
            print e
            continue

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
    test_pass = (subprocess.call([local_test, 'get', instance.ip_address, checkout.secret], stdout = output_local) == 0)
    if checkout.state == 'compromised':
        team.score -= 20
    elif test_pass:
        checkout.state = 'correct'
        team.score += 1
    else:
        checkout.state = 'incorrect'
        team.score -= 1
    session.add(checkout)
    session.add(team)
    session.commit()

