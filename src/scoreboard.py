from flask import Flask, request, render_template, Response, flash, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask.ext.security.forms import RegisterForm, TextField, Required, ConfirmRegisterForm
from flask.ext.mail import Mail
from boto.ec2 import connect_to_region
import json

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "afsdjfsafasd239"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ctf:fishandchipsaredelicious@localhost/ctf'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_PASSWORD_HASH'] = 'plaintext'
app.config['SECURITY_PASSWORD_SALT'] = 'DFa#reJK84rijhAiojOIHGFKLAJR8U'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'casectf@gmail.com'
app.config['MAIL_PASSWORD'] = 'correcthorsebatterystaple'
SECRET_KEY = 'LgGsOQJr27ZRiBeeuRx/kSBf6fV8Qs7wH1o/djA7'
ACCESS_KEY = 'AKIAJGM53Z656332A33A'
ec2 = connect_to_region('us-east-1', aws_access_key_id = ACCESS_KEY,
        aws_secret_access_key = SECRET_KEY)

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
    instance = db.Column(db.Integer(), db.ForeignKey('instances.iid'))
    score = db.Column(db.Integer(), default = 0)
    confirmed_at = db.Column(db.DateTime(), nullable=True)
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

class ProblemCheckout(db.Model):
    __tablename__ = 'checkouts'
    sid = db.Column(db.Integer(), primary_key = True)
    team = db.Column(db.Integer(), db.ForeignKey('teams.id'))
    problem = db.Column(db.Integer(), db.ForeignKey('problems.problem_id'))
    secret_hash = db.Column(db.String(64))
    posted_time = db.Column(db.Time())
    state = db.Column(db.Enum('correct', 'compromised', 'incorrect', 'down'))
    compromised_by = db.Column(db.Integer(), db.ForeignKey('teams.id'), nullable=True)

class Instance(db.Model):
    __tablename__ = 'instances'
    iid = db.Column(db.Integer(), primary_key = True)
    instance_id = db.Column(db.String(12), unique=True)
    ip = db.Column(db.String(15))
    priv_key = db.Column(db.String(2048))


class ExtendedRegisterForm(RegisterForm):
    teamname = TextField('Team Name', [Required()])

user_datastore = SQLAlchemyUserDatastore(db, Team, None)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

@app.route('/scoreboard')
@login_required
def sb_callback():
    scores = [{'teamname':x.teamname, 'score':x.score} for x in session.query(Team).all()]
    return render_template("scoreboard.html", scores = scores)

@app.route('/')
def root_callback():
    print "called by user == " + str(current_user.get_id())
    if current_user.is_anonymous():
        uname = None
        team_id = None
    else:
        uname = current_user.teamname
        team_id = current_user.get_id()
    print uname, team_id
    return render_template("index.html", username = uname, team_id = team_id)

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

@app.route('/team/<int:teamid>')
def team():
    pass

@app.route('/teammanagement')
@login_required
def team_management():
    instance = session.query(Instance).filter(Instance.iid == current_user.instance).first()
    instance_ip = 'Not Ready'
    if instance is None:
        pass
    elif instance.ip is None:
        all_instances = ec2.get_all_instances()
        for reservation in all_instances:
            print reservation
            if reservation.instances[0].id == instance.instance_id:
                if reservation.instances[0].ip_address:
                    instance.ip_address = reservation.instances[0].ip_address
                    instance_ip = instance.ip_address
                    session.add(instance)
                    session.commit()
                break
    else:
        instance_ip = instance.ip_address

    print instance

    return render_template("team_management.html", team = current_user, instance_ip = instance_ip)

@app.route('/teamsetup/<int:teamid>')
@login_required
def setup_a_new_team(teamid):
    if current_user.id != teamid:
        return "<h1>Not Authorized.</h1>\n<p>Try logging in, or maybe get back to hacking on the code and not on my framework, jerk.  :P</p>", 403
    keyname = current_user.teamname

    current_instance = session.query(Instance).filter(Instance.iid == current_user.instance).first()
    if current_instance:
        try:
            ec2.terminate_instances([current_instance.instance_id])
        except: pass

    while ec2.get_key_pair(keyname):
        keyname = str(keyname) + '_'
    key = ec2.create_key_pair(keyname)
    reservation = ec2.run_instances('ami-1cbb2075', key_name = keyname, instance_type = 'm1.small')
    instance = reservation.instances[0]
    instance_record = Instance(ip=instance.ip_address, instance_id = instance.id, priv_key = key.material)
    session.add(instance_record)
    session.commit()
    current_user.instance = instance_record.iid
    session.add(current_user)
    session.commit()
    flash("Your key is here:")
    flash(str(key.material))
    flash("Your instance is being brought up.  Its IP address will be available on the team management page soon.")
    return ""

@app.route('/report')
@login_required #Report will allow users to report either a solution or a compromise.
def report():
    return render_template("report.html", current_user.teamname, current_user.get_id())

@app.route('/report', methods=['POST'])
@login_required
def do_report():
    if request.form['type'] == 'compromise':
        rep_team = current_user.get_id()
        comp_team = request.form['compTeam']
        secret = request.form['secret']
        #sha256 secret
        m = hashlib.sha256()
        m.update(secret)
        match = session.query(ProblemCheckout).filter(ProblemCheckout.secret_hash == m.hexdigest()).first()
        if not match:
            flash('The secret that you have submitted is not valid. Check that you have copied it correctly and try again.')
            return redirect('/')
        if not match.team == comp_team:
            flash ('That solution is not valid.')
        if match.state == 'compromised':
            flash ('That problem has already been compromised.')
            return redirect('/')
        if match.state == 'down':
            flash ('That problem is no longer active.')
            return redirect('/')
        match.state = 'compromised'
        match.compromised_by = rep_team
        session.add(match)
        session.commit()
        flash ('Solution successfully validated!')
        return redirect('/')

    if not request.form['type'] == 'solve':
        return redirect('/')

    team = current_user.get_id()
    problem = request.form['problem']
    match = session.query(ProblemCheckout).filter(ProblemCheckout.team == team).filter(ProblemCheckout.problem = problem).first()
    match.state = 'correct'
    match.posted_time = datetime.now()
    session.add(match)
    session.commit()
    flash('Solution successfully submitted!')
    run_test(team, problem)
    return redirect('/')

if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    app.run(host='0.0.0.0')
