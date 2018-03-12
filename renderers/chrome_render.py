"""

chrome_render.py

This script sets up a Chrome server for use by xssmap

"""

from base64 import b64decode
from flask import Flask, request, url_for
from selenium import webdriver
from seleniumrequests import Chrome

import json

HOST = '127.0.0.1'
PORT = 5555
PRINT_DEBUG = True

print('[INFO] Starting Chrome rendering engine on ' + HOST + ':' + str(PORT) + '...')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('headless')

#driver = webdriver.Chrome(chrome_options = chrome_options)
driver = Chrome(chrome_options = chrome_options)

app = Flask(__name__)

def print_debug(string):
    if PRINT_DEBUG:
        print('\t[DEBUG] ' + string)

def get_string_from_base64(b64_string):
    return str(b64decode(b64_string).decode('utf-8'))

@app.route('/', methods=['POST'])
def render_page():
    """
    Render webpage.
    """
    if request.method == 'POST':
        
        print_debug('Got request')

        req_data = request.get_json(force=True)
        
        url = get_string_from_base64(req_data['url'])

        method = 'GET'
        if 'method' in req_data:
            method = get_string_from_base64(req_data['method']).upper()

        print_debug(method + ' ' + url)

        body = None
        if 'body' in req_data:
            body = get_string_from_base64(req_data['body'])
            print_debug('body = ' + str(body))

        headers = None
        if 'headers' in req_data:
            headers = json.loads(get_string_from_base64(req_data['headers']))
            print_debug('Headers = ' + str(headers))

        cookies = None
        if 'cookies' in req_data:
            cookies = json.loads(get_string_from_base64(req_data['cookies']))
            print_debug('Cookies = ' + str(cookies))

        provoke_page_events = True
        if 'provokePageEvents' in req_data:
            provoke_page_events = req_data['provokePageEvents']

        print_debug('Provoking page events = ' + str(provoke_page_events))
        
        # Make the request
        # TODO add options configured above...
        response = driver.request(method, url)
        
        return response.content

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
    driver.quit()
