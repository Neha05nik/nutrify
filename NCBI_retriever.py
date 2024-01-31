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
    ids = [elem.text for elem in root.findall('.//Id')]
    
    # Parse WebEnv and QueryKey
    web = esearch_xml.split('<WebEnv>')[1].split('</WebEnv>')[0]

    return ids, web

# Function to perform EFetch for abstracts
def perform_efetch_abstracts(ids, query, web, api_key, chunk_size=200, sort_by="relevance", retmax=100):
    
    abstracts = []
    
    chunk_size = len(ids) if len(ids) > chunk_size else chunk_size
    
    for i in range(0, len(ids), chunk_size):
        current_ids = ids[i:i + chunk_size]
        efetch_url = f"{base_url}efetch.fcgi?db={db}&WebEnv={web}&api_key={api_key}"
        efetch_url += f"&retmode=xml&rettype=abstract&id=" + ",".join(current_ids)

        # Perform the EFetch request
        efetch_response = requests.get(efetch_url)
        efetch_xml = efetch_response.text

        # Parse publication Abstracts from the XML response
        root = ET.fromstring(efetch_xml)
        
        for article in root.findall('.//PubmedArticle'):
            abstract_elements = article.findall('.//AbstractText')
            abstract_texts = [elem.text for elem in abstract_elements]
            # Some abstracts are cut in multiples places, it helps to link them together
            abstracts.append(" ".join(filter(None, abstract_texts)))

    return abstracts