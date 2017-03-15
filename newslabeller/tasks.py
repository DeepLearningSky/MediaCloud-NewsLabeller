from __future__ import absolute_import
from celery.utils.log import get_task_logger
import mediacloud.api

from newslabeller import mc_server, NYT_LABELER_1_0_0_TAG_ID, NYT_LABELS_TAG_SET_NAME
from newslabeller.celery import app
from newslabeller.nytlabeller import get_labels

logger = get_task_logger(__name__)

# subjectively determined based on random experimentation
CONFIDENCE_THRESHOLD = 0.70

# helpful to set this to False when you're debugging
POST_WRITE_BACK = True


@app.task(serializer='json', bind=True)
def label_from_sentences(self, story):
    '''
    Take in a story with sentences and tag it with labels based on what the model says
    '''
    text = " ".join([sentence['sentence'] for sentence in story['story_sentences']])
    try:
        results = get_labels(text)
        _post_tags_from_results(story, results)
    except Exception as e:
        logger.exception("Exception - something bad happened")
        raise self.retry(exc=e)


def _post_tags_from_results(story, results):
    '''
    
    '''
    # Tag the story as processed by the labeller
    story_tags = [
        mediacloud.api.StoryTag(story['stories_id'], tags_id=NYT_LABELER_1_0_0_TAG_ID)
    ]
    # only tag it with ones that score really high
    taxonomic_classifiers = results['taxonomies']
    for label in taxonomic_classifiers:
        if float(label['score']) > CONFIDENCE_THRESHOLD:
            story_tags.append(
                mediacloud.api.StoryTag(story['stories_id'], tag_set_name=NYT_LABELS_TAG_SET_NAME, tag_name=label['label'])
            )
            logger.info("  label {} on {}".format(label['label'], story['stories_id']))
    if POST_WRITE_BACK:
        results = mc_server.tagStories(story_tags, clear_others=True)
        if results['success'] != 1:
            logger.error("  Tried to push {} story tags to story {}, but got no success!".format(
                len(story_tags), story['stories_id']))
    else:
        logger.info("  in testing mode - not sending sentence tags to MC")
