from scoreboard import db, Problem

db.drop_all()
db.create_all()
db.session.add(Problem(problem_download_location='https://s3.amazonaws.com/case_ctf_spring_2013/keyvalue_store.tgz',
    problem_name = 'keyvalue_store',
    problem_testing_script_location = 'https://s3.amazonaws.com/case_ctf_spring_2013/check_keystore.sh' ))
db.session.add(Problem(problem_download_location='https://s3.amazonaws.com/case_ctf_spring_2013/obfs.tgz',
    problem_name = 'obfuscated python',
    problem_testing_script_location = 'https://s3.amazonaws.com/case_ctf_spring_2013/test_onlinedict.py' ))
db.session.add(Problem(problem_download_location='https://s3.amazonaws.com/case_ctf_spring_2013/tattle.tgz',
    problem_name = 'Tattle',
    problem_testing_script_location = 'https://s3.amazonaws.com/case_ctf_spring_2013/check_tattle'))
db.session.commit()
