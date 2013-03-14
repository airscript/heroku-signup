import json
import urllib
import time
import re

from webapp2 import WSGIApplication
from webapp2 import Response

from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import memcache

signup_endpoint = 'https://api.heroku.com/signup'
verify_endpoint = 'https://api.heroku.com/invitation2/save'
email_regex = re.compile('https://api.heroku.com/signup/accept2/(\d+)/(\w+)')

def create_new_account(request):
    username = request.get('username')
    password = request.get('password')
    appname = request.host.split(':')[0].split('.')[0]
    email = "{0}@{1}.appspotmail.com".format(username, appname)
    memcache.set(email, (None, password), 300)
    result = urlfetch.fetch(url=signup_endpoint, method=urlfetch.POST,
                payload=urllib.urlencode({'email': email}),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                deadline=30)
    if result.status_code == 200:
        return Response(status='201 Created', location='/new/{0}'.format(email))
    else:
        return Response(result.content, status_int=result.status_code)

def wait_for_account(request, email):
    for _ in range(5):
        result = memcache.get(email)
        if result is None:
            return Response('Not Found', status='404 Not Found')
        success, payload = result
        if success is None:
            time.sleep(5)
        elif success:
            memcache.delete(email)
            return Response(json.dumps({'email': email, 'password': payload}))
        else:
            memcache.delete(email)
            return Response(payload, status='503 Upstream Error')
    return Response(status='307 Redirect', location='/new/{0}'.format(email))

def receive_email(request, email):
    result = memcache.get(email)
    if result is not None:
        _, password = result
        message = mail.InboundEmailMessage(request.body)
        message_text = message.bodies('text/plain').next()[1].decode()
        match = email_regex.search(message_text)
        if match:
            id = match.group(1)
            token = match.group(2)
            result = urlfetch.fetch(url=verify_endpoint, method=urlfetch.POST,
                payload=urllib.urlencode({
                    'id': id, 
                    'token': token,
                    'user[password]': password,
                    'user[password_confirmation]': password,
                    'user[receive_newsletter]': '0'}),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                deadline=30)
            if result.status_code == 200:
                memcache.set(email, (True, password), 300)
            else:
                memcache.set(email, (False, result.content), 300)


app = WSGIApplication([
    ('/new', create_new_account),
    ('/new/(.+)', wait_for_account),
    ('/_ah/mail/(.+)', receive_email),
], debug=True)
