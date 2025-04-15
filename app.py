import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    department = db.Column(db.String(50))
    level = db.Column(db.String(10))
    content = db.Column(db.Text)
    reply = db.Column(db.Text)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    department = request.form['department']
    level = request.form['level']
    content = request.form['content']
    feedback = Feedback(name=name, department=department, level=level, content=content)
    db.session.add(feedback)
    db.session.commit()
    flash(f"Feedback submitted! Your index number is: {feedback.id}")
    return redirect(url_for('index'))

@app.route('/view_feedback')
def view_feedback():
    feedbacks = Feedback.query.all()
    return render_template('view_feedback.html', feedbacks=feedbacks)

@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        staff = Staff.query.filter_by(username=username).first()
        if staff and check_password_hash(staff.password, password):
            session['staff_id'] = staff.id
            return redirect(url_for('staff_dashboard'))
        else:
            flash('Invalid login credentials')
    return render_template('staff_login.html')

@app.route('/staff/register', methods=['GET', 'POST'])
def staff_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash("Passwords do not match")
            return redirect(url_for('staff_register'))
        if Staff.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('staff_register'))
        hashed_pw = generate_password_hash(password)
        new_staff = Staff(username=username, password=hashed_pw)
        db.session.add(new_staff)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for('staff_login'))
    return render_template('staff_register.html')

@app.route('/staff/dashboard')
def staff_dashboard():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    feedbacks = Feedback.query.all()
    return render_template('staff_dashboard.html', feedbacks=feedbacks)

@app.route('/staff/logout')
def staff_logout():
    session.pop('staff_id', None)
    flash("Logged out successfully")
    return redirect(url_for('staff_login'))

@app.route('/reply/<int:feedback_id>', methods=['POST'])
def reply(feedback_id):
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.reply = request.form['reply']
    db.session.commit()
    flash("Reply sent.")
    return redirect(url_for('staff_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
