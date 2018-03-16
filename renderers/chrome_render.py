"""
chrome_render.py

This script sets up a Chrome server for use by xssmap.
"""

from base64 import b64decode, b64encode
from flask import Flask, request, url_for
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import json
import re
import requests

HOST = '127.0.0.1'
PORT = 5555
DEBUG = True

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('headless')
chrome_options.add_argument('disable-web-security')
chrome_options.add_argument('allow-file-access-from-files')

desired = DesiredCapabilities.CHROME
desired['loggingPrefs'] = { 'browser' : 'ALL' }

driver = webdriver.Chrome(chrome_options = chrome_options, desired_capabilities = desired)
driver.maximize_window()

app = Flask(__name__)

def print_debug(string):
    """
    Debug print method.
    """
    if DEBUG:
        print('\t[DEBUG] ' + string)

def make_base64_from_string(string):
    """
    Make Base64 from string.
    """
    return str(b64encode(string.encode()).decode('utf-8'))

def get_string_from_base64(b64_string):
    """
    Get string from Base64.
    """
    return str(b64decode(b64_string).decode('utf-8'))

def get_element_size_and_location(element):
    """
    Get element size and location.
    """
    s_l = element.rect
    return s_l['location']['x'], s_l['location']['y'],\
                    s_l['size']['height'], s_l['size']['width']

def get_offset_still_inside_element(element):
    """
    Get offset still inside element.
    """
    x, y, h, w = get_element_size_and_location(element)
    # Moving towards the upper lefthand corner
    off_x = -1 * (w/4)
    off_y = -1 * (h/4)
    return off_x, off_y

def get_offset_outside_element(element, driver):
    """
    Get offset outside element.
    """
    element_size_and_loc = element.rect
    x, y, h, w = get_element_size_and_location(element)
    browser_size = driver.get_window_size()
    max_x = browser_size['width']
    max_y = browser_size['height']
    off_x = 0
    off_y = 0
    if (x - w) > 0:
        off_x -= w
    elif (y - h) > 0:
        off_y -= h
    elif (x + w) < max_x:
        off_x += w
    elif (x + h) < max_y:
        off_y += h
    return off_x, off_y

def parse_message_from_console_entry(string, url=None):
    """
    Parse message from console entry.
    """
    message = re.split(r'(> )(\d+)(:)(\d+)( ")', string)[-1]
    if url:
        message = message.replace(url, '')
    return message

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
            driver.get(url)  # TODO set headers and cookies for this
        else:
            if method == 'POST':
                response = requests.post(url, data=body, headers=headers, cookies=cookies)
            elif method == 'PUT':
                response = requests.put(url, data=body, headers=headers, cookies=cookies)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, cookies=cookies)
            response_html = response.text
            # TODO transpose applicable headers and cookies from response into Chrome
            # TODO page isn't really loading right (like no 404s on broken stuff)
            # Render and manipulate the page source with Headless Chrome
            driver.get('data:text/html;charset=utf-8,' + response_html)

        errors = []
        console_messages = []
        popups = []

        # Handle off-the-bat JavaScript popups - alert() confirm() prompt()
        while True:
            try:
                a = driver.switch_to_alert()
                popups.append(a.text)
                a.accept()
            except:
                # Probably/hopefully NoAlertPresentException
                break

        # TODO what if a page event provokes another popup? Need to handle

        # Handle provocation of page events
        if provoke_page_events:
            print_debug('Starting page events')
            page_event_count = 0
            click_elements = driver.find_elements_by_xpath('//*[@onclick]')
            if click_elements:
                print_debug('\t' + 'Triggering @onclick')
                for e in click_elements:
                    ActionChains(driver).click(e).pause(1).perform()
                    page_event_count += 1
            contextmenu_elements = driver.find_elements_by_xpath('//*[@oncontextmenu]')
            if contextmenu_elements:
                print_debug('\t' + 'Triggering @oncontextmenu')
                for e in contextmenu_elements:
                    ActionChains(driver).context_click(e).pause(1).perform()
                    page_event_count += 1
            dblclick_elements = driver.find_elements_by_xpath('//*[@ondblclick]')
            if dblclick_elements:
                print_debug('\t' + 'Triggering @ondblclick')
                for e in dblclick_elements:
                    ActionChains(driver).double_click(e).pause(1).perform()
                    page_event_count += 1
            mousedown_elements = driver.find_elements_by_xpath('//*[@onmousedown]')
            if mousedown_elements:
                print_debug('\t' + 'Triggering @onmousedown')
                for e in mousedown_elements:
                    ActionChains(driver).click(e).pause(1).perform()
                    page_event_count += 1
            mouseenter_elements = driver.find_elements_by_xpath('//*[@onmouseenter]')
            if mouseenter_elements:
                print_debug('\t' + 'Triggering @onmouseenter')
                for e in mouseenter_elements:
                    ActionChains(driver).move_to_element(e).pause(1).perform()
                    page_event_count += 1
            mouseleave_elements = driver.find_elements_by_xpath('//*[@onmouseleave]')
            if mouseleave_elements:
                print_debug('\t' + 'Triggering @onmouseleave')
                for e in mouseleave_elements:
                    # Move the mouse in and then out
                    actions = ActionChains(driver).move_to_element(e).pause(1)
                    move_x, move_y = get_offset_outside_element(e)
                    actions.move_by_offset(move_x, move_y)
                    actions.pause(1)
                    actions.perform()
                    page_event_count += 1
            mousemove_elements = driver.find_elements_by_xpath('//*[@onmousemove]')
            if mousemove_elements:
                print_debug('\t' + 'Triggering @onmousemove')
                for e in mousemove_elements:
                    # Move the mouse in, wait, then somewhere else in the element, wait
                    actions = ActionChains(driver).move_to_element(e).pause(1)
                    move_x, move_y = get_offset_still_inside_element(e)
                    actions.move_by_offset(move_x, move_y)
                    actions.pause(1)
                    actions.perform()
                    page_event_count += 1
            mouseover_elements = driver.find_elements_by_xpath('//*[@onmouseover]')
            if mouseover_elements:
                print_debug('\t' + 'Triggering @onmouseover')
                for e in mouseover_elements:
                    actions = ActionChains(driver).move_to_element(e).pause(1)
                    actions.perform()
                    page_event_count += 1
            mouseout_elements = driver.find_elements_by_xpath('//*[@onmouseout]')
            if mouseout_elements:
                print_debug('\t' + 'Triggering @onmouseout')
                for e in mouseout_elements:
                    # Move the mouse in, wait, then out and wait for something to happen
                    actions = ActionChains(driver).move_to_element(e).pause(1)
                    move_x, move_y = get_offset_outside_element(e)
                    actions.move_by_offset(move_x, move_y)
                    actions.pause(1)
                    actions.perform()
                    page_event_count += 1
            mouseup_elements = driver.find_elements_by_xpath('//*[@onmouseup]')
            if mouseup_elements:
                print_debug('\t' + 'Triggering @onmouseup')
                for e in mouseup_elements:
                    # Click, hold the click, then release and wait for something to happen
                    actions = ActionChains(driver).click_and_hold(e).pause(1)
                    actions.release().pause(1)
                    actions.perform()
                    page_event_count += 1
            print_debug('Finished page events (' + str(page_event_count) + ')')
        else:
            # Wait a couple seconds for 404 errors and what-not
            ActionChains(driver).pause(2).perform()

        # Handle JavaScript console errors and messages
        for entry in driver.get_log('browser'):
            message = parse_message_from_console_entry(entry['message'], url)
            if entry['level'] == 'INFO':
                console_messages.append(message)
            elif entry['level'] == 'WARNING' or entry['level'] == 'SEVERE':
                errors.append(message)

        # Get the source now that everything's done and loaded
        page_source = driver.page_source

        # Build object of the information we need to send back
        res = {}
        res['html'] = make_base64_from_string(page_source)
        res['errors'] = make_base64_from_string(json.dumps(errors))
        res['console_messages'] = make_base64_from_string(json.dumps(console_messages))
        res['popups'] = make_base64_from_string(json.dumps(popups))
        
        return json.dumps(res)

if __name__ == '__main__':
    print('[INFO] Started Chrome rendering engine on ' + HOST + ':' + str(PORT) + '...')
    app.run(host=HOST, port=PORT, debug=DEBUG)
    driver.quit()
