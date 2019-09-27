# -*- coding: utf-8 -*-

import json
import sys
import os

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only

sio = SocketIO(app)


# ======== Routing =========================================================== #

# -------- Home ------------------------------------------------------------- #
@app.route('/', methods=['GET'])
def home():
    if session.get('logged_in'):
        return redirect(url_for('sessions'))
    return redirect(url_for('login'))


# -------- Login ------------------------------------------------------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['id'] = os.urandom(128)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    return redirect(url_for('sessions'))


# -------- Logout ------------------------------------------------------------- #
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))


# -------- Session ---------------------------------------------------------- #
@app.route('/sessions', methods=['GET', 'POST'])
def sessions():
    if session.get('logged_in'):
        user = helpers.get_user()
        return render_template('session.html', user=user)
    return redirect(url_for('login'))


# -------- Message Callback ---------------------------------------------------------- #
def message_received():
    print("Message received")


# -------- Message Event ---------------------------------------------------------- #
@sio.on('connect')
def handle_new_conn():
    print(f"Received new connection")
    if session.get('logged_in'):
        user = helpers.get_user()
        print(f"Received new connection from {user}")


# -------- Message Event ---------------------------------------------------------- #
@sio.on('request')
def handle_new_url(message):
    print(f"Received new URL message: {message}")
    if session.get('logged_in'):
        user = helpers.get_user()
        return sio.emit('response', {
            "user": str(user),
            "body": f"{message}",
        }, callback=message_received)
    print("Not logged in...redirecting.")
    return redirect(url_for('login'))


# ======== Main ============================================================== #
if __name__ == "__main__":
    sio.run(app, debug=True)
    #app.run(debug=True, use_reloader=True)
