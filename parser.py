import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from biothings import config
logging = config.logger


def create_curationObject():
    now = datetime.now()
    curatedBy = {
    "@type": "Organization",
    'identifier': 'imperialcollege',
    'url': 'http://www.imperial.ac.uk/mrc-global-infectious-disease-analysis/covid-19/covid-19-reports/',
    "name": "MRC Centre for Global Infectious Disease Analysis",
    "affiliation": ["Imperial College London"],
    "curationDate":now.strftime("%Y-%m-%d")
    }    
    return(curatedBy)


def get_report_links(reports_url):
    recordlist = requests.get(reports_url)
    spiralbase = "https://spiral.imperial.ac.uk:8443/"
    parsedrecordlist = BeautifulSoup(recordlist.text, "html.parser")
    urlstable = parsedrecordlist.findAll("table")[0]
    urlstublist = urlstable.findAll("a")
    url_list = []
    for eachlink in urlstublist:
        tmpurl = spiralbase+eachlink.get("href")
        url_list.append(tmpurl)
    return(url_list)


def get_meta_content(metacontentfield):
    if len(metacontentfield) == 1:
        metacontentlist = metacontentfield[0].get("content")
    else:
        metacontentlist = []
        for eachitem in metacontentfield:
            metaitem = eachitem.get("content")
            metacontentlist.append(metaitem)
    return(metacontentlist)  


def transform_pub_meta(soupobject):
    urlfield = soupobject.findAll("meta", {"name":"citation_pdf_url"})
    url = get_meta_content(urlfield)
    titlefield = soupobject.findAll("meta", {"name":"citation_title"})
    title = get_meta_content(titlefield)
    datePublishedfield = soupobject.findAll("meta", {"name":"citation_date"})
    datePublished = get_meta_content(datePublishedfield)
    abstractfield = soupobject.findAll("meta", {"name":"DCTERMS.abstract"})
    abstract = get_meta_content(abstractfield)
    defaultidurlfield = soupobject.findAll("meta", {"scheme":"DCTERMS.URI"})
    defaultid = get_meta_content(defaultidurlfield)
    tmpdict = {
        "@context": {
        "schema": "http://schema.org/",
        "outbreak": "https://discovery.biothings.io/view/outbreak/"
        },
        "@type": "Publication",
        "journalName": "Imperial College London",
        "journalNameAbbreviation": "imperialcollege",
        "publicationType": "Report", 
        "abstract":abstract,
        "name":title,
        "datePublished":datePublished,
        "url":url,
        "identifier":defaultid
    }
    keywordsfield = soupobject.findAll("meta", {"name":"DC.subject"})
    if len(keywordsfield)>0:
        keywordsobject = get_meta_content(keywordsfield)
        tmpdict["keywords"] = keywordsobject

    licensefield = soupobject.findAll("meta", {"name":"DC.rights"})
    if len(licensefield)>0:
        license = get_meta_content(licensefield)
        tmpdict["license"] = license
        
    identifiersfield = soupobject.findAll("meta", {"name":"DC.identifier"})
    for eachitem in identifiersfield:
        eachitemcontent = eachitem.get("content")
        if "doi" in eachitemcontent:
            doi = eachitemcontent.replace("https://doi.org/","")
            tmpdict["identifier"] = "icl_"+doi.split('/', 1)[-1]
            tmpdict["doi"] = doi
        elif "10." in eachitemcontent:
            doi = eachitemcontent
            tmpdict["identifier"] = "icl_"+doi.split('/', 1)[-1]
            tmpdict["doi"] = doi
    tmpdict['_id'] = tmpdict["identifier"]
    return(tmpdict)


def get_authors(soupobject):
    authorsfield = soupobject.findAll("meta", {"name":"citation_author"})
    authors = get_meta_content(authorsfield)
    authorlist = []
    for eachauthor in authors:
        authparse = eachauthor.split(",")
        if (len(authparse) == 2) and len(authparse[1])<3:
            authdict = {'@type': 'outbreak:Person', 'affiliation': [], 'name': eachauthor, 
                       'familyName':authparse[0]}
        else:
            authdict = {'@type': 'outbreak:Person', 'affiliation': [], 'name': eachauthor}
        authorlist.append(authdict)
    return(authorlist)


def get_funding(soupobject):
    fundersfield = soupobject.findAll("meta", {"name":"DC.contributor"})
    funders = get_meta_content(fundersfield)
    fundercheck = len(fundersfield)
    if fundercheck > 0:
        identifiersfield = soupobject.findAll("meta", {"name":"DC.identifier"}) 
        fundidlist = []
        for eachitem in identifiersfield:
            eachitemcontent = eachitem.get("content")
            if "https:" in eachitemcontent:
                miscurls = eachitemcontent
            else:
                fundingid = eachitemcontent
                fundidlist.append(fundingid)
        fundlist = []
        i=0
        while i < len(funders):
            fundict = {"@type": "MonetaryGrant",
                       "funder": {
                       "name": funders[i]
                       },
                      "identifier": fundidlist[i],
                      "name": ""
            }
            fundlist.append(fundict)
        fundflag = True
    else:
        fundlist = []
        fundflag = False
    return(fundlist, fundflag)


def create_id(description_text):
    words = description_text.lower().split()
    letters = [word[0] for word in words]
    identifier = "icl_"+"".join(e for e in letters if e.isalnum())
    return(identifier)


def transform_resource_meta(metaobject):
    tmpdict = {
      "@context": {
        "schema": "http://schema.org/",
        "outbreak": "https://discovery.biothings.io/view/outbreak/"
      },
      "author": {
        "@type": "Organization",
        "name": 'Imperial College COVID-19 Response Team',
        "affiliation": ["MRC Centre for Global Infectious Disease Analysis",
                        "Imperial College London"]
      }
    }
    tmpdict['name'] = metaobject.find("h3",{"class":"title"}).get_text()
    tmpdict['description'] = metaobject.find("p").get_text()
    tmpdict['identifier'] = create_id(tmpdict['description'])
    tmpdict['_id'] = tmpdict['identifier']
    basetype = metaobject.find("span",{"class":"link primary"}).get_text()
    tmpurl = metaobject.find("a").get("href") 
    
    if "http" in tmpurl:
        url = tmpurl
    else:
        url = baseurl+tmpurl
    try:
        basedate = re.findall("\(\d{2}\-\d{2}\-\d{4}\)", tmpdict['description'])[0].strip("(").strip(")")
        datetime_object = datetime.strptime(basedate, '%d-%m-%Y')
        datePublished = datetime_object.strftime("%Y-%m-%d")
    except:
        datePublished = "Not Available"  
    if "data" in basetype:
        tmpdict['@type'] = "Dataset"
        tmpdict['dataDownload'] = {
            "contentUrl": url,
            "dateModified": datePublished
        }
        tmpdict['species']: "Homo sapiens"
        tmpdict['infectiousAgent']: "SARS-CoV-2"
    elif "code" in basetype:
        tmpdict['@type'] = "SoftwareSourceCode"
        tmpdict['downloadUrl'] = url
        tmpdict['datePublished'] = datePublished
    elif "survey" in basetype:
        tmpdict['@type'] = "Protocol"
        tmpdict['url'] = url
        tmpdict['datePublished'] = datePublished
        tmpdict['protocolSetting'] = "public"
        tmpdict["protocolCategory"] = "protocol"
    if "for \"Report" in tmpdict['description']:
        report_check = tmpdict['description'].replace("for \"Report","for|Report").split("|")
        citedByTitle = report_check[1].replace('"','')
        tmpdict['citedBy'] = {"name": citedByTitle,
                              "type": "Publication"}
    return(tmpdict)




def get_reports():
    reports_url = 'https://spiral.imperial.ac.uk:8443/handle/10044/1/78555/simple-search?location=10044%2F1%2F78555&query=&filter_field_1=type&filter_type_1=equals&filter_value_1=Report&rpp=100&sort_by=score&order=DESC&etal=1&submit_search=Update'
    url_list = get_report_links(reports_url)
    curatedBy = create_curationObject()

    for each_url in url_list:
        record_result = requests.get(each_url)
        parsed_record = BeautifulSoup(record_result.text, "html.parser")
        base_info = transform_pub_meta(parsed_record)
        base_info["curatedBy"] = curatedBy
        author_list = get_authors(parsed_record)
        fund_list, fund_flag = get_funding(parsed_record)
        ## Create the Json
        base_info["author"] = author_list
        if fund_flag == True:
            base_info["funding"] = fund_list
        
        yield(base_info)

        
def get_resources():
    curatedBy = create_curationObject()
    url = 'http://www.imperial.ac.uk/mrc-global-infectious-disease-analysis/covid-19/covid-19-scientific-resources/'
    response = requests.get(url)
    if response.status_code == 200:
        parsedlisting = BeautifulSoup(response.text, "html.parser")
        baseurl = "http://www.imperial.ac.uk/"
        resourceclass = parsedlisting.findAll("div", {"class": "media-item full light-secondary reverse equal-height"})
        resourcelist = []
        for eachblock in resourceclass:
            try:
                tmpdict = transform_resource_meta(eachblock) 
                tmpdict["curatedBy"] = curatedBy
                yield(tmpdict)
            except:
                logging.warning("resource transformation for: "+eachblock+" failed.")
    else:
        logging.warning("Imperial college Covid-19 resources not found")

        
def get_analysis():
    curatedBy = create_curationObject()
    analysislisturl = 'http://www.imperial.ac.uk/mrc-global-infectious-disease-analysis/covid-19/covid-19-planning-tools/'
    analysisresponse = requests.get(analysislisturl)
    if analysisresponse.status_code == 200:
        analysislisting = BeautifulSoup(analysisresponse.text, "html.parser")
        analysisclass = analysislisting.findAll("div", {"class": "media-item full light-secondary reverse equal-height"})

        for eachblock in analysisclass:
            tmpdict = {
              "@context": {
                "schema": "http://schema.org/",
                "outbreak": "https://discovery.biothings.io/view/outbreak/"
              },
              "author": {
                "@type": "Organization",
                "name": 'Imperial College COVID-19 Response Team',
                "affiliation": ["MRC Centre for Global Infectious Disease Analysis",
                                "Imperial College London"]
              }
            }
            try:
                tmpdict['name'] = eachblock.find("h3",{"class":"title"}).get_text()
                tmpurl = eachblock.find("a").get("href") 
                tmpdict['species'] = "Homo sapiens"
                tmpdict['infectiousAgent'] = "SARS-CoV-2"
                tmpdict['infectiousDisease'] = "COVID-19"
                tmpdict['description'] = eachblock.find("p").get_text()
                tmpdict['identifier'] = create_id(tmpdict['description'])
                tmpdict['_id'] = tmpdict['identifier']
                tmpdict["curatedBy"] = curatedBy
                if "http" in tmpurl:
                    tmpdict['url'] = tmpurl
                else:
                    tmpdict['url'] = baseurl+tmpurl
                tmpdict['datePublished'] = 'Not Available'
                yield(tmpdict)
            except:
                logging.warning("analysis transformation for: "+eachblock+" failed.")
    else:
        logging.warning("Imperial college Covid-19 planning tools not found")

        
def load_annotations():
    try:
        report_list = get_reports()
        for eachreport in report_list:
            yield(eachreport)
    except:
        logging.warning("report fetching failed")
    try:
        resource_list = get_resources()
        for eachresource in resource_list:
            yield(eachresource)
    except:
        logging.warning("resource fetching failed")
    try:
        analyses_list = get_analyses()
        for eachanalysis in analyses_list:
            yield(eachanalysis)
    except:
        logging.warning("analysis fetching failed")