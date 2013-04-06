from scoreboard import *

@app.route('/scoreboard')
@login_required
def sb_callback():
    teams = [x.id for x in session.query(Team).all()]
    return render_template("scoreboard.html", teams = teams)

@app.route('/')
def root_callback():
    print current_user
    if current_user.is_anonymous():
        uname = None
        team_id = None
    else:
        uname = current_user.teamname
        team_id = current_user.get_id()
        checkouts = session.query(ProblemCheckout).filter(ProblemCheckout.team == team_id).all()
        print checkouts
        if not checkouts:
            for problem in session.query(Problem).all():
                session.add(ProblemCheckout(team=team_id, problem=problem.problem_id, secret=None, posted_time=None,
                    state='down', compromised_by=None))
            session.commit()

    return render_template("index.html", username = uname, team_id = team_id)

@app.route('/score/<int:teamid>')
def get_score(teamid):
    try:
        team = session.query(Team).filter(Team.id == teamid).one()
        instance = session.query(Instance).filter(Instance.iid == current_user.instance).first()
        if not instance or not instance.ip:
          instance_ip = "Not Ready"
        else:
          instance_ip = instance.ip
    except:
        score = 0
    return json.dumps([team.teamname, team.score, instance_ip])

@app.route('/teams')
def teams():
    teams = session.query(Team).all()
    return json.dumps([x.teamname for x in teams])

@app.route('/team')
@login_required
def redirect_team():
    #return team(current_user.get_id())
    teamid = current_user.get_id()
    team = session.query(Team).filter(Team.id == teamid).first()
    checkouts = session.query(ProblemCheckout).filter(ProblemCheckout.team == teamid).all()
    if request.json:
      #return json.dumps([[checkout.sid, checkout.team, checkout.problem, checkout.secret, checkout.posted_time, checkout.state, checkout.compromised_by] for checkout in checkouts])
      return json.dumps([[1,2,3,4,5,6]])
    else:
      return render_template('team.html')

@app.route('/team/<int:teamid>')
def team(teamid):
    team = session.query(Team).filter(Team.id == teamid).first()
    checkouts = session.query(ProblemCheckout).filter(ProblemCheckout.team == teamid).all()
    if request.json:
      return json.dumps([[checkout.sid, checkout.team, checkout.problem, checkout.secret, checkout.posted_time, checkout.state, checkout.compromised_by] for checkout in checkouts])
    else:
      return render_template('team.html', team=team, checkouts = checkouts)


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
                    instance.ip = reservation.instances[0].ip_address
                    instance_ip = instance.ip
                    session.add(instance)
                    session.commit()
                break
    else:
        instance_ip = instance.ip

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
    reservation = ec2.run_instances('ami-1cbb2075', key_name = keyname,
            instance_type = 'm1.small', user_data = startup_script, security_groups = ['superdumb'])
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
    return render_template("report.html")

@app.route('/compromise', methods=['POST'])
@login_required
def do_compromise():
    rep_team = current_user.get_id()
    comp_team = request.form['compTeam']
    secret = request.form['secret']
    match = session.query(ProblemCheckout).filter(ProblemCheckout.secret == secret).first()
    if not match:
        flash('The secret that you have submitted is not valid. Check that you have copied it correctly and try again.')
        return redirect('/')
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

@app.route('/manageproblems')
@login_required
def manage_problems():
    team_id = current_user.get_id()
    problems = session.query(ProblemCheckout, Problem).filter(ProblemCheckout.team == team_id).filter(
            Problem.problem_id == ProblemCheckout.problem).all()
    ip = session.query(Instance).filter(Instance.iid == current_user.instance).first()
    if ip is not None:
        ip = ip.ip

    return render_template('problem_management.html', problems = problems, team=current_user, instance_ip = ip)

@app.route('/bringup/<int:problem_id>')
def bring_up_problem(problem_id):
    print 'test'
    checkout = session.query(ProblemCheckout).filter(ProblemCheckout.team == current_user.get_id()).filter(
            ProblemCheckout.problem == problem_id).first()
    problem = session.query(Problem).filter(Problem.problem_id == problem_id).first()
    instance = session.query(Instance).filter(Instance.iid == current_user.instance).first()
    print checkout, problem, instance, instance.ip
    if not checkout or not problem or not instance or not instance.ip:
        flash('problem or instance does not exist')
        return ""

    local_test = './testscript-' + str(problem.problem_id)
    print local_test
    if not os.path.exists(local_test):
        remote_f = urlopen(problem.problem_testing_script_location)
        f = open(local_test,'w')
        f.write(remote_f.read())
        f.close()
        os.chmod(local_test, 0755)

    checkout.secret = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(64))

    output = subprocess.call([local_test, 'put', instance.ip, checkout.secret])
    if output == 0:
        flash('successfully brought up the service.')
        checkout.state = 'correct'
        checkout.posted_time = datetime.time(datetime.now())
        session.add(checkout)
        session.commit()
    else:
        flash('did not successfully bring up the service; check to see that it is running on the right port.')
    return ""


@app.route('/bringdown/<int:problem_id>')
def bring_down_problem(problem_id):
    checkout = session.query(ProblemCheckout).filter(ProblemCheckout.team == current_user.get_id()).filter(
            ProblemCheckout.problem == problem_id).first()
    if not checkout:
        flash('problem does not exist')
        return redirect('/')
    checkout.secret = None
    checkout.posted_time = None
    checkout.state = 'down'
    checkout.compromised_by = None
    session.add(checkout)
    session.commit()
    flash('successfully taken down')
    return ""

@app.route('/complete', methods=['POST'])
@login_required
def do_complete():
    team = current_user.get_id()
    problem = request.form['problem']
    match = session.query(ProblemCheckout).filter(ProblemCheckout.team == team).filter(ProblemCheckout.problem == problem).first()
    if not match:
        flash('No such problem.')
        return redirect('/')

    match.state = 'correct'
    match.posted_time = datetime.now()
    session.add(match)
    session.commit()
    flash('Solution successfully submitted!')
    run_test(team, problem)
    return redirect('/')


if __name__ == "__main__":
    for problem in session.query(Problem).all():
        startup_script += '\nwget -O /home/ubuntu/problem' + str(problem.problem_id) + '.tgz ' + problem.problem_download_location + '\n'
        startup_script += 'tar xpzf /home/ubuntu/problem' + str(problem.problem_id) + '.tgz -C /home/ubuntu/\n'
    print startup_script
    app.run(host='0.0.0.0', port=80)
