from flask import Flask, request, render_template, Response, flash, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask.ext.security.forms import RegisterForm, TextField, Required, ConfirmRegisterForm
from flask.ext.mail import Mail
from boto.ec2 import connect_to_region
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from urllib2 import urlopen
from datetime import datetime
import json, os, random, string, subprocess

app = Flask(__name__)
app.config['DEBUG'] = False 
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
BUCKET_NAME = 'case_ctf_spring_2013'
SECRET_KEY = 'LgGsOQJr27ZRiBeeuRx/kSBf6fV8Qs7wH1o/djA7'
ACCESS_KEY = 'AKIAJGM53Z656332A33A'
ec2 = connect_to_region('us-east-1', aws_access_key_id = ACCESS_KEY,
        aws_secret_access_key = SECRET_KEY)
startup_script = "#! /bin/bash"

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
    problem_name = db.Column(db.String(50), unique=True)
    problem_download_location = db.Column(db.String(100))
    problem_testing_script_location = db.Column(db.String(100))

class ProblemCheckout(db.Model):
    __tablename__ = 'checkouts'
    sid = db.Column(db.Integer(), primary_key = True)
    team = db.Column(db.Integer(), db.ForeignKey('teams.id'))
    problem = db.Column(db.Integer(), db.ForeignKey('problems.problem_id'))
    secret = db.Column(db.String(64))
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
