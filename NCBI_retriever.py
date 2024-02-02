import requests
from xml.etree import ElementTree as ET

#We use the ncbi database
db = 'pubmed'
base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# Function to perform ESummary and return publication IDs
def perform_esearch_ids(query, api_key, sort_by="relevance", retmax=100):
    
    esearch_url = f"{base_url}esearch.fcgi?db={db}&term={query}&usehistory=y&api_key={api_key}"
    esearch_url += f"&sort={sort_by}&retmax={retmax}"
    
    # Perform the ESearch request
    esearch_response = requests.get(esearch_url)
    esearch_xml = esearch_response.text

    # Parse publication IDs from the XML response
    root = ET.fromstring(esearch_xml)
    pmids = [elem.text for elem in root.findall('.//Id')]
    
    # Parse WebEnv and QueryKey
    web = esearch_xml.split('<WebEnv>')[1].split('</WebEnv>')[0]

    return pmids, web

# Function to perform EFetch for abstracts
def perform_efetch_abstracts(pmids, web, api_key, chunk_size=200):
    
    articles_informations = []
    
    chunk_size = len(pmids) if len(pmids) > chunk_size else chunk_size
    
    for i in range(0, len(pmids), chunk_size):
        current_ids = pmids[i:i + chunk_size]
        efetch_url = f"{base_url}efetch.fcgi?db={db}&WebEnv={web}&api_key={api_key}"
        efetch_url += f"&retmode=xml&rettype=abstract&id=" + ",".join(current_ids)

        # Perform the EFetch request
        efetch_response = requests.get(efetch_url)
        efetch_xml = efetch_response.text

        # Parse publication Abstracts from the XML response
        root = ET.fromstring(efetch_xml)
        
        for article in root.findall('.//PubmedArticle'):
            # Extracting information
            article_title = article.find('.//ArticleTitle').text
            try:
                pub_date = article.find('.//ArticleDate')
                year = pub_date.find('Year').text
                month = pub_date.find('Month').text
                day = pub_date.find('Day').text
                pub_date = f"{year}-{month}-{day}"
            except:
                pub_date = None
           
            try:
                authors = []
                # We search for the authors of the article
                for author in article.findall('.//Author'):
                    last_name = author.find('LastName').text
                    fore_name = author.find('ForeName').text
                    authors.append(f"{fore_name} {last_name}")
            except:
                authors = None
            try:
                journal_info = article.find('.//MedlineJournalInfo')
            except:
                journal_info = None
            try:
                journal_name = journal_info.find('MedlineTA').text
            except:
                journal_name = None
            try:
                doi = article.find('.//ELocationID[@EIdType="doi"]').text
            except:
                doi = None

            # We search for the abstract of the article
            abstract_elements = article.findall('.//AbstractText')
            abstract_texts = [elem.text for elem in abstract_elements]
            # Some abstracts are cut in multiples places, it helps to link them together
            abstract_texts = " ".join(filter(None, abstract_texts))
            
            articles_informations.append([abstract_texts, article_title, pub_date, authors, journal_name, doi])       

    return articles_informations