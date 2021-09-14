import configparser
from datetime import timedelta
from hashlib import sha256

import flask
import mysql.connector
from flask import request, session, redirect, render_template, escape

app = flask.Flask(__name__)

# Connect to the database
config = configparser.ConfigParser()
config.read('config.ini')

database = mysql.connector.connect(
    host=config['DB']['host'],
    user=config['DB']['user'],
    passwd=config['DB']['password'],
    database=config['DB']['database']
)


# Homepage
@app.route("/")
def main():
    return render_template('index.html')


# Login
@app.route("/login")
def login():
    return render_template('login.html')


# Event Manager's page
@app.route("/event_manager")
def event_manager():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("https://www.youtube.com/watch?v=HO8ctP_QNZc&ab_channel=LEZZO", code=302)
    return render_template('event_manager.html')


# Reseller's page
@app.route("/reseller")
def reseller():
    if session.get('role') != 'reseller' or session.get('logged_in') is False:
        return redirect("https://www.youtube.com/watch?v=HO8ctP_QNZc&ab_channel=LEZZO", code=302)
    return render_template('reseller.html')


# Validator's page
@app.route("/validator")
def validator():
    if session.get('role') != 'validator' or session.get('logged_in') is False:
        return redirect("https://www.youtube.com/watch?v=HO8ctP_QNZc&ab_channel=LEZZO", code=302)
    return render_template('validator.html')


# Buyer's page
@app.route("/buyer")
def buyer():
    if session.get('role') != 'buyer' or session.get('logged_in') is False:
        return redirect("https://www.youtube.com/watch?v=HO8ctP_QNZc&ab_channel=LEZZO", code=302)
    return render_template('buyer.html')


# Validate the data of login
@app.route("/validate_login", methods=['POST'])
def validate_login():
    cursor = database.cursor()
    username = str(escape(request.form['input_username']))
    password = str(escape(request.form['input_password']))
    hash_password = sha256(
        password.encode('utf-8')).hexdigest()  # Calculate the hash of the password for integrity's reason

    # To prevent SQL Injection are used both escape method (that remove character like ', ", < ecc) and then
    # sanitized the query passing the values as safe parameters
    cursor.execute("""
                    SELECT 
                        username, password, role 
                    FROM 
                        users 
                    WHERE 
                        username = %(username)s AND password = SHA2(%(password)s,256)""",
                   {
                       'username': username,
                       'password': password
                   })
    result = cursor.fetchone()

    if result is not None:
        if username == result[0] and hash_password == result[1]:
            session['logged_in'] = True
            session['user'] = result[0]
            session['password'] = result[1]
            session['role'] = result[2]
            if session['role'] == 'event_manager':
                return redirect('/event_manager')
            elif session['role'] == 'reseller':
                return redirect('/reseller')
            elif session['role'] == 'validator':
                return redirect('/validator')
            elif session['role'] == 'buyer':
                return redirect('/buyer')
        else:
            # If there are problems with the credentials, return an error in the login page.
            return render_template('login.html', error='The credentials entered are incorrect. Try again.')
    else:
        # If the user does not exists return an error.
        # This error is generic to avoid to give too much information to an attacker.
        return render_template('login.html', error='The credentials entered are incorrect. Try again.')


# Event Creation page
@app.route("/event_creation")
def event_creation():
    return render_template('event_creation.html')


# Create Event
@app.route("/event_create", methods=['POST'])
def create_event():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("https://www.youtube.com/watch?v=HO8ctP_QNZc&ab_channel=LEZZO", code=302)
    # TODO: Bisogna interfacciare il sito con la blockchain. In particolare, bisogna compilare lo Smart Contract,
    #  farne il deploy con i dati inseriti dall'Event Man., ottenere l'indirizzo (salvarlo in una lista da
    #  condividere con tutti con getter e setter) e poi usare quell'indirizzo per ottenere i dati nella sezione dgli
    #  eventi disponibili del reseller.
    event_name = str(escape(request.form['input_name']))
    event_date = str(escape(request.form['input_date']))
    event_seats = str(escape(request.form['input_availableseats']))


if __name__ == "__main__":
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.secret_key = 'secret password'  # It should be modified, used to decode the session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)  # Session's timeout
    app.run()
