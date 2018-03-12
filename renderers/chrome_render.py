"""
chrome_render.py
"""

from flask import Flask, request, url_for
from selenium import webdriver

HOST = '127.0.0.1'
PORT = 5555

print('[INFO] Starting Chrome rendering engine on ' + HOST + ':' + str(PORT) + '...')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('headless')

driver = webdriver.Chrome(chrome_options = chrome_options)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def render_page():
    """
    Render webpage.
    """
    if request.method == 'POST':
        print('[DEBUG] Got request')
        driver.get('https://github.com/gingeleski')
        return driver.page_source

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
    driver.quit()
