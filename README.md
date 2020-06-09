Simple Flask app. Start with e.g.:
```
FLASK_APP=instarss.py flask run -p 4242
```
or a proper wsgi server if you intend more serious usage, and navigate to `localhost:4242/rss/<username>`

Since recently, credentials are needed. The app will look for them in the default keychain used by `python-keyring` under service name `instarss` and user `user` (yes, literally, this is not a placeholder). The session id can be seeded with:
```
python -m keyring instarss user
```
and should be valid for a year.
On first request, if keychain is locked, the app will hang while unlock prompt is displayed.
