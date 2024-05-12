from flask import Flask, render_template, request, session, redirect, url_for, flash
from random import randint
from subprocess import Popen
import db_manager as dbm
from uuid import uuid4

DEBUG = True
app = Flask(__name__)
app.secret_key = "hiSirLuqman!"

pfps = [
    '/static/imgs/pfps/default-black.jpg',
    '/static/imgs/pfps/default-purple.jpg',
    '/static/imgs/pfps/default-goggle.jpg'
]

def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

# When running the app for the first time, run this command to activate the css stuff
# npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch

@app.route('/')
def index():
    return render_template('home.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        if request.form['type'] == "register":
            # Get data from user and save to db
            username = request.form['reg-username']
            password = request.form['reg-password']
            email = request.form['reg-email']
            pfp = pfps[randint(0, len(pfps)-1)]
            user = dbm.add_user(username, password, email, pfp)

            # Save session
            session['user'] = {'username': username, 'pfp': pfp, 'email': email, 'id': user.lastrowid}
        elif request.form['type'] == 'login':
            # Get data from user and save to db
            email = request.form['login-email']
            password = request.form['login-password']

            # Validate user credentials and save session
            user = dbm.validate_user(email, password)
            if user:
                if user[4] == "Banned":
                    flash("Unable to login, this account has been banned. If you feel this ban was a mistake please contact us.")
                    return redirect(url_for('index'))
                session['user'] = {'username': user[1], 'pfp': user[6], 'email': user[3], 'id': user[0]}
            else:
                flash("Incorrect email or password")
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)
    flash("Successfully logged out")
    return redirect(url_for('index'))


@app.route('/profile/<username>')
def profile(username):
    return redirect(url_for('profile_dashboard', username=username))


@app.route('/profile/<username>/dashboard')
def profile_dashboard(username):
    # Get user data and check if it exists
    user = dbm.get_user(username)
    if not user:
        flash("Unable to find user with name " + username)
        return redirect(url_for('index'))

    # If exists, check if profile belongs to user
    if 'user' in session and session['user']['username'] == username:
        bookings = dbm.get_booking(user_id=session['user']['id'])
        if bookings:
            ids = [booking[2] for booking in bookings]
            flights = dbm.get_flights(ids=ids)
            # print(flights)
            return render_template('profile/dashboard.html', user=user, bookings=bookings[::-1], flights=flights)
        return render_template('profile/dashboard.html', user=user)

    # If not redirect home and flash error
    flash("You are not logged in")
    return redirect(url_for('login'))


@app.route('/profile/<username>/settings')
def profile_settings(username):
    # Get user data and check if it exists
    user = dbm.get_user(username)
    if not user:
        flash("Unable to find user with name " + username)
        return redirect(url_for('index'))

    # If exists, check if profile belongs to user
    if 'user' in session and session['user']['username'] == username:
        return render_template('profile/settings.html', user=user)

    # If not redirect home and flash error
    flash("You are not logged in")
    return redirect(url_for('login'))


@app.route('/profile/<username>/admin', methods=['POST', 'GET'])
def profile_admin(username):
    if request.method == 'POST':
        _from = request.form['add-from']
        to = request.form['add-to']
        date = request.form['add-date'].replace('-', '')
        quantity = request.form['add-quantity']

        dbm.add_flight(_from, to, date, quantity)
        return redirect(url_for('profile_admin', username=username))
            
    # Get user data and check if it exists
    user = dbm.get_user(username)
    if not user:
        flash("Unable to find user with name " + username)
        return redirect(url_for('index'))

    # If exists, check if profile belongs to user
    if 'user' in session and session['user']['username'] == username and user[4] == 'Admin':
        flights = dbm.get_flights()
        users = dbm.get_all_users()

        return render_template('profile/admin.html', user=user, flight_collection=flights, users=users)

    # If not redirect home and flash error
    flash("You are not logged in")
    return redirect(url_for('login'))


@app.route('/book', methods=['POST', 'GET'])
def book():
    if request.method == 'POST':
        user_id = request.form['user-id']
        flight_id = request.form['flight-id']

        pax_data = []
        for passanger_keys in list(request.form.keys())[2:-4]:
            pax_data.append(request.form[passanger_keys])

        contact_name = request.form['contact-name']
        ic_num = request.form['identification-no']
        email = request.form['email']
        phone_no = request.form['phone-no']
        booking = dbm.add_booking(flight_id, user_id)
        id = booking.lastrowid
        dbm.add_contact(id, contact_name, ic_num, email, phone_no)

        for passanger in list(split(pax_data, int(len(pax_data)/5))):
            dbm.add_passanger(id, *passanger)

        print(pax_data[1], id)
        return redirect(url_for('manage', last_name=pax_data[1], reference_id=id))
    
    if request.args:
        dep = request.args.get('departure', None)
        arr = request.args.get('arrival', None)
        date = request.args.get('start', None)
        flights = dbm.get_flights(dep, arr, date)

        if not flights:
            flash("No flights found")
            return redirect(url_for('book'))
        return render_template('booking.html', current='book', flight_collection=flights, airports=dbm.get_airports())
    return render_template('booking.html', current='book', airports=dbm.get_airports())


# @app.route('/flights')
# def flight_view():
#     return render_template('flights.html', form = request.args)


@app.route('/tracker')
def tracker():
    flight_num = request.args.get('flight_num')
    return render_template('tracker.html', flight_num=flight_num, current='track')


@app.route('/manage')
def manage():
    if request.args:
        last_name = request.args.get('last_name', 'None')
        reference_id = request.args.get('reference_id', 'None')
        booking = dbm.get_booking(last_name, reference_id)

        if booking:
            print(booking[int(reference_id)][0][1])
            flight = dbm.get_flights(ids=[booking[int(reference_id)][0][1]])
            return render_template('manage.html', current='manage', booking=booking[int(reference_id)], flight=flight)
        flash("No bookings found")
        return redirect(url_for('manage'))
    return render_template('manage.html', current='manage', )


@app.route('/about')
def aboutus():
    return render_template('aboutus.html', current='about')


@app.route('/debug/<func>')
def debug(func):
    if func == 'users':
        data = dbm.get_all_users()
        return data

    if func == 'flights':
        _from = request.args.get('from', None)
        to = request.args.get('to', None)
        date = request.args.get('date', None)
        flights = dbm.get_flights(_from, to, date)
        return flights

    if func == 'airports':
        return dbm.get_airports()

    if func == 'bookings':
        return dbm.get_booking('all')

    flash("Invalid Function")
    return redirect(url_for('index'))


@app.route('/delete/<func>', methods=['post'])
def delete(func):
    if func == "flight":
        username = request.form['username']
        id = request.form['flight-id']
        dep = request.form['flight-dep']
        arr = request.form['flight-arr']
        dbm.delete_flight(id)
        flash("Deleted flight from {} to {}".format(dep, arr))
        return redirect(url_for('profile_admin', username=username))
    if func == 'user':
        username = request.form['username']
        id = request.form['user-id']
        user = request.form['user-name']
        dbm.delete_user(id)
        flash("Deleted user with name {}".format(user))
        return redirect(url_for('profile_admin', username=username))
    if func == 'booking':
        id = request.form['booking-id']
        dbm.delete_booking(id)
        flash("Deleted booking with id {}".format(id))
        return redirect(url_for('index'))
    

    flash("Invalid function")
    return redirect(url_for('index'))


@app.route('/update/<func>', methods=['post'])
def update(func):
    if func == 'user':
        # incomplete
        id = request.form.get('user-id', None)
        old_email = request.form.get('old-email', None)
        pfp = request.files['pfp']
        user = request.form.get('user-name', None)
        email = request.form.get('email', None)
        dob = request.form.get('dob', None)
        old_pass = request.form.get('old-pass', None)
        new_pass = request.form.get('new-pass', None)

        query = "UPDATE users SET "
        args = []
        update_sesh = {
            'username': session['user']['username'],
            'email': session['user']['email'],
            'pfp': session['user']['pfp'],
            'id': session['user']['id']
        }
        print("tstest")
        if pfp:
            with open("static/imgs/user_pfps/" + uuid4().hex[:16] + pfp.filename[-4:], 'wb') as pfpFile:
                pfpFile.write(pfp.read())

            query += "pfp = ?, "
            args.append('/'+pfpFile.name)
            update_sesh['pfp'] = '/'+pfpFile.name

        if user:
            query += "username = ?, "
            args.append(user)
            update_sesh['username'] = user
        if email:
            query += "email = ?, "
            args.append(email)
            update_sesh['email'] = email 
        if dob: 
            query += "dob = ?, "
            args.append(dob)
        if old_pass and new_pass:
            validated_user = dbm.validate_user(old_email, old_pass)
            if validated_user:
                query += "password = ?, "
                hash_pass = dbm.hash_password(new_pass)
                args.append(hash_pass.decode())
            else:
                flash("Invalid Old Password")
                return redirect(url_for('profile_settings', username=username))

        if query.endswith(', '):
            query = query[:-2] # remove the last ', '
            query += " WHERE id = ?"
            args.append(id)

            dbm.update_user(query, *args)
            session.pop('user', None)
            session['user'] = update_sesh
            
            return redirect(url_for('profile_settings', username=user if user else request.form['username']))
        return redirect(url_for('profile_settings', username=request.form['username']))

    if func == 'status':
        username = request.form['username']
        user_id = request.form['user-id']
        user_name = request.form['user-name']
        status_update= request.form['status-update']
        dbm.update_user_status(user_id, status_update)
        flash("Updated user status with name {} to {}".format(user_name, status_update))
        return redirect(url_for('profile_admin', username=username))
    return redirect(url_for('index'))


@app.route('/qrpay')
def qr():
    
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUJcmljayByb2xs')

if __name__ == '__main__':
    if DEBUG:
        Popen('npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch', shell=True)
    app.run(host='0.0.0.0', port=81, debug=DEBUG)
