from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL config
DB_CONFIG = {
    'user': 'root',
    'password': '',  # Set your MySQL root password here
    'host': 'localhost',
    'database': 'MC_ride',
    'raise_on_warnings': True
}


def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            # Create database if not exists
            temp_config = DB_CONFIG.copy()
            temp_config.pop('database')
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            cursor.execute('CREATE DATABASE MC_ride')
            conn.commit()
            cursor.close()
            conn.close()
            DB_CONFIG['database'] = 'MC_ride'
            return mysql.connector.connect(**DB_CONFIG)
        else:
            raise


def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)
    # Rides table (without driver)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rides(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            origin VARCHAR(255) NOT NULL,
            destination VARCHAR(255) NOT NULL,
            ride_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()





@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            flash('Username already exists!', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username=%s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('landing'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])


@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO rides (user_id, origin, destination) VALUES (%s, %s, %s)',
            (session['user_id'], origin, destination)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Ride booked successfully!', 'success')
        return redirect(url_for('history'))

    return render_template('book.html')


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT origin, destination, ride_time FROM rides WHERE user_id=%s ORDER BY ride_time DESC',
        (session['user_id'],)
    )
    rides = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('history.html', rides=rides)


if __name__ == '__main__':
    app.run(debug=True)
