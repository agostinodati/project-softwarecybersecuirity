import configparser
import datetime
from datetime import timedelta
from hashlib import sha256

import flask
import mysql.connector
from flask import request, session, redirect, render_template, escape

import blockchain_manager

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
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    return render_template('event_manager.html')


# Reseller's page
@app.route("/reseller")
def reseller():
    if session.get('role') != 'reseller' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    return render_template('reseller.html')


# Validator's page
@app.route("/validator")
def validator():
    if session.get('role') != 'validator' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    return render_template('validator.html')


# Buyer's page
@app.route("/buyer")
def buyer():
    if session.get('role') != 'buyer' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
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

@app.route("/logout")
def logout():
    session['logged_in'] = False;
    return render_template('/login.html')

@app.route("/back")
def back():
    if session['logged_in'] == False:
        return redirect('/login.html')
    elif session['role'] == 'event_manager':
        return redirect('/event_manager')
    elif session['role'] == 'reseller':
        return redirect('/reseller')
    elif session['role'] == 'validator':
        return redirect('/validator')
    elif session['role'] == 'buyer':
        return redirect('/buyer')

# Event Creation page
@app.route("/event_creation")
def event_creation():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    return render_template('event_creation.html')

# Create Event
@app.route("/event_create", methods=['POST'])
def event_create():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)

    name_event = str(escape(request.form['input_name']))
    date_event_str = str(escape(request.form['input_date']))
    seats_event = escape(request.form['input_available_seats'])

    ticket_price = escape(request.form['input_ticket_price'])

    # Control on input data
    date_event_datetime = datetime.datetime.strptime(date_event_str, '%Y-%m-%d').date()
    if date_event_datetime < datetime.date.today():
        return render_template('event_creation.html', error='Select a future date.')
    try:
        seats_event = int(seats_event)
    except Exception as e:
        return render_template('event_creation.html', error='Available seats must be an integer value.')
    try:
        ticket_price = int(ticket_price)
    except Exception as e:
        return render_template('event_creation.html', error='Ticket price must be an integer value.')

    # Deployment of the event's smart contract
    smart_contract_name, error = blockchain_manager.deploy_smart_contract_new_event(name_event, date_event_str,
                                                                                    seats_event, ticket_price, session['user'])

    # Check the output of deploy_smart_contract_new_event()
    if smart_contract_name is not None and error == 'No error':
        return render_template('event_creation.html', error='The event ' + smart_contract_name + ' add correctly.')
    else:
        return render_template('event_creation.html', error=error)



# Show all events for Event Manager
@app.route("/show_events_manager")
def show_events_manager():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    list_event_names = []

    # Extract name of events on the block chain from the dictionary created or read it from the local file.
    try:
        event_dict = blockchain_manager.get_smart_contracts_dict()
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict()
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_events_manager.html', error='Something went wrong.')

    return render_template('show_events_manager.html', event_names=list_event_names)



# Show all events for reseller
@app.route("/show_events")
def show_events():
    if session.get('role') != 'reseller' or session.get('logged_in') is False:
        return redirect("http://127.0.0.1:5000/single_event_seats/Bho", code=302)
    list_event_names = []

    # Extract name of events on the block chain from the dictionary created or read it from the local file.
    try:
        event_dict = blockchain_manager.get_smart_contracts_dict()
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict()
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_events.html', error='Something went wrong.')

    return render_template('show_events.html', event_names=list_event_names)

# Show the information page of the single event for the Event Manager
@app.route("/event_info_manager")
@app.route("/event_info_manager/<event_name>")
def event_info_manager(event_name):
    """
    Show the information about the event indicated.
    :param event_name: Event's name
    :return:
    """
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return render_template("login.html", error='Please, log in.')

    date, available_seats, ticket_price, e = blockchain_manager.get_event_information(session['user'], event_name)

    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile.
    return render_template('event_info_manager.html', event_name=event_name, event_date=date,
                           event_seats=available_seats, ticket_price=ticket_price)

# Show the information page of the single event
@app.route("/single_event_seats")
@app.route("/single_event_seats/<event_name>")
def single_event_seats(event_name):
    """
    Show the information about the event indicated and, eventually, allow to purchase seats.
    :param event_name: Event's name
    :return:
    """
    if session.get('role') != 'reseller' or session.get('logged_in') is False:
        return render_template("login.html", error='Please, log in.')
    date, available_seats, ticket_price, e = blockchain_manager.get_event_information(session['user'], event_name)
    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile.
    return render_template('single_event_seats.html', event_name=event_name, event_date=date,
                           event_seats=available_seats, ticket_price=ticket_price)


@app.route("/purchase_seats_event/<event_name>", methods=['POST'])
def purchase_seats_event(event_name):
    if session.get('role') != 'reseller' or session.get('logged_in') is False:
        return render_template("login.html", error='Please, log in.')

    date, available_seats, ticket_price, e = blockchain_manager.get_event_information(session['user'], event_name)
    seats_purchase = int(escape(request.form['input_seats']))

    # Check if the number of the seats is an integer greater then 0.
    if seats_purchase <= 0:
        return render_template('single_event_seats.html', error='Insert an integer value greater then 0.', event_name=event_name,
                               event_date=date, event_seats=available_seats, ticket_price=ticket_price)
    diff = available_seats - seats_purchase

    # Check if the difference between available seats and the value inserted by the reseller is a valid value.
    if diff < 0:
        return render_template('single_event_seats.html', error='Insufficient available seats.',
                               event_name=event_name,
                               event_date=date, event_seats=available_seats,ticket_price=ticket_price)

    # Make the "purchase"
    e_purchase = blockchain_manager.purchase_seats(session['user'], event_name, seats_purchase)

    date, available_seats, e = blockchain_manager.get_event_information(session['user'], event_name)

    if e_purchase is None:
        return render_template('single_event_seats.html', error='Seats purchased successfully.', event_name=event_name,
                               event_date=date, event_seats=available_seats, ticket_price=ticket_price)
    else:
        return render_template('single_event_seats.html', error=e_purchase, event_name=event_name,
                               event_date=date, event_seats=available_seats, ticket_price=ticket_price)


if __name__ == "__main__":
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.secret_key = 'secret password'  # It should be modified, used to decode the session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Session's timeout
    app.run()
