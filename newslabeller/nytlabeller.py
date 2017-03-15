import requests
import logging

from newslabeller import settings

log = logging.getLogger(__name__)

host = settings.get('labeller', 'host')
port = settings.get('labeller', 'port')


def _get_url():
    return host+':'+str(port)+'/predict.json'


def get_labels(story_text):
    return _query({'text': story_text})


def _query(data):
    try:
        r = requests.post(_get_url(), json=data)
        log.debug('labeller says %r', r.content)
        return r.json()
    except requests.exceptions.RequestException as e:
        log.exception(e)
    return None
