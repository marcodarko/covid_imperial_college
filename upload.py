import biothings.hub.dataload.uploader
import os

import requests
import biothings
import config
biothings.config_for_app(config)

MAP_URL = "https://raw.githubusercontent.com/SuLab/outbreak.info-resources/master/outbreak_resources_es_mapping.json"
MAP_VARS = ["@type", "abstract", "author", "citedBy", "curatedBy", "dateModified", "datePublished", "doi", "funding", "identifier", "citedBy", "journalName", "journalNameAbbrev", "keywords", "license", "name", "publicationType", "url","dataDownload", "species", "infectiousAgent", "protocolSetting", "protocolCategory", "description", "downloadUrl","infectiousDisease"]

# when code is exported, import becomes relative
try:
    from covid_imperial_college.parser import load_annotations as parser_func
except ImportError:
    from .parser import load_annotations as parser_func


class ImperialCollegeUploader(biothings.hub.dataload.uploader.BaseSourceUploader):

    main_source="covid_imperial_college"
    name = "covid_imperial_college"
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
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        self.logger.info("No data to load from file for imperial college")
        return parser_func()

    @classmethod
    def get_mapping(klass):
        r = requests.get(MAP_URL)
        if(r.status_code == 200):
            mapping = r.json()
            mapping_dict = { key: mapping[key] for key in MAP_VARS }
            return mapping_dict