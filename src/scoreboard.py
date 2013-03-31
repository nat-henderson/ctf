from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "afsdjfsafasd239"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ctf:fishandchipsaredelicious@localhost/ctf'
db = SQLAlchemy(app)
session = db.session



def Team(db.Model):
    __tablename__ = 'teams'
    teamname = db.Column(db.String(50), primary_key = True)
    instance_ip = db.Column(db.String(15))
    score = db.Column(db.Integer())

def Problem(db.Model):
    __tablename__ = 'problems'
    problem_id = db.Column(Integer(), primary_key = True)
    problem_s3_location = db.Column(db.String(100))
    problem_testing_script_location = db.Column(db.String(100))

def Solution(db.Model):
    __tablename__ = 'solutions'
    sid = db.Column(db.Integer(), primary_key = True)
    team = db.Column(db.String(50), db.ForeignKey('teams.teamname'))
    problem = db.Column(db.Integer(), db.ForeignKey('problems.problem_id'))
    posted_time = db.Column(db.Time())
    state = db.Column(db.Enum(enums = ['correct', 'compromised', 'incorrect']))
    compromised_by = db.Column(String(50), db.ForeignKey('teams.teamname'))



@app.route('/')
def root_callback():
    session = Session()
    scores = [{'teamname':x.teamname, 'ip':x.instance_ip, 'score':x.score} for x in session.query(Team).all()]
    session.close()
    return render_template("scoreboard.html", scores = scores)

@app.route('/score/<teamname>')
def get_score(teamname):
    session = Session()
    try:
        score = session.query(Team).filter(Team.teamname == teamname).one().score
    except:
        score = 0
    session.close()
    return score

@app.route('/teams'):
    session = Session()
    teams = session.query(Team).all()
    session.close()
    return json.dumps([x.teamname for x in teams])


app.run(port=80, bind='0.0.0.0')
