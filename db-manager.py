from sqlite3 import connect

con = connect('system.db')
cur = con.cursor()

def create_users():
	cur.execute('''CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT NOT NULL,
		password TEXT NOT NULL,
		email TEXT NOT NULL,
		status TEXT NOT NULL,
		dob TEXT
	)''')
	con.commit()


def create_flights():
	cur.execute('''CREATE TABLE IF NOT EXISTS flights (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		flight_number TEXT NOT NULL,
		departure_airport TEXT NOT NULL,
		arrival_airport TEXT NOT NULL,
		departure_time TEXT NOT NULL,
		arrival_time TEXT NOT NULL,
		price TEXT NOT NULL
	)''')
	con.commit()


def create_bookings():
	cur.execute('''CREATE TABLE IF NOT EXISTS bookings (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		flight_id INTEGER NOT NULL,
		user_id INTEGER NOT NULL,
		seat_number TEXT NOT NULL,
		status TEXT NOT NULL,
		FOREIGN KEY (flight_id) REFERENCES flights(id),
		FOREIGN KEY (user_id) REFERENCES users(id)
	)''')
	con.commit()
