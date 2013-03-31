from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
import json

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "afsdjfsafasd239"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ctf:fishandchipsaredelicious@localhost/ctf'
db = SQLAlchemy(app)
session = db.session


class Team(db.Model, UserMixin):
    __tablename__ = 'teams'
    id = db.Column(db.Integer(), primary_key = True)
    teamname = db.Column(db.String(50), unique = True)
    instance_ip = db.Column(db.String(15))
    score = db.Column(db.Integer())


class Problem(db.Model):
    __tablename__ = 'problems'
    problem_id = db.Column(db.Integer(), primary_key = True)
    problem_s3_location = db.Column(db.String(100))
    problem_testing_script_location = db.Column(db.String(100))

class Solution(db.Model):
    __tablename__ = 'solutions'
    sid = db.Column(db.Integer(), primary_key = True)
    team = db.Column(db.String(50), db.ForeignKey('teams.teamname'))
    problem = db.Column(db.Integer(), db.ForeignKey('problems.problem_id'))
    posted_time = db.Column(db.Time())
    state = db.Column(db.Enum('correct', 'compromised', 'incorrect'))
    compromised_by = db.Column(db.String(50), db.ForeignKey('teams.teamname'))

user_datastore = SQLAlchemyUserDatastore(db, Team, None)
security = Security(app, user_datastore)

@app.route('/')
@login_required
def root_callback():
    scores = [{'teamname':x.teamname, 'ip':x.instance_ip, 'score':x.score} for x in session.query(Team).all()]
    return render_template("scoreboard.html", scores = scores)

@app.route('/score/<int:teamid>')
def get_score(teamid):
    try:
        score = session.query(Team).filter(Team.id == teamid).one().score
    except:
        score = 0
    return json.dumps(score)

@app.route('/teams')
def teams():
    teams = session.query(Team).all()
    return json.dumps([x.teamname for x in teams])

if __name__ == "__main__":
    app.run()
