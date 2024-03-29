import requests
import re
import sys
import json
import rfeed
import time
import datetime
import keyring
from bs4 import BeautifulSoup

from flask import Flask, url_for, Response
from werkzeug.exceptions import BadGateway

app = Flask(__name__)

def get_profile(user, retries=10):
    tries = 0
    status = 0
    
    session_id = keyring.get_password("instarss", "user")
    
    while status != 200 and tries < retries:
        if tries:
                time.sleep(1)
        r = requests.get(
            'https://www.instagram.com/' + user + '/',
            cookies={'sessionid':session_id},
            allow_redirects=False)
        status = r.status_code
        if r.status_code != 200:
            print(user, status, file=sys.stderr) 
        tries += 1
    if status != 200:
        sys.stderr.flush()
        raise BadGateway(description=status)
    return r.content

def create_feed(profile_html, url, max_items=10):

    # Parse html
    soup = BeautifulSoup(profile_html, features="html5lib")

    # Extract the data object
    data = None
    for script in soup.find_all('script'):
        text = str(script.string)
        pat = '^\s*window._sharedData\s*='
        if re.match(pat, text):
            data = json.loads(
                re.sub(';\s*$', '', re.sub(pat, '', text))
            )

    # Select relevant data and build feed
    
    try:
        user = data['entry_data']['ProfilePage'][0]['graphql']['user']
        timeline = user['edge_owner_to_timeline_media']
    except (KeyError, TypeError):
        print(data, file=sys.stderr)
        raise

    items = []
    for item in timeline['edges'][:max_items]:
        node = item['node']
        link = 'https://www.instagram.com/p/' + node['shortcode']
        caption = node['accessibility_caption']
        caption_begin = caption.split('. ')[0] if caption is not None else ''
        caption_end = '. '.join(caption.split('. ')[1:]) if caption is not None else ''
        items.append(
            rfeed.Item(
                title = caption_begin,
                link = link, 
                description = caption_end,
                author = user['full_name'],
                guid = rfeed.Guid(node['id']),
                pubDate = datetime.datetime.fromtimestamp(node['taken_at_timestamp'])
            ))

    feed = rfeed.Feed(
        title = user['full_name'],
        link = url,
        description = soup.title.text.strip(),
        language = "en-US",
        lastBuildDate = datetime.datetime.now(),
        items = items)
    
    return feed

@app.route('/rss/<username>')
def rss(username):
    profile = get_profile(username)
    try:
        feed = create_feed(profile, url_for('rss', username=username))
    except:
        print(profile, file=sys.stderr)
        raise
    return Response(feed.rss(), mimetype='application/rss+xml')
