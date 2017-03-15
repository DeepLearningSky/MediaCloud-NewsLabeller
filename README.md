MediaCloud Story Topic Labeller
===============================

This script fetches stories from Media Cloud and tags them with topic labels based on models
trained on the NYT corpus.

Installation
------------

First install the [MediaCloud API client library](https://github.com/c4fcm/MediaCloud-API-Client).
Then install these python dependencies:

```
pip install -r requirements.pip
```

Now you need to set up a Redis queue somewhere:
* On OSX you should use [homebrew](http://brew.sh) - `brew install redis`.
* On Unbuntu, do `apt-get install redis-server` (the config file ends up in `/etc/redis/redis.conf`).

Now copy `settings.config.sample` to `settings.config` and be sure to fill it in.

Use
---

First you need to run the `fetch-stories.py` script load stories into the queue for geocoding 
(you can do this on a cron job if you want).

Then run the the Celery work server to label queued stories and post tags back to MediaCloud: 
`celery -A newslabeller worker -l info`.

If you set up Celery as a [service on Ubuntu](http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#init-script-celeryd) then you can run `sudo service celeryd start` to start the service:
* copy the [daemon script](https://raw.githubusercontent.com/ask/celery/master/contrib/generic-init.d/celeryd) to `/etc/init.d/celeryd' and make it executable
* copy the [example configuration](http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#example-configuration) to `/etc/default/celeryd` and change the `CELERYD_NODES` name to something you will recognize, change `CELERY_BIN` and `CELERY_CHDIR` to point at your virtualenv, set `CELERYD_LOG_LEVEL= "DEBUG"` if you want more logging
* create a new unpriveleged celery user: `sudo groupadd celery; sudo useradd -g celery celery`

If you need to empty out all your queues, just `redis-cli flushall`.
