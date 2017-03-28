import os
import sys
import json
import ConfigParser
import logging.config

import mediacloud.api

# The tag set that holds one tag for each version of the geocoder we use
NYT_LABELS_VERSION_TAG_SET_ID = 1964
NYT_LABELS_VERSION_TAG_SET_NAME = 'nyt_labels_version'
# The tag applied to any stories processed with NYT labeller v1.0
NYT_LABELER_1_0_0_TAG_ID = 9360669

# The huge tag set that has one tag for each taxonomic classifier
NYT_LABELS_TAG_SET_ID = 1963
NYT_LABELS_TAG_SET_NAME = 'nyt_labels'

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# set to true to re label ones that have already been labeled - set to false for no redos
RELABEL = True

# possible values for settings['labeller']['mode']
MODE_WRITE_TO_DB = "WRITE_TO_DB"
MODE_WRITE_MC_TAGS = "WRITE_MC_TAGS"

# load the shared settings file
settings_file_path = os.path.join(base_dir, 'config', 'settings.config')
settings = ConfigParser.ConfigParser()
settings.read(settings_file_path)

# set up logging
with open(os.path.join(base_dir, 'config', 'logging.json'), 'r') as f:
    logging_config = json.load(f)
logging.config.dictConfig(logging_config)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)

# load settings
stories_to_fetch = settings.get('mediacloud', 'stories_per_fetch')
mode = settings.get('labeller', 'mode')
if mode not in [MODE_WRITE_TO_DB, MODE_WRITE_MC_TAGS]:
    log.error("Not a valid mode: {}".format(mode))
    sys.exit()
if mode == MODE_WRITE_TO_DB:
    log.info("  writing results to {} on {}".format(settings.get('db', 'name'), settings.get('db', 'host')))
elif mode == MODE_WRITE_MC_TAGS:
    log.info("  write results back to mediacloud as tags in {}".format(NYT_LABELS_VERSION_TAG_SET_ID))

# connect to everything
mc_server = mediacloud.api.AdminMediaCloud(settings.get('mediacloud', 'key'))
db = mediacloud.storage.MongoStoryDatabase(db_name=settings.get('db', 'name'),
                                           host=settings.get('db', 'host'))

