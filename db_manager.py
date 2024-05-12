from sqlite3 import connect
from bcrypt import gensalt, hashpw, checkpw
import xml.etree.ElementTree as ET
from random import uniform
from requests import get
from os import getenv
from re import compile

con = connect('system.db', check_same_thread=False)
cur = con.cursor()

URL = 'https://timetable-lookup.p.rapidapi.com/TimeTable/{_from}/{to}/{date}/'

HEADERS = {
    "X-RapidAPI-Key": getenv('flight_search_api_key'),
    "X-RapidAPI-Host": "timetable-lookup.p.rapidapi.com"
}

def regexp(expr, item):
    reg = compile(expr)
    return reg.search(item) is not None

con.create_function("REGEXP", 2, regexp)

def create_users():
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT NOT NULL,
		password TEXT NOT NULL,
		email TEXT NOT NULL,
		status TEXT NOT NULL,
		pfp TEXT NOT NULL,
		dob TEXT NOT NULL,
	)''')
    con.commit()


def create_flight():
    cur.execute('''CREATE TABLE IF NOT EXISTS flight (
        id INTEGER PRIMARY KEY,
        total_trip_time TEXT NOT NULL,
        total_miles INTEGER NOT NULL,
        flight_type TEXT NOT NULL,
        number_legs INTEGER NOT NULL,
        price TEXT NOT NULL
    )''')
    con.commit()


def create_flight_leg():
    cur.execute('''CREATE TABLE IF NOT EXISTS flight_leg (
		id INTEGER,
		departure_datetime TEXT NOT NULL,
		departure_timeoffset INTEGER NOT NULL,
		arrival_datetime TEXT NOT NULL,
		arrival_timeoffset INTEGER NOT NULL,
		flight_number TEXT NOT NULL,
        journey_duration TEXT NOT NULL,
        sequence_number INTEGER NOT NULL,
        leg_distance INTEGR NOT NULL,
		departure_airport TEXT NOT NULL,
		arrival_airport TEXT NOT NULL,
        departure_terminal INTEGER NOT NULL,
        arrival_terminal INTEGER NOT NULL,
        airline_code TEXT NOT NULL,
        airline_name TEXT NOT NULL,

        foreign key (departure_airport) references airport (location_code),
        foreign key (arrival_airport) references airport (location_code),
        foreign key (id) references flight (id)
    )''')
    con.commit()


def create_airport():
    cur.execute('''CREATE TABLE IF NOT EXISTS airport (
        location_code TEXT PRIMARY KEY,
        location_name TEXT NOT NULL
    )''')
    con.commit()


def create_bookings():
    cur.execute('''CREATE TABLE IF NOT EXISTS bookings (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		flight_id INTEGER NOT NULL,
        user_id INTEGER,
		status TEXT NOT NULL,
		FOREIGN KEY (flight_id) REFERENCES flights(id)
	)''')
    con.commit()

def create_passengers():
	cur.execute('''CREATE TABLE IF NOT EXISTS passengers (
		id INTEGER,
		fname TEXT NOT NULL,
		lname TEXT NOT NULL,
		dob DATE NOT NULL,
		gender TEXT NOT NULL,
		nationality TEXT NOT NULL
	)''')
	con.commit()

def create_contacts():
    cur.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY,
        contact_name TEXT NOT NULL,
        ic_num TEXT NOT NULL,
        email TEXT NOT NULL,
        phone_no TEXT NOT NULL
    )''')
    con.commit()

def hash_password(password):
    encode = password.encode('utf-8')
    salt = gensalt()
    hash_pass = hashpw(encode, salt)

    return hash_pass


def add_user(username, password, email, pfp):
    hash_pass = hash_password(password)

    user = cur.execute(
        'INSERT INTO users (username, password, email, status, pfp, dob) VALUES (?, ?, ?, ?, ?, ?)',
        (username, hash_pass.decode(), email, "Active", pfp, None))
    con.commit()
    return user

def remove_user(user_id):
    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    con.commit()

def get_user(username):
    user = cur.execute('SELECT * FROM users WHERE username = ?',(username, )).fetchone()
    return user

def get_all_users():
    return cur.execute('SELECT * FROM users').fetchall()

def validate_user(email, password):
    user = cur.execute('SELECT * FROM users WHERE email = ?',
                       (email, )).fetchone()
    encode = password.encode('utf-8')

    if not user:
        return False

    result = checkpw(encode, user[2].encode())

    if result:
        return user
    return False

def delete_user(id):
    cur.execute('DELETE FROM users WHERE id = ?', (id,))
    con.commit()


def update_user(query, *args):
    cur.execute(query, args)
    con.commit()
# print(query, args)



def update_user_status(id, status):
    cur.execute('UPDATE users SET status = ? WHERE id = ?', (status, id))
    con.commit()


def add_flight(_from, to, date, quantity):
    data = get(URL.format(_from=_from, to=to, date=date), headers=HEADERS, params={"Results": str(quantity)})
    root = ET.fromstring(data.content)
    # root = tree.getroot()
    
    for detail in root.find('.')[2:]:
        cur.execute('''INSERT INTO flight (total_trip_time, total_miles, flight_type, number_legs, price) VALUES (?, ?, ?, ?, ?)''', (
            detail.attrib['TotalTripTime'],
            detail.attrib['TotalMiles'],
            detail.attrib['FLSFlightType'],
            detail.attrib['FLSFlightLegs'],
            round(int(detail.attrib['TotalMiles']) * uniform(0.6, 0.7), 1)
        ))

        flight_id = cur.lastrowid
        for leg in detail:
            cur.execute('''INSERT INTO flight_leg (id, departure_datetime, departure_timeoffset, arrival_datetime, arrival_timeoffset, flight_number, journey_duration, sequence_number, leg_distance, departure_airport, arrival_airport, departure_terminal, arrival_terminal, airline_code, airline_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                flight_id,
                leg.attrib['DepartureDateTime'],
                leg.attrib['FLSDepartureTimeOffset'],
                leg.attrib['ArrivalDateTime'],
                leg.attrib['FLSArrivalTimeOffset'],
                leg.attrib['FlightNumber'],
                leg.attrib['JourneyDuration'],
                leg.attrib['SequenceNumber'],
                leg.attrib['LegDistance'],
                leg[0].attrib['LocationCode'], #departure
                leg[1].attrib['LocationCode'], #arrival
                leg[0].attrib['Terminal'], #departure
                leg[1].attrib['Terminal'], #arrival
                leg[2].attrib['Code'],
                leg[2].attrib['CompanyShortName'],
            ))

            cur.execute('''INSERT OR IGNORE INTO airport (location_code, location_name) VALUES (?, ?)''', (
                leg[0].attrib['LocationCode'], #departure
                leg[0].attrib['FLSLocationName'], #departure
            ))

            cur.execute('''INSERT OR IGNORE INTO airport (location_code, location_name) VALUES (?, ?)''', (
                leg[1].attrib['LocationCode'], #arrival
                leg[1].attrib['FLSLocationName'], #arrival
            ))

    con.commit()


def get_flights(_from=None, to=None, date=None, ids=None):
    if ids:
        sql_query = '''SELECT * FROM flight f
                    JOIN flight_leg fl ON f.id = fl.id
                    JOIN airport dep ON fl.departure_airport = dep.location_code
                    JOIN airport arr ON fl.arrival_airport = arr.location_code
                    WHERE f.id IN ({})
                    ORDER BY id'''.format(','.join('?' * len(ids)))
        data = cur.execute(sql_query, ids).fetchall()
        # print(ids, data)
    elif _from and to and date:
        collection = cur.execute('''SELECT * FROM flight f
                        JOIN (
                            SELECT fl.id, MIN(fl.sequence_number) as min, MAX(fl.sequence_number) as max FROM flight_leg fl
                            WHERE fl.departure_airport = ?
                            OR fl.arrival_airport = ?
                        ) AS leg1 ON f.id = leg1.id
                        JOIN flight_leg AS first_leg ON f.id = first_leg.id AND first_leg.sequence_number = leg1.min
                        JOIN flight_leg AS last_leg ON f.id = last_leg.id AND last_leg.sequence_number = leg1.max

                        JOIN airport dep ON first_leg.departure_airport = dep.location_code
                        JOIN airport arr ON last_leg.arrival_airport = arr.location_code
                        WHERE dep.location_code = ? AND arr.location_code = ? AND  INSTR(first_leg.departure_datetime, ?)
                        ORDER BY id''', (_from, to, _from, to, date,)).fetchall()
        ids = [f[0] for f in collection]
        sql_query = '''SELECT * FROM flight f
                    JOIN flight_leg fl ON f.id = fl.id
                    JOIN airport dep ON fl.departure_airport = dep.location_code
                    JOIN airport arr ON fl.arrival_airport = arr.location_code
                    WHERE f.id IN ({})
                    ORDER BY id'''.format(','.join('?' * len(ids)))
        data = cur.execute(sql_query, ids).fetchall()
    else:
        data = cur.execute('''SELECT * FROM flight f
                        JOIN flight_leg fl ON f.id = fl.id
                        JOIN airport dep ON fl.departure_airport = dep.location_code
                        JOIN airport arr ON fl.arrival_airport = arr.location_code
                        ORDER BY id''').fetchall()

    grouped_data = {}
    for row in data:
        id_value = row[0]
        if id_value not in grouped_data:
            grouped_data[id_value] = []
        grouped_data[id_value].append(row)

    return grouped_data
    
   


def delete_flight(id):
    cur.execute('DELETE FROM flight WHERE id = ?', (id,))
    cur.execute('DELETE FROM flight_leg WHERE id = ?', (id,))
    con.commit()

def get_airports(dep_arr=None):
    return cur.execute('''SELECT DISTINCT fl.departure_airport, a.location_name, fl.arrival_airport, b.location_name FROM flight_leg fl
                        JOIN airport a ON fl.departure_airport = a.location_code
                        JOIN airport b ON fl.arrival_airport = b.location_code''').fetchall()
    # return cur.execute('''SELECT * FROM airport''').fetchall()


def add_booking(flight_id, user_id):
    booking = cur.execute('''INSERT INTO bookings (flight_id, user_id, status) VALUES (?, ?, ?)''', (
        flight_id,
        user_id,
        'confirmed'
    ))
    con.commit()
    return booking

def add_passanger(booking_id, fname, lname, dob, gender, nationality):
    cur.execute('''INSERT INTO passengers (id, fname, lname, dob, gender, nationality) VALUES (?, ?, ?, ?, ?, ?)''', (
        booking_id,
        fname,
        lname,
        dob,
        gender,
        nationality
    ))
    con.commit()

def add_contact(booking_id, contact_name, ic_num, email, phone_no):
    cur.execute('''INSERT INTO contacts (id, contact_name, ic_num, email, phone_no) VALUES (?, ?, ?, ?, ?)''', (
        booking_id,
        contact_name,
        ic_num,
        email,
        phone_no
    ))
    con.commit()


def get_booking(lname=None, reference=None, user_id=None):
    if user_id:
        data = cur.execute('''SELECT b.id, b.user_id, b.flight_id FROM bookings b
                            JOIN passengers p ON b.id = p.id
                            WHERE b.user_id = ?''', (user_id,)).fetchall()
        return data
    if lname and reference:
        condition = cur.execute('''SELECT b.id, p.id, p.lname FROM bookings b
                            JOIN passengers p ON b.id = p.id
                            WHERE b.id = ? AND p.lname = ?''', (reference, lname)).fetchone()
        if not condition: return None
        data = cur.execute('''SELECT * FROM bookings b
                          JOIN passengers p ON b.id = p.id
                          JOIN contacts c ON b.id = c.id
                          WHERE b.id = ?''', (condition[0],)).fetchall()
    elif lname == 'all':
        data = cur.execute('''SELECT * FROM bookings b
                            JOIN passengers p ON b.id = p.id
                            JOIN contacts c ON b.id = c.id''').fetchall()
    else:
        return None

    grouped_data = {}
    for row in data:
        id_value = row[0]
        if id_value not in grouped_data:
            grouped_data[id_value] = []
        grouped_data[id_value].append(row)

    return grouped_data


def delete_booking(booking_id):
    cur.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    cur.execute('DELETE FROM passengers WHERE id = ?', (booking_id,))
    cur.execute('DELETE FROM contacts WHERE id = ?', (booking_id,))
    con.commit()

# update_user(3)
# delete_users()

# cur.execute('DELETE FROM bookings')
# cur.execute('DELETE FROM passengers')
# cur.execute('DELETE FROM contacts')
# cur.execute("DELETE FROM bookings")
# cur.execute("DELETE FROM users")
# cur.execute("UPDATE users SET status = 'Admin' WHERE id = 12")
# con.commit()

# add_flight()
# create_flights()
# create_flight()
# create_flight_leg()
# create_airport()
# create_contacts()
# create_bookings()
# create_passengers()
