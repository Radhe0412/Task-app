from flask import Flask, render_template, url_for, request, redirect, session
from flask_session import Session
import pymysql
import os
from datetime import date

app = Flask(__name__)

# -------------------------
# SESSION CONFIG
# -------------------------
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.session_cookie_name = 'my_custom_cookie_name'
Session(app)

# -------------------------
# DATABASE CONNECTION (DYNAMIC FOR RENDER)
# -------------------------
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.Cursor
    )

# -------------------------
# USER HOME
# -------------------------
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status=0 AND user_id=%s", (user_id,))
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=%s", (user_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status=1 AND user_id=%s", (user_id,))
    completed = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('user/home.html', pending=pending, total=total, completed=completed)

# -------------------------
# USER AUTH
# -------------------------
@app.route('/register')
def register():
    return render_template('/user/register.html')


@app.route('/register_process', methods=['POST'])
def register_process():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_name = request.form['user_name']
    contact_no = request.form['contact_no']
    user_email = request.form['user_email']
    user_pass = request.form['user_pass']
    gender = request.form['gender']
    dob = request.form['date']

    cursor.execute("SELECT * FROM user_register WHERE user_email=%s", (user_email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        return render_template('/user/register.html', msg="This email is already registered")

    query = """INSERT INTO user_register (user_name, contact_no, user_email, user_pass, gender, date)
               VALUES (%s, %s, %s, %s, %s, %s)"""

    cursor.execute(query, (user_name, contact_no, user_email, user_pass, gender, dob))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('/user/login.html')


@app.route('/login_process', methods=['POST'])
def login_process():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_email = request.form['user_email']
    user_pass = request.form['user_pass']

    cursor.execute("SELECT * FROM user_register WHERE user_email=%s AND user_pass=%s",
                   (user_email, user_pass))
    account = cursor.fetchone()

    cursor.close()
    conn.close()

    if account:
        if account[5] == 1:
            return render_template('/user/login.html', msg='Your account has been blocked by admin')

        session['user_id'] = account[0]
        session['user_name'] = account[1]
        session['user_email'] = account[4]
        session['status'] = account[5]

        return redirect(url_for('home'))
    else:
        return render_template('/user/login.html', msg="Incorrect email or password")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------------
# TASK MANAGEMENT
# -------------------------
@app.route('/all_tasks')
def all_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY due_date ASC",
                   (session['user_id'],))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('/user/all_tasks.html', data=data)


@app.route('/view_task', methods=['POST'])
def view_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_text = request.form['Task_name']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM tasks 
                      WHERE user_id=%s AND task_title LIKE %s 
                      ORDER BY due_date ASC""",
                   (session['user_id'], f"%{search_text}%"))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('/user/view_task.html', data=data)


@app.route('/add_task')
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('/user/add_task.html')


@app.route('/add_task_process', methods=['POST'])
def add_task_process():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""INSERT INTO tasks 
                      (user_id, task_title, task_description, due_date, created_date, priority)
                      VALUES (%s, %s, %s, %s, %s, %s)""",
                   (session['user_id'], request.form['task_title'], request.form['task_description'],
                    request.form['due_date'], request.form['created_date'], request.form['priority']))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('home'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE task_id=%s", (task_id,))
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('all_tasks'))


@app.route('/complete_tasks/<int:task_id>')
def complete_tasks(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE tasks SET status=1 WHERE task_id=%s", (task_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('all_tasks'))

# -------------------------
# ADMIN PANEL
# -------------------------
@app.route('/login2')
def login2():
    return render_template('/admin/login2.html')


@app.route('/login2_process', methods=['POST'])
def login2_process():
    conn = get_db_connection()
    cursor = conn.cursor()

    admin_email = request.form['admin_email']
    admin_pass = request.form['admin_pass']

    cursor.execute("SELECT * FROM admin_login WHERE admin_email=%s AND admin_pass=%s",
                   (admin_email, admin_pass))
    account = cursor.fetchone()

    cursor.close()
    conn.close()

    if account:
        session['admin_id'] = account[0]
        session['admin_email'] = account[1]
        return redirect(url_for('home2'))

    return render_template('/admin/login2.html', msg="Incorrect login")


@app.route('/admin/logout2')
def logout2():
    session.clear()
    return redirect(url_for('login2'))


@app.route('/admin/home2')
def home2():
    if 'admin_id' not in session:
        return redirect(url_for('login2'))

    conn = get_db_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("""SELECT u.user_name, t.task_id, t.task_title, t.task_description, 
                      t.due_date, t.status, t.created_date, t.priority 
                      FROM tasks t 
                      JOIN user_register u ON t.user_id=u.user_id 
                      WHERE t.due_date=%s""", (today,))
    today_tasks = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date=%s", (today,))
    total_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date=%s AND status=0", (today,))
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date=%s AND status=1", (today,))
    completed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_register")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM user_register")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/home2.html', data2=today_tasks, today=today,
                           total_today=total_today, pending=pending, completed=completed,
                           total_users=total_users, data3=users)


@app.route('/status_update/<int:user_id>')
def status_update(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE user_register SET status=1 WHERE user_id=%s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('users'))


@app.route('/status2_update/<int:user_id>')
def status2_update(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE user_register SET status=0 WHERE user_id=%s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('users'))


@app.route('/admin/users')
def users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_register")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/users.html', data=data)


@app.route('/task_detail/<int:user_id>')
def task_detail(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE user_id=%s", (user_id,))
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("/admin/task_detail.html", data=tasks)


# -------------------------
# RUN APP (Render uses Gunicorn)
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
