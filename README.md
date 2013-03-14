# Heroku Signup (Experimental)

Automated Heroku account signup using App Engine

# Usage

Register a new App Engine application, edit application field of app.yaml, then
deploy to App Engine. You can now create a Heroku account by POSTing to:

    https://<appname>.appspot.com/new
      username=<desired user identifier>
      password=<desired password>

This will kick off the signup process. If started successfully, it will return 201
Created with a Location header. This doesn't mean the account is ready
to use. It's going to generate an email address that looks like this:

    <username>@<appname>.appspotmail.com

This email address will be "invited" to Heroku by a link sent to it. Our
service receives this email and parses it to finish the signup process.

After the above request, you need to poll the URL in the Location header
until it returns 200 with full account credentials before you can login
with this account. The URL in the Location header looks like this:

    https://<appname>.appspot.com/new/<username>@<appname>.appspotmail.com

Perform a GET request that follows redirects. Very likely, account
creation will be done and you'll receive JSON that looks like this:

    {"email": "<username>@<appname>.appspotmail.com", "password": "<password>"}

This means you can now login with those credentials. If the invitation
email has not been received and the account is still not ready, the request
will wait up to 25 seconds. If by then the account is not ready, it will
return a 307 redirect to itself and try again, effectively giving you long-polling.

If there was an error with creation on Heroku, you'll receive a 503 with
the details in the body. If the account was not created for any other
reason, after 5 minutes the request expires and you'll receive a 404.
