---
layout: page
title: Using the API
---

Using the API
=============

This applies to sayit.mysociety.org for the mobile upload token interface.

* Get the login token from `/instance/token` for the instance you want to
connect to

* `curl -c cookie.jar -d login-token='[[TOKEN]]' http://[[site]]/accounts/mobile-login/`

For the curl login request, do not target the instance-specific domain, as the
token is already linked to the instance

* `curl -v -b cookie.jar -F "audio=@path/to/audio.mp3;type=audio/mpeg" -F timestamps='[{"timestamp":0},{"timestamp":30000}]' http://[[instance site]]/api/v0.1/recording/`

Note that timestamps are in milliseconds, so 30000 above is 30 seconds. The
JSON structure for the list of timestamps can also include the speaker ID, for
example `{"timestamp":0,"speaker",1}`.

It may be easier to test with short audio snippets until you are able to
successfully upload.
