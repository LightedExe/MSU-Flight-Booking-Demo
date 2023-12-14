from flask import Flask, render_template
from subprocess import Popen

DEBUG = True
app = Flask(__name__)

# When running the app for the first time, run this command to activate the css stuff
# npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch

@app.route('/')
def index():
	return render_template('home.html', blend_nav=True)


@app.route('/login')
def login():
	return render_template('login.html')


@app.route('/book')
def book():
	return render_template('booking.html')
	

@app.route('/tracker')
def tracker():
	return render_template('tracker.html')


@app.route('/manage')
def manage():
	return render_template('manage.html')


if __name__ == '__main__':
	if DEBUG:
		Popen('npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch', shell=True)
	app.run(host='0.0.0.0', port=81, debug=DEBUG)
