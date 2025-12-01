from flask import Flask, render_template, url_for, request, redirect, session, flash
from flask_session import Session
import pymysql
import os
from datetime import date

app = Flask(__name__)

# -------------------------
# SESSION CONFIG
# -------------------------
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.session_cookie_name = 'my_custom_cookie_name'
Session(app)

# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
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

    cursor.execute("SELECT COUNT(*) AS cnt FROM tasks WHERE status=0 AND user_id=%s", (user_id,))
    pending = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM tasks WHERE user_id=%s", (user_id,))
    total = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM tasks WHERE status=1 AND user_id=%s", (user_id,))
    completed = cursor.fetchone()['cnt']

    cursor.close()
    conn.close()

    return render_template('user/home.html', pending=pending, total=total, completed=completed)

# -------------------------
# USER AUTH
# -------------------------
@app.route('/register')
def register():
    return render_template('user/register.html')

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
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return render_template('user/register.html', msg="This email is already registered")

    cursor.execute(
        "INSERT INTO user_register (user_name, contact_no, user_email, user_pass, gender, date, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, 0)",
        (user_name, contact_no, user_email, user_pass, gender, dob)
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Registration successful! Please login.")
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('user/login.html')

@app.route('/login_process', methods=['POST'])
def login_process():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_email = request.form['user_email']
    user_pass = request.form['user_pass']

    cursor.execute("SELECT * FROM user_register WHERE user_email=%s AND user_pass=%s", (user_email, user_pass))
    account = cursor.fetchone()
    cursor.close()
    conn.close()

    if account:
        if account['status'] == 1:
            return render_template('user/login.html', msg='Your account has been blocked by admin')

        session['user_id'] = account['user_id']
        session['user_name'] = account['user_name']
        session['user_email'] = account['user_email']
        session['status'] = account['status']
        return redirect(url_for('home'))
    else:
        return render_template('user/login.html', msg="Incorrect email or password")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------------
# TASK MANAGEMENT ROUTES
# -------------------------

# NEW: This is the route your navbar expects → fixes the 500 error!
@app.route('/pending_tasks')
def pending_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s AND status=0 ORDER BY due_date ASC", (session['user_id'],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user/all_tasks.html', data=data)  # reuse the same template

# Optional: also make /tasks point to pending tasks (nice URL)
@app.route('/tasks')
def tasks():
    return redirect(url_for('pending_tasks'))

@app.route('/all_tasks')
def all_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY due_date ASC", (session['user_id'],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user/all_tasks.html', data=data)

@app.route('/completed_tasks')
def completed_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s AND status=1 ORDER BY due_date ASC", (session['user_id'],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user/all_tasks.html', data=data)

@app.route('/view_task', methods=['POST'])
def view_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_text = request.form['Task_name']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s AND task_title LIKE %s ORDER BY due_date ASC",
                   (session['user_id'], f"%{search_text}%"))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user/view_task.html', data=data)

@app.route('/add_task')
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user/add_task.html')

@app.route('/add_task_process', methods=['POST'])
def add_task_process():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (user_id, task_title, task_description, due_date, created_date, priority, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, 0)",
        (session['user_id'], request.form['task_title'], request.form['task_description'],
         request.form['due_date'], date.today(), request.form['priority'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Task added successfully!")
    return redirect(url_for('home'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id=%s AND user_id=%s", (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Task deleted!")
    return redirect(url_for('all_tasks'))

@app.route('/complete_task/<int:task_id>')  # Renamed for clarity
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status=1 WHERE task_id=%s AND user_id=%s", (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Task marked as complete!")
    return redirect(url_for('all_tasks'))

# Keep old route for backward compatibility (optional)
@app.route('/complete_tasks/<int:task_id>')
def complete_tasks(task_id):
    return complete_task(task_id)

# -------------------------
# ADMIN PANEL (unchanged, only small formatting)
# -------------------------
# ... (your admin routes remain exactly the same)

# [All your admin routes from /login2 to /task_detail stay 100% the same]
# I didn’t paste them again to save space, but they are fine as-is.

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  # Better for Railway
