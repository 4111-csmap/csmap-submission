import os
import random
from datetime import time, datetime
from flask import Flask, request, render_template, g, redirect, Response, url_for
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField


# setup
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = b'<REDACTED>'

DB_USER = "eh2890"
DB_PASSWORD = "<REDACTED>"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"

engine = create_engine(DATABASEURI)

# login manager
login_manager = LoginManager(app)

class User():
    def __init__(self, uni, password, name, degree_program, major_track, interests, semesters, enrolled, required, remaining_required):
        self.uni = uni
        self.password = password
        self.name = name
        self.degree_program = degree_program
        self.major_track = major_track
        self.interests = interests
        self.semesters = semesters
        self.enrolled = enrolled
        self.required = required
        self.remaining_required = remaining_required

    def is_active(self):
        return True

    def get_id(self):
        return self.uni

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

def sem_parse(sem):
    sem_decode = {'Fa':'Fall', 'Su':'Summer', 'Sp':'Spring'}
    if sem[0:2] in ['Fa', 'Sp']:
        ending = ''
    else:
        ending = ' '+ sem[-1]
    return sem_decode[sem[0:2]] + ending + ' 20' + sem[2:4]

def sem_encode(sem):
    year = sem[-2:]
    r = sem[:-5]
    sem_cipher = {'Fall':'Fa', 'Summer':'Su', 'Spring':'Sp'}
    if " " in r:
        return sem_cipher[r[:-2]] + year + sem[-6]
    return sem_cipher[r] + year

def sem_sort(key):
    sem_order = {'Fa':0, 'Su':1, 'Sp':3}
    offset = 0
    if key[-1] == "A":
        offset += 1
    return (-int(key[2:4]), sem_order[key[0:2]] + offset)

def day_parse(day):
    day_decode = {'MoWe':'Monday/Wednesday', 'TuTh':'Tuesday/Thursday', 'Mon':'Monday', 'Tue':'Tuesday', 'Wed':'Wednesday', 'Thu':'Thursday', 'Fri':'Friday'}
    return day_decode[day]

def day_encode(day):
    day_cipher = {'Monday/Wednesday':'MoWe', 'Tuesday/Thursday':'TuTh', 'Monday':'Mon', 'Tuesday':'Tue', 'Wednesday':'Wed', 'Thursday':'Thu', 'Friday':'Fri'}
    return day_cipher[day]

def sort_courses(key):
    reqs = {('COMS', '1004'):0,
            ('COMS', '3134'):1,
            ('COMS', '3157'):2,
            ('COMS', '3203'):3,
            ('COMS', '3261'):4,
            ('CSEE', '3827'):5,
            ('COMS', '3251'):6}
    code = (key[0], key[1])
    if code in reqs:
        return reqs[code]
    return int(key[1])

def sort_results(key):
    reqs = {('COMS', '1004'):0,
            ('COMS', '3134'):1,
            ('COMS', '3157'):2,
            ('COMS', '3203'):3,
            ('COMS', '3261'):4,
            ('CSEE', '3827'):5,
            ('COMS', '3251'):6}
    code = (key[0], key[1])
    output = []
    if code in reqs:
        output.append(reqs[code])
    else:
        output.append(int(key[1]))
    x = key[4]
    output.append(-int(x[2:4]))
    sem_order = {'Fa':0, 'Su':1, 'Sp':3}
    offset = 0
    if x[-1] == "A":
        offset += 1
    output.append(sem_order[x[0:2]] + offset)
    return output

def sort_professors(key):
    fields = key[1].split(" ")
    first = fields[0]
    last = fields[1]
    return last, first

def parse_year(year):
    return year.strftime("%Y")

@app.context_processor
def my_utility_processor():
    def get_credits(course):
        t = text("SELECT * FROM COURSES_OFFERED C WHERE C.subject_code = :course0 and C.course_code = :course1 and C.course_name = :course2")
        cursor = g.conn.execute(t, course0=course[0], course1=course[1], course2=course[2])
        credit = 0
        for result in cursor:
            credit = result['credit_options']
        cursor.close()
        return credit

    return dict(get_credits=get_credits)

def update_user(uni):
    # degree_type and major_track
    t = text("SELECT * FROM DECLARED D WHERE D.uni = :uni0")
    cursor = g.conn.execute(t, uni0=uni)
    degree_type = ''
    major_track = ''
    for result in cursor:
        degree_type = result['degree_type']
        major_track = result['major_track']
    cursor.close()
    # interests
    t = text("SELECT * FROM INTERESTED I WHERE I.uni = :uni0")
    cursor = g.conn.execute(t, uni0=uni)
    interests = []
    for result in cursor:
        interests.append(result['cs_subfield_name'])
    cursor.close()
    # semesters
    t = text("SELECT E.semester_id FROM ENROLLED E WHERE E.uni = :uni0 UNION SELECT T.semester_id FROM TAKES T WHERE T.uni = :uni0")
    cursor = g.conn.execute(t, uni0=uni)
    semesters_tmp = []
    for result in cursor:
        semesters_tmp.append(result['semester_id'])
    cursor.close()
    semesters_tmp.sort(key=lambda x: sem_sort(x))
    semesters = []
    for sem in semesters_tmp:
        semesters.append(sem_parse(sem))
    # enrolled
    t = text("SELECT * FROM TAKES T INNER JOIN INSTRUCTS I on T.subject_code = I.subject_code and T.course_code = I.course_code and T.course_name = I.course_name and T.semester_id = I.semester_id and T.call_number = I.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE T.uni = :uni0")
    cursor = g.conn.execute(t, uni0=uni)
    enrolled = []
    for result in cursor:
        course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['call_number'])
        semid = result['semester_id']
        enrolled.append((sem_parse(semid), course))
    enrolled.sort(key=lambda x: sort_courses(x[1]))
    cursor.close()
    # required
    t = text("SELECT * FROM REQUIRES R WHERE R.degree_type = :degree and R.major_track = :major")
    cursor = g.conn.execute(t, degree=degree_type, major=major_track)
    required = []
    for result in cursor:
        required.append((result['subject_code'], result['course_code'], result['course_name']))
    required.sort(key=sort_courses)
    cursor.close()
    # remaining_required
    t = text("SELECT R.subject_code, R.course_code, R.course_name FROM REQUIRES R WHERE R.degree_type = :degree and R.major_track = :major EXCEPT SELECT R.subject_code, R.course_code, R.course_name FROM TAKES T INNER JOIN REQUIRES R on R.subject_code = T.subject_code and R.course_code = T.course_code and R.course_name = T.course_name WHERE T.uni = :uni and R.degree_type = :degree and R.major_track = :major")
    cursor = g.conn.execute(t, degree=degree_type, major=major_track, uni=uni)
    remaining_required = []
    for result in cursor:
        remaining_required.append((result['subject_code'], result['course_code'], result['course_name']))
    remaining_required.sort(key=sort_courses)
    cursor.close()

    current_user.degree_type = degree_type
    current_user.major_track = major_track
    current_user.interests = interests
    current_user.semesters = semesters
    current_user.enrolled = enrolled
    current_user.required = required
    current_user.remaining_required = remaining_required
    return

# some stuff
@login_manager.user_loader
def load_user(user_id):
    uni = user_id
    # password and name
    t = text("SELECT * FROM STUDENTS S WHERE S.uni = :uni")
    cursor = g.conn.execute(t, uni=uni)
    password = ''
    name = ''
    for result in cursor:
        password = result['password']
        name = result['name']
    cursor.close()
    # degree_type and major_track
    t = text("SELECT * FROM DECLARED D WHERE D.uni = :uni")
    cursor = g.conn.execute(t, uni=uni)
    degree_type = ''
    major_track = ''
    for result in cursor:
        degree_type = result['degree_type']
        major_track = result['major_track']
    cursor.close()
    # interests
    t = text("SELECT * FROM INTERESTED I WHERE I.uni = :uni")
    cursor = g.conn.execute(t, uni=uni)
    interests = []
    for result in cursor:
        interests.append(result['cs_subfield_name'])
    cursor.close()
    # semesters
    t = text("SELECT E.semester_id FROM ENROLLED E WHERE E.uni = :uni UNION SELECT T.semester_id FROM TAKES T WHERE T.uni = :uni")
    cursor = g.conn.execute(t, uni=uni)
    semesters_tmp = []
    for result in cursor:
        semesters_tmp.append(result['semester_id'])
    cursor.close()
    semesters_tmp.sort(key=lambda x: sem_sort(x))
    semesters = []
    for sem in semesters_tmp:
        semesters.append(sem_parse(sem))
    # enrolled
    t = text("SELECT * FROM TAKES T INNER JOIN INSTRUCTS I on T.subject_code = I.subject_code and T.course_code = I.course_code and T.course_name = I.course_name and T.semester_id = I.semester_id and T.call_number = I.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE T.uni = :uni")
    cursor = g.conn.execute(t, uni=uni)
    enrolled = []
    for result in cursor:
        course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['call_number'])
        semid = result['semester_id']
        enrolled.append((sem_parse(semid), course))
    enrolled.sort(key=lambda x: sort_courses(x[1]))
    cursor.close()
    # required
    t = text("SELECT * FROM REQUIRES R WHERE R.degree_type = :degree and R.major_track = :major")
    cursor = g.conn.execute(t, degree=degree_type, major=major_track)
    required = []
    for result in cursor:
        required.append((result['subject_code'], result['course_code'], result['course_name']))
    required.sort(key=sort_courses)
    cursor.close()
    # remaining_required
    t = text("SELECT R.subject_code, R.course_code, R.course_name FROM REQUIRES R WHERE R.degree_type = :degree and R.major_track = :major EXCEPT SELECT R.subject_code, R.course_code, R.course_name FROM TAKES T INNER JOIN REQUIRES R on R.subject_code = T.subject_code and R.course_code = T.course_code and R.course_name = T.course_name WHERE T.uni = :uni and R.degree_type = :degree and R.major_track = :major")
    cursor = g.conn.execute(t, degree=degree_type, major=major_track, uni=uni)
    remaining_required = []
    for result in cursor:
        remaining_required.append((result['subject_code'], result['course_code'], result['course_name']))
    remaining_required.sort(key=sort_courses)
    cursor.close()

    return User(uni, password, name, degree_type, major_track, interests, semesters, enrolled, required, remaining_required)

@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

# pages
@app.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Drop
        key = ''
        for i in request.form:
            key = i
        fields = key.split(",")
        subject_code = fields[1]
        course_code = fields[2]
        course_name = fields[3]
        professor = fields[4]
        semester = sem_encode(fields[5])
        call_number = fields[6]
        t = text("DELETE FROM TAKES T WHERE T.uni = :uni and T.subject_code = :subject and T.course_code = :course and T.course_name = :name and T.semester_id = :semester and T.call_number = :call")
        cursor = g.conn.execute(t, uni=current_user.uni, subject=subject_code, course=course_code, name=course_name, semester=semester, call=call_number)
        cursor.close()
        update_user(current_user.uni)
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        t = text("SELECT * FROM STUDENTS S WHERE S.uni = :uni")
        cursor = g.conn.execute(t, uni=request.form['uni'])
        for result in cursor:
            if request.form['password'] == result['password']:
                cursor.close()
                user = load_user(request.form['uni'])
                login_user(user)
                return redirect(url_for('index'))
        cursor.close()
        error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/search", methods=['GET', 'POST'])
def search():
    output = None
    reqs = None

    # get professors
    cursor = g.conn.execute("SELECT * FROM FACULTY F where F.uni != 'n/a'")
    professors = []
    for result in cursor:
        professors.append(result['name'])
    professors.sort()
    cursor.close()
    # get semesters
    cursor = g.conn.execute("SELECT * FROM SEMESTERS")
    semesters_tmp = []
    for result in cursor:
        semesters_tmp.append(result['semester_id'])
    semesters_tmp.sort(key=lambda x: sem_sort(x))
    semesters = []
    for sem in semesters_tmp:
        semesters.append(sem_parse(sem))
    cursor.close()
    # get subfields
    cursor = g.conn.execute("SELECT * FROM CS_SUBFIELDS")
    subfields = []
    for result in cursor:
        subfields.append(result['cs_subfield_name'])
    subfields.sort()
    cursor.close()
    # get days of week
    cursor = g.conn.execute("SELECT enum_range(NULL::DAYS_OF_WEEK)")
    for result in cursor:
        days_tmp = result[0][1:-1].split(',')
    days = []
    for d in days_tmp:
        days.append(day_parse(d))
    cursor.close()
    # create start_times
    start_times = []
    for i in range(8, 20):
        start_times.append(time(i,0,0).strftime("%I:%M %p"))

    # create end_times
    end_times = []
    for i in range(9, 23):
        end_times.append(time(i,0,0).strftime("%I:%M %p"))

    if request.method == 'POST':
        if 'search' in request.form:
            # all courses
            results = set()
            cursor = g.conn.execute("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni")
            for result in cursor:
                course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                results.add(course)
            cursor.close()
            # professor
            if request.form['professor'] != 'Choose...':
                professor_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE F.name = :professor")
                cursor = g.conn.execute(t, professor=request.form['professor'])
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    professor_set.add(course)
                cursor.close()
                results = results.intersection(professor_set)
            # semester
            if request.form['semester'] != 'Choose...':
                semester_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE I.semester_id = :semester")
                cursor = g.conn.execute(t, semester=sem_encode(request.form['semester']))
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    semester_set.add(course)
                cursor.close()
                results = results.intersection(semester_set)
            # subfield
            if request.form['subfield'] != 'Choose...':
                subfield_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F ON F.uni = I.uni INNER JOIN COURSE_WITHIN W ON I.subject_code = W.subject_code and I.course_code = W.course_code and I.course_name = W.course_name WHERE W.cs_subfield_name = :subfield")
                cursor = g.conn.execute(t, subfield=request.form['subfield'])
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    subfield_set.add(course)
                cursor.close()
                results = results.intersection(subfield_set)
            # days
            if request.form['days'] != 'Choose...':
                days_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE S.days_of_week = :days")
                cursor = g.conn.execute(t, days=day_encode(request.form['days']))
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    days_set.add(course)
                cursor.close()
                results = results.intersection(days_set)
            # start_time
            if request.form['start_time'] != 'Choose...':
                start_time_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE S.start_time >= :start\:\:time")
                cursor = g.conn.execute(t, start=datetime.strptime(request.form['start_time'], "%I:%M %p").strftime("%H:%M"))
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    start_time_set.add(course)
                cursor.close()
                results = results.intersection(start_time_set)
            # end_time
            if request.form['end_time'] != 'Choose...':
                end_time_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE S.end_time <= :end\:\:time")
                cursor = g.conn.execute(t, end=datetime.strptime(request.form['end_time'], "%I:%M %p").strftime("%H:%M"))
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    end_time_set.add(course)
                cursor.close()
                results = results.intersection(end_time_set)
            # key phrase
            if request.form['keywords'] != '':
                keywords_set = set()
                t = text("SELECT * FROM INSTRUCTS I INNER JOIN SEMESTER_OFFERED S ON I.subject_code = S.subject_code and I.course_code = S.course_code and I.course_name = S.course_name and I.semester_id = S.semester_id and I.call_number = S.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE UPPER(S.subject_code) LIKE :keywords or UPPER(S.course_code) LIKE :keywords or UPPER(S.course_name) LIKE :keywords")
                cursor = g.conn.execute(t, keywords="%%"+str(request.form['keywords']).upper()+"%%")
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    keywords_set.add(course)
                cursor.close()
                results = results.intersection(keywords_set)

            # output
            output_tmp = list(results)
            output_tmp.sort(key=sort_results)
            output = []
            enrolled = []
            for c in current_user.enrolled:
                enrolled.append(c[1][0:3])
            for out in output_tmp:
                taken = False
                if out[0:3] in enrolled:
                    taken = True
                if out[5]:
                    output.append((out[0], out[1], out[2], out[3], sem_parse(out[4]), taken, out[5].strftime("%I:%M %p"), out[6].strftime("%I:%M %p"), day_parse(out[7]), out[8]))
        else:
            # Add course
            key = ''
            for i in request.form:
                key = i
            fields = key.split(",")
            if fields[0] == 'add':
                subject_code = fields[1]
                course_code = fields[2]
                course_name = fields[3]
                semester = sem_encode(fields[5])
                call_number = fields[6]
                t = text("INSERT INTO TAKES VALUES (:uni, :subject, :code, :name, :semester, :call);")
                cursor = g.conn.execute(t, uni=current_user.uni, subject=subject_code, code=course_code, name=course_name, semester=semester, call=call_number)
                cursor.close()
                update_user(current_user.uni)
                return redirect(url_for("index"))
            else:
                t = text("SELECT * FROM SEMESTER_OFFERED as C JOIN ( SELECT C.subject_code as subject_code, C.course_code as course_code, C.course_name as course_name, num_students_enrolled FROM (SELECT T.course_name, COUNT(DISTINCT S.uni) as num_students_enrolled FROM STUDENTS as S INNER JOIN DECLARED as D ON S.uni = D.uni INNER JOIN TAKES as T ON T.uni = S.uni WHERE semester_id = 'Fa22' AND major_track = :major GROUP BY T.course_name ORDER BY num_students_enrolled DESC) AS TopPop JOIN COURSES_OFFERED as C ON TopPop.course_name = C.course_name) as tmp ON tmp.subject_code = C.subject_code and tmp.course_code = C.course_code and tmp.course_name = C.course_name INNER JOIN INSTRUCTS I ON I.subject_code = C.subject_code and I.course_code = C.course_code and I.course_name = C.course_name and I.semester_id = C.semester_id and I.call_number = C.call_number INNER JOIN FACULTY F ON F.uni = I.uni WHERE C.semester_id = 'Fa22'")
                cursor = g.conn.execute(t, major=current_user.major_track)
                enrolled = []
                for c in current_user.enrolled:
                    enrolled.append(c[1][0:3])
                results = []
                count = 0
                for result in cursor:
                    course = (result['subject_code'], result['course_code'], result['course_name'], result['name'], result['semester_id'], result['start_time'], result['end_time'], result['days_of_week'], result['call_number'])
                    if course[0:3] not in enrolled:
                        count += 1
                        results.append(course)
                        if count >= 3:
                            break
                cursor.close()

                # output
                output_tmp = list(results)
                output_tmp.sort(key=sort_results)
                output = []
                enrolled = []
                for c in current_user.enrolled:
                    enrolled.append(c[1][0:3])
                for out in output_tmp:
                    taken = False
                    if out[0:3] in enrolled:
                        taken = True
                    if out[5]:
                        output.append((out[0], out[1], out[2], out[3], sem_parse(out[4]), taken, out[5].strftime("%I:%M %p"), out[6].strftime("%I:%M %p"), day_parse(out[7]), out[8]))

        # reqs
        reqs = dict()
        t = text("SELECT * FROM ( SELECT interest_subject_code as subject_code, interest_course_code as course_code, interest_course_name as course_name, STRING_AGG(CONCAT(prereq_subject_code, ' ', prereq_course_code, ': ', prereq_course_name), ' or ') as reqs FROM PREREQUISITE_FOR P GROUP BY subject_code, course_code, course_name, batch) T WHERE T.reqs not LIKE all( SELECT CONCAT('%%', T.subject_code, ' ', T.course_code, ': ', T.course_name, '%%') FROM TAKES T INNER JOIN INSTRUCTS I on T.subject_code = I.subject_code and T.course_code = I.course_code and T.course_name = I.course_name and T.semester_id = I.semester_id and T.call_number = I.call_number INNER JOIN FACULTY F on F.uni = I.uni WHERE T.uni = :uni)")
        cursor = g.conn.execute(t, uni=current_user.uni)
        for result in cursor:
            course = (result['subject_code'], result['course_code'], result['course_name'])
            if course in reqs:
                if ' or ' in result['reqs']:
                    insert = " and ("+result['reqs']+")"
                else:
                    insert = " and "+result['reqs']
                reqs[course] += insert
            else:
                reqs[course] = result['reqs']
        cursor.close()

    return render_template("search.html", output=output, professors=professors, semesters=semesters, subfields=subfields, days=days, start_times=start_times, end_times=end_times, reqs=reqs)

@app.route("/professors", methods=['GET', 'POST'])
def professors():
    output = None
    courses = None
    # get professors
    cursor = g.conn.execute("SELECT * FROM FACULTY F where F.uni != 'n/a'")
    professors = []
    for result in cursor:
        professors.append(result['name'])
    professors.sort()
    cursor.close()
    # get departments
    cursor = g.conn.execute("SELECT * FROM DEPARTMENTS")
    departments = []
    for result in cursor:
        departments.append(result['department_name'])
    departments.sort()
    cursor.close()
    # get subfields
    cursor = g.conn.execute("SELECT * FROM CS_SUBFIELDS")
    subfields = []
    for result in cursor:
        subfields.append(result['cs_subfield_name'])
    subfields.sort()
    cursor.close()
    if request.method == 'POST':
        if 'search' in request.form:
            # all professors
            results = set()
            cursor = g.conn.execute("SELECT * FROM (SELECT F.uni, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.uni = F.uni")
            for result in cursor:
                professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                results.add(professor)
            cursor.close()
            # professor
            if request.form['name'] != 'Choose...':
                professor_set = set()
                t = text("SELECT * FROM (SELECT F.uni, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.uni = F.uni WHERE F.name = :name")
                cursor = g.conn.execute(t, name=request.form['name'])
                for result in cursor:
                    professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                    professor_set.add(professor)
                cursor.close()
                results = results.intersection(professor_set)
            # department_name
            if request.form['department'] != 'Choose...':
                department_set = set()
                t = text("SELECT * FROM (SELECT F.uni, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.uni = F.uni WHERE Z.department_name LIKE :department")
                cursor = g.conn.execute(t, department="%%"+request.form['department']+"%%")
                for result in cursor:
                    professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                    department_set.add(professor)
                cursor.close()
                results = results.intersection(department_set)
            # subfield
            if request.form['subfield'] != 'Choose...':
                subfield_set = set()
                t = text("SELECT * FROM (SELECT F.uni, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.uni = F.uni WHERE Z.interests LIKE :subfield")
                cursor = g.conn.execute(t, subfield="%%"+request.form['subfield']+"%%")
                for result in cursor:
                    professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                    subfield_set.add(professor)
                cursor.close()
                results = results.intersection(subfield_set)
            # key phrase
            if request.form['keywords'] != '':
                keywords_set = set()
                t = text("SELECT * FROM (SELECT F.uni, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.uni = F.uni WHERE UPPER(Z.interests) LIKE :keywords or UPPER(F.name) LIKE :keywords or UPPER(Z.uni) LIKE :keywords or UPPER(Z.department_name) LIKE :keywords")
                cursor = g.conn.execute(t, keywords="%%"+str(request.form['keywords']).upper()+"%%")
                for result in cursor:
                    professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                    keywords_set.add(professor)
                cursor.close()
                results = results.intersection(keywords_set)
            # output
            output = list(results)
            output.sort(key=sort_professors)

        else:
            output = []
            t = text("SELECT * FROM ( SELECT MS.uni as zuni, MS.name, COALESCE(match_score, 0) + COALESCE(taken_score, 0) as score FROM ( SELECT F.uni, F.name, num_courses_taken as match_score FROM FACULTY as F INNER JOIN RESEARCHES as R ON F.uni = R.uni INNER JOIN ( SELECT CW.cs_subfield_name as Course_Field, COUNT(DISTINCT CW.course_name) as Num_Courses_Taken FROM STUDENTS as S INNER JOIN DECLARED as D ON S.uni = D.uni INNER JOIN TAKES as T ON S.uni = T.uni INNER JOIN COURSE_WITHIN as CW ON T.course_name = CW.course_name WHERE S.uni = :uni GROUP BY Course_Field) as SC ON SC.Course_Field = R.cs_subfield_name) as MS LEFT JOIN ( SELECT I.uni, 2 * COUNT(I.uni) as taken_score FROM INSTRUCTS as I INNER JOIN TAKES as T ON I.subject_code = T.subject_code and I.course_code = T.course_code and  I.course_name = T.course_name and I.semester_id = T.semester_id and I.call_number = T.call_number WHERE T.uni = :uni GROUP BY I.uni ORDER BY COUNT (I.uni) DESC) as TS ON MS.uni = TS.uni ORDER BY score DESC) as X INNER JOIN (SELECT * FROM (SELECT F.uni as funi, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.funi = F.uni) as Y ON X.zuni = Y.funi WHERE X.score > ( SELECT max(B.score) / 2 as threshold FROM ( SELECT * FROM ( SELECT MS.uni as zuni, MS.name, COALESCE(match_score, 0) + COALESCE(taken_score, 0) as score FROM ( SELECT F.uni, F.name, num_courses_taken as match_score FROM FACULTY as F INNER JOIN RESEARCHES as R ON F.uni = R.uni INNER JOIN ( SELECT CW.cs_subfield_name as Course_Field, COUNT(DISTINCT CW.course_name) as Num_Courses_Taken FROM STUDENTS as S INNER JOIN DECLARED as D ON S.uni = D.uni INNER JOIN TAKES as T ON S.uni = T.uni INNER JOIN COURSE_WITHIN as CW ON T.course_name = CW.course_name WHERE S.uni = :uni GROUP BY Course_Field) as SC ON SC.Course_Field = R.cs_subfield_name) as MS LEFT JOIN ( SELECT I.uni, 2 * COUNT(I.uni) as taken_score FROM INSTRUCTS as I INNER JOIN TAKES as T ON I.subject_code = T.subject_code and I.course_code = T.course_code and  I.course_name = T.course_name and I.semester_id = T.semester_id and I.call_number = T.call_number WHERE T.uni = :uni GROUP BY I.uni ORDER BY COUNT (I.uni) DESC) as TS ON MS.uni = TS.uni ORDER BY score DESC) as X INNER JOIN (SELECT * FROM (SELECT F.uni as funi, max(INTERESTS) as interests, STRING_AGG(A.department_name, ', ') as department_name FROM (SELECT F.uni, STRING_AGG(R.cs_subfield_name, ', ') as INTERESTS FROM FACULTY F INNER JOIN RESEARCHES R ON F.uni = R.uni GROUP BY F.uni) as T INNER JOIN FACULTY F ON F.uni = T.uni INNER JOIN AFFILIATED A on F.uni = A.uni GROUP BY F.uni) AS Z INNER JOIN FACULTY F ON Z.funi = F.uni) as Y ON X.zuni = Y.funi) as B) ORDER BY X.score DESC")
            cursor = g.conn.execute(t, uni=current_user.uni)
            for result in cursor:
                professor = (result['uni'], result['name'], result['department_name'], result['interests'], parse_year(result['doj']))
                output.append(professor)
            cursor.close()
        # courses
        courses = dict()
        for row in output:
            professor = row[0]
            t = text("SELECT DISTINCT subject_code, course_code, course_name, name, F.uni FROM INSTRUCTS as I JOIN Faculty as F on I.uni = F.uni WHERE F.uni = :uni")
            cursor = g.conn.execute(t, uni=professor)
            teaches = []
            for result in cursor:
                teaches.append((result['subject_code'], result['course_code'], result['course_name']))
            cursor.close()
            teaches.sort(key=sort_courses)
            courses[professor] = teaches
    return render_template("professors.html", output=output, professors=professors, departments=departments, subfields=subfields, courses=courses)

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    # get semesters
    cursor = g.conn.execute("SELECT * FROM SEMESTERS")
    semesters = []
    for result in cursor:
        semesters.append(sem_parse(result['semester_id']))
    cursor.close()
    semesters.sort(key=lambda x: sem_sort(sem_encode(x)))
    # get interests
    cursor = g.conn.execute("SELECT * FROM CS_SUBFIELDS")
    interests = []
    for result in cursor:
        interests.append(result['cs_subfield_name'])
    interests.sort()
    cursor.close()
    # get degrees
    degrees = []
    cursor = g.conn.execute("SELECT enum_range(NULL::DEGREE_TYPES)")
    for result in cursor:
        degrees = result[0][1:-1].replace('"','').split(',')
    cursor.close()
    # get major_tracks
    major_tracks = []
    cursor = g.conn.execute("SELECT enum_range(NULL::MAJOR_TRACK)")
    for result in cursor:
        major_tracks = result[0][1:-1].replace('"','').split(',')
    cursor.close()

    if request.method == 'POST':
        # update semesters
        for s in semesters:
            if s in request.form and s not in current_user.semesters:
                t = text("INSERT INTO ENROLLED VALUES (:uni, :sem);")
                cursor = g.conn.execute(t, uni=current_user.uni, sem=sem_encode(s))
                cursor.close()
            elif s not in request.form and s in current_user.semesters:
                t = text("DELETE FROM ENROLLED E WHERE E.uni = :uni and E.semester_id = :sem;")
                cursor = g.conn.execute(t, uni=current_user.uni, sem=sem_encode(s))
                cursor.close()
        # update interests
        for s in interests:
            if s in request.form and s not in current_user.interests:
                t = text("INSERT INTO INTERESTED VALUES (:uni, :sem);")
                cursor = g.conn.execute(t, uni=current_user.uni, sem=s)
                cursor.close()
            elif s not in request.form and s in current_user.interests:
                t = text("DELETE FROM INTERESTED E WHERE E.uni = :uni and E.cs_subfield_name = :sem;")
                cursor = g.conn.execute(t, uni=current_user.uni, sem=s)
                cursor.close()
        # update degree and track
        t = text("DELETE FROM DECLARED WHERE uni = :uni")
        cursor = g.conn.execute(t, uni=current_user.uni)
        cursor.close()
        print("______________")
        print(request.form)
        if request.form['degree'] in ['CS Minor', 'CS Concentration']:
            t = text("INSERT INTO DECLARED VALUES (:uni, :deg, 'N/A');")
            cursor = g.conn.execute(t, uni=current_user.uni, deg=request.form['degree'])
        else:
            print('should be major:', request.form['degree'])
            t = text("INSERT INTO DECLARED VALUES (:uni, :deg, :track);")
            cursor = g.conn.execute(t, uni=current_user.uni, deg=request.form['degree'], track=request.form['major_track'])
        cursor.close()
        
        update_user(current_user.uni)
        return redirect(url_for("index"))

    return render_template("settings.html", semesters=semesters, current_semesters=current_user.semesters, interests=interests, current_interests=current_user.interests, degrees=degrees, current_degree=current_user.degree_program, major_tracks=major_tracks, current_track=current_user.major_track)

app.run(host='0.0.0.0', port=5000, debug=False)
login_manager.login_view = "login"
login_manager.init_app(app)
