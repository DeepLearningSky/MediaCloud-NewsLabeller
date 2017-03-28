import time
import logging

import newslabeller.tasks
from newslabeller import settings, mc_server, db, NYT_LABELER_1_0_0_TAG_ID, RELABEL, stories_to_fetch, \
    mode, MODE_WRITE_MC_TAGS, MODE_WRITE_TO_DB

log = logging.getLogger(__name__)

# load task-specific
topic_id = settings.get('mediacloud', 'topic_id')
log.info("Fetching all stories from Topic #{}".format(topic_id))

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
    log.debug("    fetched {} text in {} seconds".format(len(stories_with_text), text_time - story_time))

    # now toss them into the queue
    queued = 0
    already_labeled = 0
    for story in stories_with_text:
        if mode == MODE_WRITE_MC_TAGS:
            already_labeled = NYT_LABELER_1_0_0_TAG_ID in story['story_tags']
            if RELABEL or not already_labeled:
                newslabeller.tasks.label_from_story_text.delay(story)
                queued += 1
            else:
                already_labeled += 1
        elif mode == MODE_WRITE_TO_DB:
            story_exists = db.storyExists(story['stories_id'])
            if RELABEL or not story_exists:
                newslabeller.tasks.save_labels_to_db.delay(story)
                queued += 1
            else:
                already_labeled += 1
    queued_time = time.time()
    log.debug("    queued in {} seconds".format(queued_time - text_time))

    # and report back timing on this round
    log.info("    queued {} stories in {} seconds ({} already labelled)".format(queued, time.time() - start_time, already_labeled))
    #sys.exit()

log.info("Done with entire topic")
