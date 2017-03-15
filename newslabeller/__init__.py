import os, ConfigParser
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

def get_settings_file_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(base_dir, 'config', 'settings.config')
    return config_file_path

# load the shared settings file
settings = ConfigParser.ConfigParser()
settings.read(get_settings_file_path())

# connect to everything
mc_server = mediacloud.api.AdminMediaCloud(settings.get('mediacloud','key'))
