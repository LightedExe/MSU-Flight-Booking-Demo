from flask import Flask, render_template

app = Flask(__name__)

# When running the app for the first time, run this command to activate the css stuff
# npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch

@app.route('/')
def index():
	return render_template('home.html')


@app.route('/login')
def login():
	return render_template('login.html')


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=81, debug=True)
