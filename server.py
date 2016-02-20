from __future__ import division
import os
import time
import json
import datetime
import hashlib
import requests
from flask import Flask, render_template, jsonify, redirect, request, url_for, session, flash, abort


app = Flask(__name__)
app.secret_key = 'gf6dfg87sfg7sf5gs4dfg5s7fgsd980n'
app.debug = True

def access_check():
    serial = request.environ.get('SSL_CLIENT_M_SERIAL')

    if not serial:
        abort(403)

    with os.popen('/usr/local/sbin/emcssh emcweb') as f:
        ssh_result = f.read()

    if serial.upper() not in ssh_result.upper():
        abort(403)

@app.errorhandler(403)
def access_forbidden(e):
    return render_template('403.html'), 403

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    if request.method == 'POST':
        payload = {
            'method': 'sendtoaddress',
            'params': [
                request.form['address'],
                float(request.form['amount'])
            ]
        }

        resp = requests.post(url, data=json.dumps(payload)).json()

        if resp['error']:
            flash(resp['error']['message'], 'danger')
        else:
            flash('Money successfully transfered!', 'success')

        return redirect(url_for('wallet'))

    # display wallet balance
    payload = {
        'method': 'getbalance'
    }

    resp = requests.post(url, data=json.dumps(payload))

    balance = resp.json()['result']
    balance = format(balance, '.8f')
   
    # display list of transactions
    payload = {
        'method': 'listtransactions'
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    transactions = resp['result']

    for transaction in transactions:
        transaction['sexy_time'] = datetime.datetime.fromtimestamp(transaction['time']).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('wallet.html', balance=balance, transactions=transactions)


@app.route('/minfo', methods=['GET', 'POST'])
def minfo():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

	# display mining info
    payload = {
        'method': 'getinfo'
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    info = resp['result']

	# display Difficulty info
    payload = {
        'method': 'getdifficulty'
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    infodif = resp['result']

    return render_template('minfo.html', info=info, infodif=infodif)


@app.route('/wallet_create', methods=['POST'])
def wallet_create():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    payload = {
        'method': 'getnewaddress'
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    flash('New address created: ' + resp['result'], 'success')

    return redirect(url_for('receive'))

@app.route('/receive', methods=['GET', 'POST'])
def receive():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    payload = {
        'method': 'getaddressesbyaccount',
        'params': ['']
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    inforeceive = resp['result']

    return render_template('receive.html', inforeceive=inforeceive)

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    if request.method == 'POST':
        payload = {
            'method': 'signmessage',
            'params': [
                request.form['address'],
                request.form['message']
            ]
        }

        resp = requests.post(url, data=json.dumps(payload)).json()

        if resp['error']:
            flash(resp['error']['message'], 'danger')
        else:
            flash('Message signed: ' + resp['result'], 'success')

        return redirect(url_for('sign'))

    return render_template('sign.html')

@app.route('/nvs')
def nvs():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    payload = {
        'method': 'name_list'
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    name_list = resp['result']

    return render_template('nvs.html', name_list=name_list)

@app.route('/nvs_new', methods=['POST'])
def nvs_new():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    payload = {
        'method': 'name_new',
        'params': [
            request.form['name'],
            request.form['value'],
            int(request.form['days'])
        ]
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name created: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))

@app.route('/nvs_update', methods=['POST'])
def nvs_update():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

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

    resp = requests.post(url, data=json.dumps(payload)).json()

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name updated: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))

@app.route('/nvs_delete', methods=['POST'])
def nvs_delete():
    access_check()
    with open('config/rpc', 'r') as f:
        rpc_config = json.loads(f.read())

    url = 'http://' + rpc_config['user'] + ':' + rpc_config['password'] + '@' + rpc_config['host'] + ':' + rpc_config['port']

    payload = {
        'method': 'name_delete',
        'params': [
            request.form['name']
        ]
    }

    resp = requests.post(url, data=json.dumps(payload)).json()

    if resp['error']:
        flash(resp['error']['message'], 'danger')
    else:
        flash('Name deleted: ' + resp['result'], 'success')

    return redirect(url_for('nvs'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
