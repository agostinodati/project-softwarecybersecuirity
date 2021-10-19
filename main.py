import configparser
import datetime
from datetime import timedelta
from hashlib import sha256

import flask
import mysql.connector
from flask import request, session, redirect, render_template, escape, url_for

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
    try:
        messages = request.args['messages']
    except:
        messages = ""
    return render_template('login.html', error=messages)


# Event Manager's page
@app.route("/event_manager")
def event_manager():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'event_manager':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        messages = request.args['messages']
    except:
        messages = ""
    return render_template('event_manager.html', error=messages)


# Reseller's page
@app.route("/reseller")
def reseller():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        messages = request.args['messages']
    except:
        messages = ""
    return render_template('reseller.html', error=messages)


# Validator's page
@app.route("/validator")
def validator():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'validator':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        messages = request.args['messages']
    except:
        messages = ""
    return render_template('validator.html', error=messages)


# Buyer's page
@app.route("/buyer")
def buyer():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        messages = request.args['messages']
    except:
        messages = ""
    return render_template('buyer.html', error=messages)


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
                return redirect(url_for('event_manager'))
            elif session['role'] == 'reseller':
                return redirect(url_for('reseller'))
            elif session['role'] == 'validator':
                return redirect(url_for('validator'))
            elif session['role'] == 'buyer':
                return redirect(url_for('buyer'))
        else:
            # If there are problems with the credentials, return an error in the login page.
            return redirect(url_for('login', messages='The credentials entered are incorrect. Try again.'))
    else:
        # If the user does not exists return an error.
        # This error is generic to avoid to give too much information to an attacker.
        return redirect(url_for('login', messages='The credentials entered are incorrect. Try again.'))


@app.route("/logout")
def logout():
    session['logged_in'] = False;
    return redirect(url_for("login", messages="Successfully logged out!"))


@app.route("/back")
def back():
    try:
        if session['role'] == 'event_manager':
            return redirect(url_for('event_manager'))
        elif session['role'] == 'reseller':
            return redirect(url_for('reseller'))
        elif session['role'] == 'validator':
            return redirect(url_for('validator'))
        elif session['role'] == 'buyer':
            return redirect(url_for('buyer'))
    except:
        return redirect(url_for('login', messages="Please log in."))


# Event Creation page
@app.route("/event_creation")
def event_creation():
    if session.get('role') != 'event_manager' or session.get('logged_in') is False:
        return redirect("login", code=302)
    return render_template('event_creation.html')


# Create Event
@app.route("/event_creation", methods=['POST'])
def event_create():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'event_manager':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    name_event = str(escape(request.form['input_name']))
    date_event_str = str(escape(request.form['input_date']))
    hour_event_str = str(escape(request.form['input_hours']))

    artist_event = str(escape(request.form['input_artist']))
    location_event = str(escape(request.form['input_location']))
    description_event = str(escape(request.form['input_description']))

    seats_event = escape(request.form['input_available_seats'])
    seats_price = escape(request.form['input_seats_price'])

    # Control on input data
    date_event_datetime = datetime.datetime.strptime(date_event_str, '%Y-%m-%d').date()
    if date_event_datetime < datetime.date.today():
        return render_template('event_creation.html', error='Select a future date.')
    try:
        seats_event = int(seats_event)
    except Exception as e:
        return render_template('event_creation.html', error='Available seats must be an integer value.')
    try:
        seats_price = int(seats_price)
    except Exception as e:
        return render_template('event_creation.html', error='Ticket price must be an integer value.')

    date_event_str = date_event_str + '+' + hour_event_str

    # Deployment of the event's smart contract
    try:
        smart_contract_name, error = blockchain_manager.deploy_smart_contract_new_event(name_event, date_event_str,
                                                                                        seats_event, seats_price,
                                                                                        artist_event, location_event,
                                                                                        description_event,
                                                                                        session['user'])
    except:
        return redirect(url_for("event_manager", messages='Network is offline, please try again in another moment...'))

    # Check the output of deploy_smart_contract_new_event()
    if smart_contract_name is not None and error == 'No error':
        return render_template('event_creation.html', error='The event ' + smart_contract_name + ' add correctly.')
    else:
        return render_template('event_creation.html', error=error)


# Show all events for Event Manager
@app.route("/show_events_manager")
def show_events_manager():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'event_manager':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    list_event_names = []

    # Extract name of events on the block chain from the dictionary created or read it from the local file.
    try:
        event_dict = blockchain_manager.get_smart_contracts_dict("event")
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict("event")
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_events_manager.html', error=e)

    if len(list_event_names) == 0:
        return render_template('show_events_manager.html', error='There are no events currently listed.')

    return render_template('show_events_manager.html', event_names=list_event_names)


# Show all events for reseller
@app.route("/show_events")
def show_events():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
        # return render_template("/login.html", error="Acess denied.")

    mode = "purchase"
    list_event_names = []

    # Extract name of events on the block chain from the dictionary created or read it from the local file.
    try:
        event_dict = blockchain_manager.get_smart_contracts_dict("event")
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict("event")
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_events.html', mode=mode, error=e)

    if len(list_event_names) == 0:
        return render_template('show_events.html', mode=mode, error='There are no events currently listed.')

    return render_template('show_events.html', mode=mode, event_names=list_event_names)


# Show the information page of the single event for the Event Manager
@app.route("/event_info_manager")
@app.route("/event_info_manager/<event_name>")
def event_info_manager(event_name):
    """
    Show the information about the event indicated.
    :param event_name: Event's name
    :return:
    """
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'event_manager':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
    except:
        return redirect(url_for('event_manager', messages='Network is offline, please try again in another moment...'))

    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile.

    try:
        x = date.split("+")
    except:
        x = [None, None]

    return render_template('event_info_manager.html', event_name=event_name, event_date=x[0], event_hours=x[1],
                           event_seats=available_seats, seats_price=seats_price, event_artist=artist,
                           event_location=location, event_description=description)


# Show the information page of the single event
@app.route("/single_event_seats")
@app.route("/single_event_seats/<event_name>")
def single_event_seats(event_name):
    """
    Show the information about the event indicated and, eventually, allow to purchase seats.
    :param event_name: Event's name
    :return:
    """
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
    except:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...'))

    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile. FARE ATTENZIONE AI DOPPI ACQUISTI, VENGONO ISTANZIATI DUE SMART CONTRACT DELLE BIGLIETTERIE

    try:
        x = date.split("+")
    except:
        x = [None, None]
    mode = "purchase"
    return render_template('single_event_seats.html', mode=mode, event_name=event_name, event_date=x[0], event_hours=x[1],
                           event_seats=available_seats, seats_price=seats_price, event_artist=artist,
                           event_location=location, event_description=description)


@app.route("/purchase_seats_event/<event_name>", methods=['POST'])
def purchase_seats_event(event_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
    except:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...'))

    seats_purchase = int(escape(request.form['input_seats']))
    new_ticket_price = int(escape(request.form['ticket_price']))

    try:
        x = date.split("+")
    except:
        x = [None, None]

    if seats_purchase <= 0:
        return render_template('single_event_seats.html', error='Insert an integer value greater then 0.',
                               event_name=event_name, event_date=x[0], event_hours=x[1],
                               event_seats=available_seats, seats_price=seats_price, event_artist=artist,
                               event_location=location, event_description=description)
    diff = available_seats - seats_purchase

    # Check if the difference between available seats and the value inserted by the reseller is a valid value.
    if diff < 0:
        return render_template('single_event_seats.html', error='Insufficient available seats.', event_name=event_name,
                               event_date=x[0], event_hours=x[1], event_seats=available_seats,
                               seats_price=seats_price,
                               event_artist=artist, event_location=location, event_description=description)

    # Make the "purchase"
    error_purchase = blockchain_manager.purchase_seats(session['user'], event_name, seats_purchase)

    date, available_seats, ticket_price, artist, location, description, e = blockchain_manager.get_event_information(
        session['user'], event_name)

    try:
        x = date.split("+")
    except:
        x = [None, None]

    mode = "purchase"

    if error_purchase is None:
        address_event, abi = blockchain_manager.get_address_abi(event_name, "event")

        dict_ticket, error_ticket = blockchain_manager.deploy_ticket(event_name, address_event, new_ticket_price, seats_purchase)

        if error_ticket is None:
            return render_template('single_event_seats.html', mode=mode, error='Seats purchased successfully.',
                                   event_name=event_name,
                                   event_date=x[0], event_hours=x[1], event_seats=available_seats,
                                   ticket_price=new_ticket_price,
                                   event_artist=artist, event_location=location, event_description=description)
        else:
            return render_template('single_event_seats.html', mode=mode, error=error_ticket, event_name=event_name,
                                   event_date=x[0],
                                   event_hours=x[1], event_seats=available_seats, ticket_price=ticket_price,
                                   event_artist=artist, event_location=location, event_description=description)

    else:
        return render_template('single_event_seats.html', mode=mode, error=error_purchase, event_name=event_name, event_date=x[0],
                               event_hours=x[1], event_seats=available_seats, ticket_price=ticket_price,
                               event_artist=artist, event_location=location, event_description=description)


# Show all events purchased for reseller
@app.route("/show_events_purchased_reseller")
def show_events_purchased_reseller():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    mode = "show"
    list_event_names = []

    try:
        list_event_names, error = blockchain_manager.get_reseller_events()
        #print(len(list_event_names))
    except Exception as e:
        render_template('show_events.html', error=e)

    if (len(list_event_names) == 0):
        return render_template('show_events.html', mode=mode, event_names=list_event_names,
                               error='No seats have been purchased.')

    if error is None:
        return render_template('show_events.html', mode=mode, event_names=list_event_names)
    else:
        return render_template('show_events.html', mode=mode, error='Something went wrong.\nError: ' + str(error))


# Show the information page of the single event
@app.route("/single_event_tickets")
@app.route("/single_event_tickets/<event_name>")
def single_event_tickets(event_name):
    """
    Show the information about the event indicated.
    :param event_name: Event's name
    :return:
    """
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'reseller':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        date, available_seats, ticket_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
    except:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...'))

    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile.

    try:
        x = date.split("+")
    except:
        x = [None, None]

    total_tickets = blockchain_manager.get_reseller_tickets_for_event(event_name)
    ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_info(event_name)
    tickets_sold = total_tickets - ticket_remaining

    mode = "show"

    if e is None:
        return render_template('single_event_seats.html', mode=mode, event_name=event_name, event_date=x[0], event_hours=x[1], available_seats=available_seats,
                           available_tickets=ticket_remaining, ticket_price=ticket_p, tickets_sold=tickets_sold, event_artist=artist,
                           event_location=location, event_description=description, error="")
    else:
        return render_template('single_event_seats.html', mode=mode, event_name=event_name, event_date=x[0],
                               event_hours=x[1], available_seats=available_seats,
                               available_tickets=ticket_remaining, ticket_price=ticket_p, event_artist=artist,
                               event_location=location, event_description=description, error=e)

# Show the event list for the buyer
@app.route("/show_events_buyer")
def show_events_buyer():
    """
        Show the events for the buyer.
        :param event_name: Event's name
        :return:
        """
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    list_event_names = []

    # Extract name of events on the block chain from the dictionary created or read it from the local file.
    try:
        event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_events_buyer.html', error=e)

    if len(list_event_names) == 0:
        return render_template('show_events_buyer.html', error='There are no events currently listed.')

    return render_template('show_events_buyer.html', event_names=list_event_names)

# Show the information page for buying the ticket (buyer)
@app.route("/event_info")
@app.route("/event_info/<event_name>")
def event_info(event_name):
    """
        Show the events for the buyer.
        :param event_name: Event's name
        :return:
        """
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        date, available_seats, ticket_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
    except:
        return redirect(url_for('buyer', messages='Network is offline, please try again in another moment...'))

    # TODO: Controllo su data (se passata, rendere l'evento non acquistabile) e posti disponibili (se esauriti,
    #  rendere l'evento non acquistabile.

    try:
        x = date.split("+")
    except:
        x = [None, None]

    #available_tickets = blockchain_manager.get_reseller_tickets_for_event(event_name)
    ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_info(event_name)

    if e is None:
        return render_template('event_info.html', event_name=event_name, event_date=x[0],
                               event_hours=x[1],
                               available_tickets=ticket_remaining, tickets_price=ticket_p, event_artist=artist,
                               event_location=location, event_description=description, error="")
    else:
        return render_template('event_info.html', event_name=event_name, event_date=x[0],
                               event_hours=x[1],
                               available_tickets=ticket_remaining, seats_price=ticket_p, event_artist=artist,
                               event_location=location, event_description=description, error=e)

@app.route("/purchase_tickets_event/<event_name>", methods=['POST'])
def purchase_tickets_event(event_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)

        #available_tickets = blockchain_manager.get_reseller_tickets_for_event(event_name)
        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_info(event_name)

    except:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...'))

    tickets_purchase = int(escape(request.form['input_tickets']))

    try:
        x = date.split("+")
    except:
        x = [None, None]

    if tickets_purchase <= 0:
        return render_template('event_info.html', error='Insert an integer value greater then 0.',
                               event_name=event_name, event_date=x[0], event_hours=x[1],
                               available_tickets=ticket_remaining, tickets_price=ticket_p, event_artist=artist,
                               event_location=location, event_description=description)

    diff = ticket_remaining - tickets_purchase

    # Check if the difference between available seats and the value inserted by the reseller is a valid value.
    if diff < 0:
        return render_template('event_info.html', error='Insufficient available tickets.', event_name=event_name,
                               event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                               tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)

    # Make the "purchase"
    error_purchase = blockchain_manager.purchase_ticket(session['user'], event_name, tickets_purchase)

    if error_purchase is None:
        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_info(event_name)
        return render_template('event_info.html', error='Tickets bought correctly.', event_name=event_name,
                               event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                               tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)
    else:
        return render_template('event_info.html', error=error_purchase, event_name=event_name,
                               event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                               tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)

if __name__ == "__main__":
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.secret_key = 'secret password'  # It should be modified, used to decode the session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Session's timeout
    app.run()
