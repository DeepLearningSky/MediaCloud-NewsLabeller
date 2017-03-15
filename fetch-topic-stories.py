import os
import sys
import time
import json
import logging.config

import newslabeller.tasks
from newslabeller import settings, mc_server, base_dir, NYT_LABELER_1_0_0_TAG_ID, nytlabeller

# set to true to re label ones that have already been labeled - set to false for no redos
RELABEL = True

# set up logging
with open(os.path.join(base_dir,'config','logging.json'), 'r') as f:
    logging_config = json.load(f)
logging.config.dictConfig(logging_config)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)

# load settings
stories_to_fetch = settings.get('mediacloud', 'stories_per_fetch')
topic_id = settings.get('mediacloud', 'topic_id')
log.info("Fetching {} stories by page from Topic #{} to label".format(stories_to_fetch, topic_id) )

more_stories = True
next_link_id = None

# best to just go through all the stories in an open loop and fill up the redis queue
while more_stories:

    start_time = time.time()
    # Fetch some story ids and queue them up to get text (because topicStoryList doesn't support text option)
    log.info("Fetch link_id {}".format(next_link_id))
    stories = mc_server.topicStoryList(topic_id, link_id=next_link_id, limit=stories_to_fetch)
    story_ids = [story['stories_id'] for story in stories['stories'] if story['language'] in [None,'en']]
    log.debug("  fetched {} stories ({} in english)".format(len(stories['stories']),len(story_ids)))
    if 'next' in stories['link_ids']:
        next_link_id = stories['link_ids']['next']
        more_stories = True
    else:
        more_stories = False
    story_time = time.time()
    log.debug("    fetched stories in {} seconds".format(story_time - start_time))

    # now we need to fetch text
    log.debug("  fetching text")
    story_ids = [str(sid) for sid in story_ids]
    stories_with_text = mc_server.storyList("stories_id:("+" ".join(story_ids)+")", text=True, rows=stories_to_fetch)
    text_time = time.time()
    log.debug("    fetched text in {} seconds".format(text_time - story_time))

    # now toss them into the queue
    queued = 0
    already_labeled = 0
    for story in stories_with_text:
        tags = [tag['tags_id'] for tag in story['story_tags']]
        already_labeled = NYT_LABELER_1_0_0_TAG_ID in tags
        if RELABEL or not already_labeled:
            newslabeller.tasks.label_from_story_text.delay(story)
            queued += 1
        else:
            already_labeled += 1
    queued_time = time.time()
    log.debug("    queued in {} seconds".format(queued_time - text_time))

    # and report back timing on this round
    log.info("    queued {} stories in {} seconds ({} already labelled)".format(queued, time.time() - start_time, already_labeled))

log.info("Done with entire topic")
