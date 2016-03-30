from __future__ import division
import os
import re
import base64
import hashlib
import time
import json
import datetime
from hashlib import md5
import requests
from flask import Flask, render_template, jsonify, redirect, request, url_for, session, flash, abort


app = Flask(__name__)
app.secret_key = 'gf6dfg87sfg7sf5gs4dfg5s7fgsd980n'
app.debug = True


def req_to_emc(data):
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'https://%s:%s@%s:%s' % (rpc_config['user'],
                                   rpc_config['password'],
                                   rpc_config['host'],
                                   rpc_config['port'])
    

    return requests.post(url, data=json.dumps(data), verify=rpc_config['ssl_verify']).json()


def access_check():
    if check_login() == 0:
        abort(403)


def check_login():
    if 'auth' in session:
        try:
            with open('config/passwd', 'r') as f:
                login_pass = f.read().strip()
                if session['auth'] == login_pass:
                    return 1
        except IOError:
            pass

    serial = request.environ.get('SSL_CLIENT_M_SERIAL')
    serial = serial.rjust(16, '0').lower() if serial else ''.rjust(16, '0')

    if not all([request.environ.get('SSL_CLIENT_CERT'),
                request.environ.get('SSL_CLIENT_I_DN_UID') == 'EMC',
                serial[0] != '0']):
        return 0

    resp = req_to_emc({
        'method': 'name_show',
        'params': [
            'ssl:%s' % serial
        ],
    })

    if resp['error'] or resp['result']['expires_in'] <= 0:
        return 0

    value = resp['result']['value'].split('=')
    if value[0] not in hashlib.algorithms:
        return 0

    cert = re.sub(r'\-+BEGIN CERTIFICATE\-+|-+END CERTIFICATE\-+|\n|\r', '', request.environ.get('SSL_CLIENT_CERT'))
    if getattr(hashlib, value[0])(base64.b64decode(cert)).hexdigest() != value[1]:
        return 0

    return 2


@app.errorhandler(403)
def access_forbidden(e):
    return render_template('403.html'), 403


@app.errorhandler(401)
def access_forbidden(e):
    return render_template('401.html'), 401


@app.route('/')
def login():
    return redirect(url_for('wallet')) if check_login() > 0 else render_template('login.html')


# Method for login via login/password
@app.route('/auth', methods=['POST'])
def auth():
    # if we have cert, we don't need check login/pass
    if check_login() == 2:
        return redirect(url_for('wallet'))

    pw_hash = md5()
    pw_hash.update(request.form['password'])
    auth_str = '%s:%s' % (request.form['username'], pw_hash.hexdigest())

    try:
        with open('config/passwd', 'r') as f:
            login_pass = f.read().strip()
    except IOError:
        abort(401)

    if auth_str != login_pass:
        abort(401)

    session['auth'] = auth_str
    return redirect(url_for('wallet'))


# Method for logout (login/password method)
@app.route('/logout')
def logout():
    session.pop('auth', None)
    return redirect(url_for('login'))


@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    access_check()

    if request.method == 'POST':
        resp = req_to_emc({
            'method': 'sendtoaddress',
            'params': [
                request.form['address'],
                float(request.form['amount'])
            ]
        })

        if resp['error']:
            flash(resp['error']['message'], 'danger')
        else:
            flash('Money successfully transfered!', 'success')

        return redirect(url_for('wallet'))

    # display wallet balance
    resp = req_to_emc({
        'method': 'getbalance'
    })

    balance = resp['result']
    balance = format(balance, '.8f')
   
    # display list of transactions
    resp = req_to_emc({
        'method': 'listtransactions'
    })

    transactions = resp['result']

    for transaction in transactions:
        transaction['sexy_time'] = datetime.datetime.fromtimestamp(transaction['time']).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('wallet.html', balance=balance, transactions=transactions, login_btn=check_login())


@app.route('/minfo', methods=['GET', 'POST'])
def minfo():
    access_check()

    # display mining info
    resp = req_to_emc({
        'method': 'getinfo'
    })

    info = resp['result']

    # display Difficulty info
    resp = req_to_emc({
        'method': 'getdifficulty'
    })

    infodif = resp['result']

    return render_template('minfo.html', info=info, infodif=infodif, login_btn=check_login())


@app.route('/wallet_create', methods=['POST'])
def wallet_create():
    access_check()

    resp = req_to_emc({
        'method': 'getnewaddress'
    })

    flash('New address created: ' + resp['result'], 'success')

    return redirect(url_for('receive'))


@app.route('/receive', methods=['GET', 'POST'])
def receive():
    access_check()

    resp = req_to_emc({
        'method': 'getaddressesbyaccount',
        'params': ['']
    })

    inforeceive = resp['result']

    return render_template('receive.html', inforeceive=inforeceive, login_btn=check_login())


@app.route('/sign', methods=['GET', 'POST'])
def sign():
    access_check()

    if request.method == 'POST':
        resp = req_to_emc({
            'method': 'signmessage',
            'params': [
                request.form['address'],
                request.form['message']
            ]
        })

        if resp['error']:
            flash(resp['error']['message'], 'danger')
        else:
            flash('Message signed: ' + resp['result'], 'success')

        return redirect(url_for('sign'))

    return render_template('sign.html', login_btn=check_login())


@app.route('/nvs')
def nvs():
    access_check()

    resp = req_to_emc({
        'method': 'name_list'
    })

    name_list = resp['result']

    return render_template('nvs.html', name_list=name_list, login_btn=check_login())


@app.route('/nvs_new', methods=['POST'])
def nvs_new():
    access_check()

    resp = req_to_emc({
        'method': 'name_new',
        'params': [
            request.form['name'],
            request.form['value'],
            int(request.form['days'])
        ]
    })

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name created: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))


@app.route('/nvs_update', methods=['POST'])
def nvs_update():
    access_check()

    payload = {
        'method': 'name_update',
        'params': [
            request.form['name'],
            request.form['value'],
            int(request.form['days'])
        ]
    }

    if request.form['address']:
        payload['params'].append(request.form['address'])

    resp = req_to_emc(payload)

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name updated: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))


@app.route('/nvs_delete', methods=['POST'])
def nvs_delete():
    access_check()

    resp = req_to_emc({
        'method': 'name_delete',
        'params': [
            request.form['name']
        ]
    })

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name deleted: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
