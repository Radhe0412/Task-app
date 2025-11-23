from flask import Flask,render_template,url_for,request,redirect,session
from flask_session import Session
import pymysql
from datetime import date
app= Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.session_cookie_name = 'my_custom_cookie_name'
Session(app)
conn=pymysql.connect(host='localhost', user='root', password='', db='todolist')

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor=conn.cursor()
    user_id=session['user_id']
    query="Select COUNT(user_id) from tasks where status=0 and user_id=%s"
    cursor.execute(query,(user_id,))
    pending=cursor.fetchone()[0]
    query="Select COUNT(user_id) from tasks where user_id=%s"
    cursor.execute(query,(user_id,))
    total=cursor.fetchone()[0]
    query="Select COUNT(user_id) from tasks where status=1 and user_id=%s"
    cursor.execute(query,(user_id,))
    completed=cursor.fetchone()[0]
    return render_template('/user/home.html',pending=pending,total=total,completed=completed)


@app.route('/register')
def register():
    return render_template('/user/register.html')

@app.route('/register_process',methods=['POST'])
def register_process():
    user_name = request.form['user_name']
    contact_no = request.form['contact_no']
    user_email = request.form['user_email']
    user_pass = request.form['user_pass']
    gender = request.form['gender']
    date = request.form['date']
    cursor=conn.cursor()
    query = "Insert into user_register(user_name,contact_no,user_email,user_pass,gender,date) values(%s,%s,%s,%s,%s,%s)"
    val = (user_name,contact_no,user_email,user_pass,gender,date)
    cursor.execute(query,val)
    conn.commit()
    cursor.close()
    msg = "Register successfully"
    return redirect(url_for('login',msg=msg))

@app.route('/login')
def login():
    return render_template('/user/login.html')

@app.route('/login_process',methods=['POST'])
def login_process():
    user_email = request.form['user_email']
    user_pass = request.form['user_pass']
    cursor = conn.cursor()
    query = "Select * from user_register where user_email = %s and user_pass = %s"
    val = (user_email,user_pass)
    cursor.execute(query, val)
    account = cursor.fetchone()
    cursor.close()

    if account:
        session['user_id'] = account[0]
        session['user_name'] = account[1]
        session['user_email'] = account[4]
        session['user_pass'] = account[2]
        session['status'] = account[5]
        msg="Login successfully"
        return redirect(url_for('home'))
    else:
        msg = "Incorrect email or password"
        return redirect(url_for('login'))

@app.route('/all_tasks')
def all_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor = conn.cursor()
    user_id = session['user_id']
    query = "Select * from tasks where user_id = %s ORDER BY due_date ASC"
    val = (user_id)
    cursor.execute(query,val)
    account = cursor.fetchall()
    return render_template('/user/all_tasks.html',data=account)

@app.route('/add_task')
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('/user/add_task.html')

@app.route('/add_task_process',methods=['POST'])
def add_task_process():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    task_title = request.form['task_title']
    task_description = request.form['task_description']
    due_date = request.form['due_date']
    created_date = request.form['created_date']
    priority = request.form['priority']
    cursor=conn.cursor()
    query = "Insert into tasks(user_id,task_title,task_description,due_date,created_date,priority) values(%s,%s,%s,%s,%s,%s)"
    val = (user_id,task_title,task_description,due_date,created_date,priority)
    cursor.execute(query,val)
    conn.commit()
    cursor.close()
    msg = "Tasks added successfully"
    return redirect(url_for('home',msg=msg))




@app.route('/pending_tasks')
def pending_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor = conn.cursor()
    user_id = session['user_id']
    query = "Select * from tasks where user_id = %s and status=0"
    val = (user_id)
    cursor.execute(query,val)
    account = cursor.fetchall()
    return render_template('/user/pending_tasks.html',data=account)


@app.route('/today_tasks')
def today_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor=conn.cursor()
    user_id=session['user_id']
    today=date.today().isoformat()
    query="Select * from tasks where due_date=%s and user_id=%s"
    val=(today,user_id)
    cursor.execute(query,val)
    account=cursor.fetchall()
    return render_template('/user/today_tasks.html',data=account)
    
@app.route('/upcoming_tasks')
def upcoming_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor=conn.cursor()
    user_id=session['user_id']
    due_date=date.today().isoformat()
    query="SELECT * from tasks where created_date>%s and user_id=%s"
    val=(due_date,user_id)
    cursor.execute(query,val)
    account=cursor.fetchall()
    return render_template('/user/upcoming_tasks.html',data=account)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    cursor=conn.cursor()
    query="DELETE from tasks where task_id=%s"
    val=(task_id,)
    cursor.execute(query,val)
    conn.commit()
    return redirect(url_for('all_tasks'))

@app.route('/done_tasks')
def done_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor = conn.cursor()
    user_id = session['user_id']
    query = "Select * from tasks where user_id = %s and status=1"
    val = (user_id)
    cursor.execute(query,val)
    account = cursor.fetchall()
    return render_template('/user/completed_tasks.html',data=account)

@app.route('/complete_tasks/<int:task_id>') 
def complete_tasks(task_id):
    cursor=conn.cursor()
    query="UPDATE tasks SET status='1' where task_id=%s"
    val=(task_id,)
    cursor.execute(query,val)
    conn.commit()
    cursor.close()
    return redirect(url_for('all_tasks'))


@app.route('/contact_2')
def contact_2():
    return render_template('/user/contact_2.html')

@app.route('/logout') 
def logout():
    session.pop('user_id',None)
    session.pop('user_email',None)
    session.pop('user_name',None)
    session.pop('user_pass',None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    cursor=conn.cursor()
    user_id=session['user_id']
    query="Select * from user_register where user_id=%s"
    val=(user_id,)
    cursor.execute(query,val)
    info=cursor.fetchone()
    return render_template('/user/profile.html',info=info)

@app.route('/update_profile',methods=['POST'])
def update_profile():
    user_id=request.form['user_id']
    user_name=request.form['user_name']
    user_email=request.form['user_email']
    user_pass=request.form['user_pass']
    gender=request.form['gender']
    date=request.form['date']
    cursor=conn.cursor()
    query="UPDATE user_register SET user_name=%s,user_email=%s,user_pass=%s,gender=%s,date=%s where user_id=%s"
    val=(user_name,user_email,user_pass,gender,date,user_id)
    cursor.execute(query,val)
    conn.commit()
    return redirect(url_for('home'))

@app.route('/forget_password')
def forget_password():
    return render_template('user/forget_password.html')

@app.route('/admin/home2')
def home2():
    if 'admin_id' not in session:
        return redirect(url_for('login2'))
    cursor=conn.cursor()
    today=date.today().isoformat()
    query2 = """SELECT u.user_name,t.task_id,t.task_title,t.task_description,t.due_date, t.status,t.created_date,t.user_id,t.priority FROM tasks t
    JOIN user_register u ON t.user_id = u.user_id where t.due_date=%s"""
    val=(today,)
    cursor.execute(query2,val)
    account2 = cursor.fetchall()
    query="Select COUNT(*) from tasks where due_date=%s"
    cursor.execute(query,(today,))
    total_today=cursor.fetchone()[0]
    query="Select COUNT(*) from tasks where due_date=%s and status=0"
    cursor.execute(query,(today,))
    pending=cursor.fetchone()[0]
    query="Select COUNT(*) from tasks where due_date=%s and status=1"
    cursor.execute(query,(today,))
    completed=cursor.fetchone()[0]
    query="Select COUNT(*) from user_register"
    cursor.execute(query,)
    total_users=cursor.fetchone()[0]
    return render_template('admin/home2.html',data2=account2,today=today,total_today=total_today,pending=pending,completed=completed,total_users=total_users)

@app.route('/admin/users')
def users():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_register")
    account = cursor.fetchall()
    return render_template('admin/users.html', data=account)


@app.route('/admin/profile2')
def profile2():
    cursor=conn.cursor()
    query="Select * from admin_login"
    cursor.execute(query,)
    account=cursor.fetchall()
    return render_template('admin/profile2.html',data=account)

@app.route('/admin/update_profile2',methods=['POST'])
def update_profile2():
    cursor=conn.cursor()
    admin_id=request.form['admin_id']
    admin_email=request.form['admin_email']
    admin_pass=request.form['admin_pass']
    query="Update admin_login SET admin_email=%s,admin_pass=%s where admin_id=%s"
    val=(admin_email,admin_pass,admin_id)
    cursor.execute(query,val,)
    conn.commit()
    return redirect(url_for('home2'))

@app.route('/admin/reports')
def reports():
    return render_template('admin/reports.html')

@app.route('/admin/tasks')
def tasks():
    return render_template('admin/tasks.html')



@app.route('/admin/logout2')
def logout2():
    session.pop('admin_id',None)
    session.pop('admin_email',None)
    session.pop('admin_pass',None)
    return redirect(url_for('login2'))

@app.route('/login2')
def login2():
    return render_template('/admin/login2.html')

@app.route('/login2_process',methods=['POST'])
def login2_process():
    admin_email=request.form['admin_email']
    admin_pass=request.form['admin_pass']
    cursor=conn.cursor()
    query="Select * from admin_login where admin_email=%s and admin_pass=%s"
    val=(admin_email,admin_pass)
    cursor.execute(query,val)
    account=cursor.fetchone()
    if account:
        session['admin_id']=account[0]
        session['admin_email']=account[1]
        session['admin_pass']=account[2]
        return redirect(url_for('home2'))
    
@app.route('/status_update/<int:user_id>')
def status_update(user_id):
    cursor=conn.cursor()
    query="UPDATE user_register SET status=1 where user_id=%s"
    val=(user_id,)
    cursor.execute(query,val)
    conn.commit()
    cursor.close()
    return redirect(url_for('users'))

   
@app.route('/status2_update/<int:user_id>')
def status2_update(user_id):
    cursor=conn.cursor()
    query="UPDATE user_register SET status=0 where user_id=%s"
    val=(user_id,)
    cursor.execute(query,val)
    conn.commit()
    cursor.close()
    return redirect(url_for('users'))

@app.route('/task_detail/<int:user_id>')
def task_detail(user_id):
    cursor = conn.cursor()
    query = "SELECT * FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    tasks = cursor.fetchall()
    return render_template("/admin/task_detail.html", data=tasks)

if __name__=='__main__':
    app.run(debug='True')
