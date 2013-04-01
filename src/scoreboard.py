from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask.ext.mail import Mail
import json

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "afsdjfsafasd239"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ctf:fishandchipsaredelicious@localhost/ctf'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = 'DFa#reJK84rijhAiojOIHGFKLAJR8U'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'casectf@gmail.com'
app.config['MAIL_PASSWORD'] = 'correcthorsebatterystaple'
mail = Mail(app)
db = SQLAlchemy(app)
session = db.session

roles_teams = db.Table('roles_teams',
                db.Column('team_id', db.Integer(), db.ForeignKey('teams.id')),
                db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))

class Team(db.Model, UserMixin):
    __tablename__ = 'teams'
    id = db.Column(db.Integer(), primary_key = True)
    email = db.Column(db.String(50), unique = True)
    teamname = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    active = db.Column(db.Boolean())
    instance_ip = db.Column(db.String(15))
    score = db.Column(db.Integer())
    roles = db.relationship('Role', secondary=roles_teams,
                backref=db.backref('teams', lazy='dynamic'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Problem(db.Model):
    __tablename__ = 'problems'
    problem_id = db.Column(db.Integer(), primary_key = True)
    problem_s3_location = db.Column(db.String(100))
    problem_testing_script_location = db.Column(db.String(100))

class Solution(db.Model):
    __tablename__ = 'solutions'
    sid = db.Column(db.Integer(), primary_key = True)
    team = db.Column(db.Integer(), db.ForeignKey('teams.id'))
    problem = db.Column(db.Integer(), db.ForeignKey('problems.problem_id'))
    posted_time = db.Column(db.Time())
    state = db.Column(db.Enum('correct', 'compromised', 'incorrect'))
    compromised_by = db.Column(db.Integer(), db.ForeignKey('teams.id'))

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

@app.route('/teammanagement')
@login_required
def team_management():
    pass

@app.route('/teamsetup/<teamname>')
@login_required
def setup_a_new_team(teamname):
    pass


if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    session.add(Team(teamname = "thisisatest", email="team", password="test", active=True))
    session.commit()
    app.run()
