import os

import biothings, config
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT

import biothings.hub.dataload.dumper


class ImperialDumper(biothings.hub.dataload.dumper.DummyDumper):

    SRC_NAME = "covid_imperial_college"
    __metadata__ = {
        "src_meta": {
            "author":{
                "name": "Ginger Tsueng",
                "url": "https://github.com/gtsueng"
            },
            "code":{
                "branch": "master",
                "repo": "https://github.com/gtsueng/covid_imperial_college.git"
            },
            "url": "https://www.imperial.ac.uk/mrc-global-infectious-disease-analysis/covid-19/",
            "license": "https://www.imperial.ac.uk/research-and-innovation/support-for-staff/scholarly-communication/open-access/oa-policy/"
        }
    }
    # override in subclass accordingly
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)
    
    SCHEDULE = "15 14 * * 1"  # mondays at 14:15UTC/7:15PT