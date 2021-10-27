import configparser
import datetime
import os.path
import time
from datetime import timedelta
from hashlib import sha256
from random import seed
from random import randint

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

    smart_contract_name, error = blockchain_manager.deploy_smart_contract_new_event("Evento Scaduto", "2020-10-12+00:00",
                                                                                        100, 10,
                                                                                        "Artist", "Location",
                                                                                        "Description",
                                                                                        session['user'])
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

    # Control on name
    path_smartcontracts = blockchain_manager.smart_contract_local
    if os.path.isfile(path_smartcontracts):
        all_events = blockchain_manager.get_smart_contracts_dict("event")
        is_populated = bool(all_events)
        if is_populated is True:
            if name_event in all_events.keys():
                return render_template('event_creation.html', error='The name "' + name_event + '" already exists. '
                                                                                                 '\nPlease, change name.')

    # Deployment of the event's smart contract
    try:
        smart_contract_name, error = blockchain_manager.deploy_smart_contract_new_event(name_event, date_event_str,
                                                                                        seats_event, seats_price,
                                                                                        artist_event, location_event,
                                                                                        description_event,
                                                                                        session['user'])
        event_state, e = blockchain_manager.get_event_state(name_event, session['user'])
    except:
        return redirect(url_for("event_manager", messages='Network is offline, please try again in another moment...'))

    # Check the output of deploy_smart_contract_new_event()
    if smart_contract_name is not None and error == 'No error':

        try:
            x = date_event_str.split("+")
        except:
            x = [None, None]

        return render_template('event_info_manager.html', error='The event "' + smart_contract_name + '" was added correctly.', event_name=name_event, event_date=x[0], event_hours=x[1],
                           event_seats=seats_event, seats_price=seats_price, event_artist=artist_event,
                           event_location=location_event, event_description=description_event, state=event_state)
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
        event_state, e = blockchain_manager.get_event_state(event_name, session['user'])
    except:
        return redirect(url_for('event_manager', messages='Network is offline, please try again in another moment...'))

    try:
        x = date.split("+")
    except:
        x = [None, None]

    date_datetime = datetime.datetime.strptime(x[0], '%Y-%m-%d').date()
    if date_datetime <= datetime.date.today():
        blockchain_manager.set_event_state(event_name, "expired", session['user'])
        blockchain_manager.set_tickets_state(event_name, "obliterated", session['user'])
        event_state, e = blockchain_manager.get_event_state(event_name, session['user'])
        render_template('event_info_manager.html', error="The event is expired.", event_name=event_name, event_date=x[0], event_hours=x[1],
                        event_seats=available_seats, seats_price=seats_price, event_artist=artist,
                        event_location=location, event_description=description, state=event_state)

    return render_template('event_info_manager.html', event_name=event_name, event_date=x[0], event_hours=x[1],
                           event_seats=available_seats, seats_price=seats_price, event_artist=artist,
                           event_location=location, event_description=description, state=event_state)


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

    try:
        total_tickets = blockchain_manager.get_reseller_tickets_for_event(event_name, session['user'])
        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
        tickets_sold = total_tickets - ticket_remaining
    except:
        ticket_remaining = available_seats
        tickets_sold = 0
    try:
        x = date.split("+")
    except Exception as error_date:
        return render_template('single_event_seats.html', mode="show", error="Error on date: " + str(error_date),
                               event_hours=None, event_date=None, event_artist=artist, event_name=event_name,
                               available_tickets=ticket_remaining, ticket_price=seats_price,
                               event_location=location, event_description=description, tickets_sold=tickets_sold)

    date_datetime = datetime.datetime.strptime(x[0], '%Y-%m-%d').date()

    event_already_purchased, err = blockchain_manager.has_event(event_name, session['user'])
    event_state, err = blockchain_manager.get_event_state(event_name, session['user'])

    if event_already_purchased is False:
        if event_state == "available":
            if date_datetime <= datetime.date.today():
                blockchain_manager.set_event_state(event_name, "expired", session['user'])
                blockchain_manager.set_tickets_state(event_name, "obliterated", session['user'])

                return render_template('single_event_seats.html', mode="show", error="Event expired.",
                                       event_hours=x[1], event_date=x[0], event_artist=artist, event_name=event_name,
                                       available_tickets=ticket_remaining, ticket_price=seats_price,
                                       event_location=location, event_description=description, tickets_sold=tickets_sold)

            mode = "purchase"
            return render_template('single_event_seats.html', mode=mode, event_name=event_name, event_date=x[0], event_hours=x[1],
                                   available_tickets=ticket_remaining, ticket_price=seats_price, event_artist=artist,
                                   event_location=location, event_description=description, tickets_sold=tickets_sold)
        elif event_state == "cancelled":
            return render_template('single_event_seats.html', mode="show", error="Event cancelled.", event_name=event_name,
                                   event_hours=x[1], event_date=x[0], event_artist=artist,
                                   available_tickets=ticket_remaining, ticket_price=seats_price,
                                   event_location=location, event_description=description, tickets_sold=tickets_sold)
        elif event_state == "expired":
            return render_template('single_event_seats.html', mode="show", error="Event expired.", event_name=event_name,
                                   event_hours=x[1], event_date=x[0], event_artist=artist,
                                   available_tickets=ticket_remaining, ticket_price=seats_price,
                                   event_location=location, event_description=description, tickets_sold=tickets_sold)
    else:
        return render_template('single_event_seats.html', mode="show", error="Event already purchased.",
                                event_name=event_name,
                                event_hours=x[1], event_date=x[0], event_artist=artist,
                                available_tickets=ticket_remaining, ticket_price=seats_price,
                                event_location=location, event_description=description, tickets_sold=tickets_sold)


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

    already_purchased = blockchain_manager.has_event(event_name, session['user'])

    if already_purchased is True:
        date, available_seats, ticket_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)

        try:
            x = date.split("+")
        except:
            x = [None, None]

        return render_template('single_event_seats.html', mode="show", error="Already purchased.", event_name=event_name,
                               event_date=x[0],
                               event_hours=x[1], event_seats=available_seats, seats_price=seats_price,
                               event_artist=artist, event_location=location, event_description=description)

    # Make the "purchase"
    event_state, err = blockchain_manager.get_event_state(event_name, session['user'])
    if event_state == "available":
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

            dict_ticket, error_ticket = blockchain_manager.deploy_ticket(event_name, address_event,
                                                                         new_ticket_price, seats_purchase, session['user'])

            if error_ticket is None:
                return render_template('single_event_seats.html', error='Seats purchased successfully.', mode="show",
                                       event_name=event_name,
                                       event_date=x[0],
                                       event_hours=x[1], available_tickets=seats_purchase, ticket_price=new_ticket_price,
                                       event_artist=artist, event_location=location, event_description=description, tickets_sold=0)
            else:
                return render_template('single_event_seats.html', mode=mode, error=error_ticket, event_name=event_name,
                                       event_date=x[0],
                                       event_hours=x[1], event_seats=available_seats, seats_price=seats_price,
                                       event_artist=artist, event_location=location, event_description=description)

        else:
            return render_template('single_event_seats.html', mode=mode, error=error_purchase, event_name=event_name,
                                   event_date=x[0], event_hours=x[1], event_seats=available_seats, seats_price=seats_price,
                                   event_artist=artist, event_location=location, event_description=description)
    else:
        date, available_seats, ticket_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)

        try:
            x = date.split("+")
        except:
            x = [None, None]

        return render_template('single_event_seats.html', mode="show", error="Event not available.",
                            event_name=event_name, event_date=x[0],
                            event_hours=x[1], event_seats=available_seats, seats_price=seats_price,
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
        list_event_names, error = blockchain_manager.get_reseller_events(session['user'])
    except Exception as e:
        render_template('show_events.html', error=e)

    if len(list_event_names) == 0:
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

    total_tickets = blockchain_manager.get_reseller_tickets_for_event(event_name, session['user'])
    ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
    tickets_sold = total_tickets - ticket_remaining

    mode = "show"

    if e is None:
        return render_template('single_event_seats.html', mode=mode, event_name=event_name, event_date=x[0],
                               event_hours=x[1], available_seats=available_seats, available_tickets=ticket_remaining,
                               ticket_price=ticket_p, tickets_sold=tickets_sold, event_artist=artist,
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

    ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])

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

        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
    except Exception as e:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...' + e))

    try:
        x = date.split("+")
    except Exception as e:
        x = [None, None]

    if ticket_remaining <= 0:
        return render_template('event_info.html', error='Insufficient available tickets.', event_name=event_name,
                               event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                               tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)

    # Check if the buyer already purchased a ticket for the event
    ticket_already_purchased, ticket_id, err = blockchain_manager.has_ticket(event_name, session['user'])

    # Simulate the payment success, if not render an error
    seed(time.time())
    payment_success = randint(0, 10)
    if payment_success <= 5:
        ticket_state, ticket_seal, ticket_date, error_info = blockchain_manager.get_ticket_info(event_name, ticket_id,
                                                                                                session['user'])
        return render_template('event_info.html', error='Purchase failed. Try again.',
                               event_name=event_name, event_date=x[0], event_hours=x[1],
                               available_tickets=ticket_remaining, tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)

    # Make the purchase
    if ticket_already_purchased is False:
        ticket_id, error_purchase = blockchain_manager.purchase_ticket(event_name, session['user'])
        ticket_state, ticket_seal, ticket_date, error_info = blockchain_manager.get_ticket_info(event_name, ticket_id,
                                                                                                session['user'])
        if error_purchase is None:
            ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
            if error_info is None:
                return render_template('ticket_info.html', event_name=event_name,
                                       event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                       tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                                       seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                                       event_location=location, event_description=description, error="Ticket purachsed successfully.")
            else:
                return render_template('ticket_info.html', error='Purchased correctly but error into getting info '
                                                                 'about ticket: ' + error_info, event_name=event_name,
                                       event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                       tickets_price=ticket_p,
                                       event_artist=artist, event_location=location, event_description=description)
        else:
            return render_template('event_info.html', error='Purchase failed. Try again.', event_name=event_name,
                                   event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                   tickets_price=ticket_p,
                                   event_artist=artist, event_location=location, event_description=description)
    else:
        return render_template('event_info.html', error='Purchase already made. You can\'t purchase more '
                                                        'than one ticket.',
                               event_name=event_name, event_date=x[0], event_hours=x[1],
                               available_tickets=ticket_remaining, tickets_price=ticket_p,
                               event_artist=artist, event_location=location, event_description=description)


@app.route("/show_tickets_list")
def show_tickets_list():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    list_tickets = []
    list_event_names = []

    try:
        event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_tickets_list.html', error=e)

    for event in list_event_names:
        purchased, ticket_id, err = blockchain_manager.has_ticket(event, session['user'])
        if purchased:
            list_tickets.append(event)

    if len(list_tickets) == 0:
        return render_template('show_tickets_list.html', error='There are no tickets purchased.')

    return render_template('show_tickets_list.html', event_names=list_tickets)


@app.route("/show_ticket/<event_name>")
def show_ticket(event_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'buyer':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)

        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
    except Exception as e:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...' + e))

    try:
        x = date.split("+")
    except Exception as e:
        x = [None, None]

    purchased, ticket_id, err = blockchain_manager.has_ticket(event_name, session['user'])
    ticket_state, ticket_seal, ticket_date, error_info = blockchain_manager.get_ticket_info(event_name, ticket_id,
                                                                                            session['user'])

    if err is None:
        if error_info is None:
            return render_template('ticket_info.html', event_name=event_name,
                                   event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                   tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                                   seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                                   event_location=location, event_description=description)
        else:
            return render_template('ticket_info.html', error=error_info, event_name=event_name,
                                   event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                   tickets_price=ticket_p,
                                   event_artist=artist, event_location=location, event_description=description)
    else:
        return render_template('buyer.html', error=err)

@app.route("/show_event_validator")
def show_event_validator():
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'validator':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    list_event_names = []

    try:
        event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
        if not event_dict:
            event_dict = blockchain_manager.get_smart_contracts_dict("ticket_office")
            event_dict = event_dict.keys()
        for key in event_dict:
            list_event_names.append(key)
    except Exception as e:
        return render_template('show_event_validator.html', error=e)

    if len(list_event_names) == 0:
        return render_template('show_event_validator.html', error='There are no events currently listed.')

    return render_template('show_event_validator.html', event_names=list_event_names)

@app.route("/show_ticket_list_validator")
@app.route("/show_ticket_list_validator/<event_name>")
def show_ticket_list_validator(event_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'validator':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    list_ticket = []

    try:
        list, e = blockchain_manager.getTicketList(event_name, session['user'])
        for t in list:
            list_ticket.append(t[5])
    except Exception as e:
        return render_template('show_ticket_list_validator.html', error=e)

    if len(list_ticket) == 0:
        return render_template('show_ticket_list_validator.html', error='There are no tickets currently bought.')

    return render_template('show_ticket_list_validator.html', ticket_list=list_ticket, event_name=event_name)

@app.route("/validate_ticket")
@app.route("/validate_ticket/<event_name>/<buyer_name>")
def validate_ticket(event_name, buyer_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'validator':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))
    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)

        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])
    except Exception as e:
        return redirect(url_for('reseller', messages='Network is offline, please try again in another moment...' + e))

    try:
        x = date.split("+")
    except Exception as e:
        x = [None, None]

    purchased, ticket_id, err = blockchain_manager.has_ticket(event_name, buyer_name)
    ticket_state, ticket_seal, ticket_date, error_info = blockchain_manager.get_ticket_info(event_name, ticket_id,
                                                                                            session['user'])
    print(ticket_id)
    print(err)
    print(error_info)
    return render_template("validate_ticket.html", event_name=event_name,
                                   event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                   tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                                   seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                                   event_location=location, event_description=description, buyer_name=buyer_name)

@app.route("/validate/<event_name>/<buyer_name>", methods=['POST'])
def validate(event_name, buyer_name):
    if session.get('logged_in') is False:
        return redirect(url_for("login", messages="Please log in."))
    elif session.get('role') != 'validator':
        session['logged_in'] = False
        return redirect(url_for("login", messages="Access denied."))

    try:
        date, available_seats, seats_price, artist, location, description, e = blockchain_manager.get_event_information(
            session['user'], event_name)
        ticket_p, ticket_remaining, e = blockchain_manager.get_ticket_office_info(event_name, session['user'])

        purchased, ticket_id, err = blockchain_manager.has_ticket(event_name, buyer_name)

        e = blockchain_manager.set_ticket_state(event_name, ticket_id, "obliterated", session['user'])
    except Exception as err:
        return redirect(url_for('validator', messages='Network is offline, please try again in another moment...' + err))

    try:
        x = date.split("+")
    except Exception as e:
        x = [None, None]

    ticket_state, ticket_seal, ticket_date, error_info = blockchain_manager.get_ticket_info(event_name, ticket_id,
                                                                                            session['user'])

    if (e is None):
        if (err is None):
            return render_template("validate_ticket.html", event_name=event_name,
                                   event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                                   tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                                   seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                                   event_location=location, event_description=description,error="Ticket obliterated successfully.")
        else:
            return render_template("validate_ticket.html", event_name=event_name,
                               event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                               tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                               seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                               event_location=location, event_description=description,
                               error=err)
    return render_template("validate_ticket.html", event_name=event_name,
                           event_date=x[0], event_hours=x[1], available_tickets=ticket_remaining,
                           tickets_price=ticket_p, ticket_id=ticket_id, state=ticket_state,
                           seal=ticket_seal, timestamp=ticket_date, event_artist=artist,
                           event_location=location, event_description=description,
                           error=e)


if __name__ == "__main__":
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.secret_key = 'secret password'  # It should be modified, used to decode the session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Session's timeout
    app.run()
