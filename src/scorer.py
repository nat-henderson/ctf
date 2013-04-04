from scorer import db, Team, Problem, Solution, ACCESS_KEY, SECRET_KEY
from lxml import etree
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import uuid

BUCKET_NAME = 'case_ctf_spring_2013'

session = db.session
s3 = S3Connection(ACCESS_KEY, SECRET_KEY)

def callback():
    teams = session.query(Team).all()
    for team in teams:
        run_tests(team.id)

def run_tests(teamid):
    team = session.query(Team).filter(Team.id == teamid).first()
    if not team:
        return ""
    instance = session.query(Instance).filter(Instance.id == team.instance).first()
    if not instance:
        return ""
    for solution in session.query(Solution).filter(team == teamid).all():
        run_test(teamid, solution.problem)

def run_test(teamid, pid):
    team = session.query(Team).filter(Team.id == teamid).first()
    if not team:
        return ""
    instance = session.query(Instance).filter(Instance.id == team.instance).first()
    if not instance:
        return ""
    problem = session.query(Problem).filter(Problem.problem_id == pid).first()
    if not problem:
        return ""
    bucket = create_bucket(BUCKET_NAME)
    key = Key(bucket)
    key.key = problem.problem_testing_script_location
    local_test = './testscript-' + str(problem.problem_id) + '-' + str(uuid.uuid1())
    key.get_contents_to_filename(local_test)
    localhost_output = './localhost-' + str(problem.problem_id) + '-' + str(uuid.uuid1())
    instance_output = './instance-' + str(problem.problem_id) + '-' + str(uuid.uuid1())
    output_local = open(localhost_output, 'w')
    output_instance = open(instance_output, 'w')
    subprocess.call([localtest, 'runtest', 'localhost'], stdout = output_local)
    subprocess.call([localtest, 'runtest', instance.ip], stdout = output_instance)
    output_local.close()
    output_instance.close()
    test_pass = (subprocess.call([localtest, 'compare', localhost_output, instance_output]) == 0)
    if test_pass:
        solution.state = 'correct'
        team.score += 1
    else:
        solution.state = 'incorrect'
        team.score -= 1
    session.add(solution)
    session.add(team)
    session.commit()

