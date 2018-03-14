"""

chrome_render.py

This script sets up a Chrome server for use by xssmap

"""

from base64 import b64decode, b64encode
from flask import Flask, request, url_for
from selenium import webdriver

import json
import requests

HOST = '127.0.0.1'
PORT = 5555
DEBUG = True

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('headless')
chrome_options.add_argument('disable-web-security')
chrome_options.add_argument('allow-file-access-from-files')

driver = webdriver.Chrome(chrome_options = chrome_options)

app = Flask(__name__)

def print_debug(string):
    if DEBUG:
        print('\t[DEBUG] ' + string)

def make_base64_from_string(string):
    return str(b64encode(string.encode()).decode('utf-8'))

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
            if method not in ['GET','POST','PUT','DELETE']:
                method = 'GET'

        print_debug(method + ' ' + url)

        body = None
        if method != 'GET' and method != 'DELETE' and 'body' in req_data:
            body = get_string_from_base64(req_data['body'])
            print_debug('body = ' + str(body))

        headers = {}
        if 'headers' in req_data:
            headers = json.loads(get_string_from_base64(req_data['headers']))
            print_debug('Headers = ' + str(headers))

        # Set close-enough user agent string
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
                                         (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36'

        # TODO right now we assume this is a dict, but better to use the Requests CookieJar
        cookies = None
        if 'cookies' in req_data:
            cookies = json.loads(get_string_from_base64(req_data['cookies']))
            print_debug('Cookies = ' + str(cookies))

        provoke_page_events = True
        if 'provokePageEvents' in req_data:
            provoke_page_events = req_data['provokePageEvents']
            if provoke_page_events not in [True,False]:
                provoke_page_events = True

        print_debug('Provoking page events = ' + str(provoke_page_events))
        
        # Make the request with Requests
        if method == 'GET':
            response = requests.get(url, headers=headers, cookies=cookies)
        elif method == 'POST':
            response = requests.post(url, data=body, headers=headers, cookies=cookies)
        elif method == 'PUT':
            response = requests.put(url, data=body, headers=headers, cookies=cookies)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, cookies=cookies)

        page_source = response.text

        # TODO transpose applicable headers from response into Chrome

        # TODO transpose applicable cookies from response into Chrome

        # Render and manipulate the page source with Headless Chrome
        driver.get('data:text/html;charset=utf-8,' + page_source)

        errors = []
        console_messages = []
        alerts = []
        confirms = []
        prompts = []

        # Handle provocation of page events
        if provoke_page_events:
            print_debug('Starting page events')
            page_event_count = 0
            click_elements = driver.find_elements_by_xpath('//*[@onclick]')
            if click_elements:
                print_debug('\t' + 'Triggering @onclick')
                for e in click_elements:
                    # TODO
                    page_event_count += 1
            contextmenu_elements = driver.find_elements_by_xpath('//*[@oncontextmenu]')
            if contextmenu_elements:
                print_debug('\t' + 'Triggering @oncontextmenu')
                for e in contextmenu_elements:
                    # TODO
                    page_event_count += 1
            dblclick_elements = driver.find_elements_by_xpath('//*[@ondblclick]')
            if dblclick_elements:
                print_debug('\t' + 'Triggering @ondblclick')
                for e in dblclick_elements:
                    # TODO
                    page_event_count += 1
            mousedown_elements = driver.find_elements_by_xpath('//*[@onmousedown]')
            if mousedown_elements:
                print_debug('\t' + 'Triggering @onmousedown')
                for e in mousedown_elements:
                    # TODO
                    page_event_count += 1
            mouseenter_elements = driver.find_elements_by_xpath('//*[@onmouseenter]')
            if mouseenter_elements:
                print_debug('\t' + 'Triggering @onmouseenter')
                for e in mouseenter_elements:
                    # TODO
                    page_event_count += 1
            mouseleave_elements = driver.find_elements_by_xpath('//*[@onmouseleave]')
            if mouseleave_elements:
                print_debug('\t' + 'Triggering @onmouseleave')
                for e in mouseleave_elements:
                    # TODO
                    page_event_count += 1
            mousemove_elements = driver.find_elements_by_xpath('//*[@onmousemove]')
            if mousemove_elements:
                print_debug('\t' + 'Triggering @onmousemove')
                for e in mousemove_elements:
                    # TODO
                    page_event_count += 1
            mouseover_elements = driver.find_elements_by_xpath('//*[@onmouseover]')
            if mouseover_elements:
                print_debug('\t' + 'Triggering @onmouseover')
                for e in mouseover_elements:
                    # TODO
                    page_event_count += 1
            mouseout_elements = driver.find_elements_by_xpath('//*[@onmouseout]')
            if mouseout_elements:
                print_debug('\t' + 'Triggering @onmouseout')
                for e in mouseout_elements:
                    # TODO
                    page_event_count += 1
            mouseup_elements = driver.find_elements_by_xpath('//*[@onmouseup]')
            if mouseup_elements:
                print_debug('\t' + 'Triggering @onmouseup')
                for e in mouseup_elements:
                    # TODO
                    page_event_count += 1
            print_debug('Finished page events (' + str(page_event_count) + ')')

        # Build object of the information we need to send back
        res = {}
        res['html'] = make_base64_from_string(page_source)
        res['errors'] = make_base64_from_string(json.dumps(errors))
        res['console_messages'] = make_base64_from_string(json.dumps(console_messages))
        res['alerts'] = make_base64_from_string(json.dumps(alerts))
        res['confirms'] = make_base64_from_string(json.dumps(confirms))
        res['prompts'] = make_base64_from_string(json.dumps(prompts))
        
        return json.dumps(res)

if __name__ == '__main__':
    print('[INFO] Started Chrome rendering engine on ' + HOST + ':' + str(PORT) + '...')
    app.run(host=HOST, port=PORT, debug=DEBUG)
    driver.quit()
