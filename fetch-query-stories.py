import time
import logging

import newslabeller.tasks
from newslabeller import settings, mc_server, db, NYT_LABELER_1_0_0_TAG_ID, RELABEL, stories_to_fetch, \
    mode, MODE_WRITE_MC_TAGS, MODE_WRITE_TO_DB, settings_file_path

log = logging.getLogger(__name__)

# load task-specific
query = settings.get('mediacloud', 'query')
last_processed_stories_id = settings.get('mediacloud', 'last_processed_stories_id' )
log.info("Fetching latest stories matching:")
log.info("  query: {}".format(query))
log.info("  last_processed_stories_id: {}".format(last_processed_stories_id))

more_stories = True

while more_stories:

    # Fetch the story texts
    start_time = time.time()
    stories_with_text = mc_server.storyList(query, last_processed_stories_id=last_processed_stories_id,
                                            rows=stories_to_fetch, text=True)
    text_time = time.time()
    log.debug("    fetched {} story texts in {} seconds".format(len(stories_with_text), text_time - start_time))

    more_stories = len(stories_with_text) > 0

    if len(stories_with_text) > 0:
        last_processed_stories_id = int(stories_with_text[-1]['processed_stories_id']) + 1

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

    # and save that we've made progress
    settings.set('mediacloud', 'last_processed_stories_id', last_processed_stories_id)
    with open(settings_file_path, 'wb') as configfile:
        settings.write(configfile)

    log.info("Done with one page")

log.info("Done with all")
