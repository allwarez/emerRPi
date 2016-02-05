from __future__ import division
import os
import json
import re
import subprocess
import time
from pycgminer import CgminerAPI

'''
Helper to work with line chart

Example:
chart = LineChart(5)
chart.lines() => [[0, 0, 0, 0, 0]]
chart.append([1])
chart.lines() => [[0, 0, 0, 0, 1]]
chart.append([5])
chart.lines() => [[0, 0, 0, 1, 5]]

Adding array with different lenght (for example now you want to work with 2 lines) will reset line chart
chart.append([10, 20])
chart.lines() => [[0, 0, 0, 0, 10], [0, 0, 0, 0, 20]]
chart.append([15, 5])
chart.lines() => [[0, 0, 0, 10, 15], [0, 0, 0, 20, 5]]
chart.append([1, 3, 5])
chart.lines() => [[0, 0, 0, 0, 1], [0, 0, 0, 0, 3], [0, 0, 0, 0, 5]]

Reset chart by providing lines quantity
chart.reset(1)
chart.lines() => [[0, 0, 0, 0, 0]]
chart.reset(3)
chart.lines() => [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
'''
class LineChart:

    def __init__(self, line_length):
        self._line_length = line_length
        self._lines = []
        self.reset(1)

    def lines(self):
        return self._lines

    def append(self, points):
        if len(self._lines) != len(points):
            self.reset(len(points))

        for i, line in enumerate(self._lines):
            self._lines[i].pop(0)
            self._lines[i].append(points[i])

    def reset(self, number_of_lines):
        new_lines = []

        for i in xrange(1, number_of_lines + 1):
            new_lines.append([0 for x in xrange(1, self._line_length + 1)])

        self._lines = new_lines

'''
Helper to work with cgminer api
'''
class CgminerError(Exception):
    pass

class Cgminer:

    def __init__(self):
        self.api = CgminerAPI()
        self.config_path = os.path.dirname(os.path.realpath(__file__)) + '/config/cgminer'

    def active(self):
        output = os.popen('ps x | grep cgminer').read()
        if re.search('config/cgminer', output):
            return True

        return False

    def start(self):
        subprocess.Popen(['cgminer', '-c', 'config/cgminer', '-T'], stdout=open('logs', 'w'))

    def stop(self):
        subprocess.Popen(['killall', 'cgminer'], stdout=subprocess.PIPE)

    def restart(self):
        self.stop()
        time.sleep(3)
        self.start()

    def devices(self):
        data = {}

        try:
            data['edevs'] = self.api.edevs()
        except Exception as e:
            raise CgminerError('Problem with API edevs method: ' + e.message)

        try:
            data['estats'] = self.api.estats()
        except Exception as e:
            raise CgminerError('Problem with API estats method: ' + e.message)

        result = []

        try:
            for i in xrange(0, len(data['edevs']['DEVS'])):
                dev = data['edevs']['DEVS'][i]
                stat = data['estats']['STATS'][i]

                result.append({
                    'id': dev['ID'],
                    'name': dev['Name'],
                    'mhs': dev['MHS 1m'],
                    'ghs': dev['MHS 1m'] / 1000,
                    'temperature': dev['Temperature'],
                    'accepted': dev['Accepted'],
                    'rejected': dev['Rejected'],
                    'clockrate': stat['base clockrate'],
                    'fan': stat['fan percent'],
                    'voltage': stat['Asic0 voltage 0']
                })
        except Exception as e:
            raise CgminerError('Problem with devices data preparing: ' + e.message)

        return result

    def summary(self):
        try:
            summary = self.api.summary()
        except Exception as e:
            raise CgminerError('Problem with API summary method: ' + e.message)

        try:
            pools = self.api.pools()
        except Exception as e:
            raise CgminerError('Problem with API pools method: ' + e.message)

        try:
            edevs = self.api.edevs()
        except Exception as e:
            raise CgminerError('Problem with API edevs method: ' + e.message)

        try:
            total = summary['SUMMARY'][0]['Accepted'] + summary['SUMMARY'][0]['Rejected']
            if total == 0:
                accepted_percent = 0
                rejected_percent = 0
            else:
                accepted_percent = int(summary['SUMMARY'][0]['Accepted'] / total * 100)
                rejected_percent = int(summary['SUMMARY'][0]['Rejected'] / total * 100)

            result = {
                'mhs': 0,
                'ghs': 0,
                'accepted': summary['SUMMARY'][0]['Accepted'],
                'rejected': summary['SUMMARY'][0]['Rejected'],
                'accepted_percent': accepted_percent,
                'rejected_percent': rejected_percent,
                'pool': {
                    'url': pools['POOLS'][0]['URL'],
                    'user': pools['POOLS'][0]['User']
                }
            }

            for edev in edevs['DEVS']:
                result['mhs'] += edev['MHS 1m']
                result['ghs'] += edev['MHS 1m'] / 1000
        except Exception as e:
            raise CgminerError('Problem with summary data preparing: ' + e.message)

        return result

    def pools(self):
        with open(self.config_path, 'r') as f:
            return json.loads(f.read())['pools']

    # TODO: catch exceptions
    def update_pools(self, pools):
        ordered_pools = sorted(pools, key=lambda pool: int(pool['priority']))

        with open(self.config_path, 'r') as f:
            config = json.loads(f.read())

        config['pools'] = ordered_pools

        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    def clockrate(self):
        with open(self.config_path, 'r') as f:
            return json.loads(f.read())['hfa-hash-clock']

    def update_clockrate(self, clockrate):
        with open(self.config_path, 'r') as f:
            config = json.loads(f.read())

        config['hfa-hash-clock'] = clockrate

        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    def fan_speed(self):
        with open(self.config_path, 'r') as f:
            config = json.loads(f.read())
            if 'hfa-fan' in config:
                return config['hfa-fan']
            else:
                return 'auto'

    def update_fan_speed(self, fan_speed):
        with open(self.config_path, 'r') as f:
            config = json.loads(f.read())

        if fan_speed == 'auto':
            if 'hfa-fan' in config:
                del config['hfa-fan']
        else:
            config['hfa-fan'] = fan_speed

        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    def overheat(self):
        with open(self.config_path, 'r') as f:
            return json.loads(f.read())['hfa-temp-overheat']

    def update_overheat(self, overheat):
        with open(self.config_path, 'r') as f:
            config = json.loads(f.read())

        config['hfa-temp-overheat'] = overheat

        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    def save(self):
        try:
            print self.api.save(self.config_path)
        except Exception as e:
            raise CgminerError('Problem with API save method: ' + e.message)

        return True

    def latest_hashrate_poins(self):
        points = []

        try:
            for edev in self.api.edevs()['DEVS']:
                points.append(edev['MHS 5m'] / 1000)
        except Exception as e:
            raise CgminerError('Problem with API edevs method: ' + e.message)

        return points

if __name__ == '__main__':
    chart = LineChart(3)
    assert chart.lines() == [[0, 0, 0]]

    chart = LineChart(7)
    assert chart.lines() == [[0, 0, 0, 0, 0, 0, 0]]

    chart = LineChart(5)
    assert chart.lines() == [[0, 0, 0, 0, 0]]

    chart.reset(2)
    assert chart.lines() == [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]

    chart.reset(3)
    assert chart.lines() == [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]

    chart.append([1, 2, 3])
    assert chart.lines() == [[0, 0, 0, 0, 1], [0, 0, 0, 0, 2], [0, 0, 0, 0, 3]]

    chart.append([10, 20, 30])
    assert chart.lines() == [[0, 0, 0, 1, 10], [0, 0, 0, 2, 20], [0, 0, 0, 3, 30]]

    chart.append([13, 31])
    assert chart.lines() == [[0, 0, 0, 0, 13], [0, 0, 0, 0, 31]]

    chart.append([100])
    assert chart.lines() == [[0, 0, 0, 0, 100]]

    chart = LineChart(3)
    assert chart.lines() == [[0, 0, 0]]
    chart.append([10, 20])
    assert chart.lines() == [[0, 0, 10], [0, 0, 20]]
    chart.append([11, 22])
    assert chart.lines() == [[0, 10, 11], [0, 20, 22]]
    chart.append([44, 99])
    assert chart.lines() == [[10, 11, 44], [20, 22, 99]]
    chart.append([100, 200])
    assert chart.lines() == [[11, 44, 100], [22, 99, 200]]
