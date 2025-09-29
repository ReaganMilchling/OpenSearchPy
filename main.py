import json
import os

import opensearchpy
from bs4 import BeautifulSoup
from opensearchpy import OpenSearch, NotFoundError

json_name = 'fables.json'
host = 'localhost'
port = 9200

# Create the client with SSL/TLS and hostname verification disabled.
client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_compress = True, # enables gzip compression for request bodies
    use_ssl = False,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False
)

def del_index(name):
    try:
        client.indices.delete(index=name)
    except NotFoundError:
        print('{} did not exist'.format(name))

def create_index():
    del_index('movies')
    del_index('python-test-index')
    del_index('my-dsl-index')

    # Create an index with non-default settings.
    index_name = 'python-test-index'
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 4
            }
        }
    }
    response = client.indices.create(index=index_name, body=index_body)
    print('\nCreating index:')
    print(response)

    # Add a document to the index.
    document = {
        'title': 'Moneyball',
        'director': 'Bennett Miller',
        'year': '2011'
    }
    id = '1'
    response = client.index(
        index=index_name,
        body=document,
        id=id,
        refresh=True
    )

    print('\nAdding document:')
    print(response)

    # Perform bulk operations
    movies = '{ "index" : { "_index" : "movies", "_id" : "2" } } \n { "title" : "Interstellar", "director" : "Christopher Nolan", "year" : "2014"} \n { "create" : { "_index" : "movies", "_id" : "3" } } \n { "title" : "Star Trek Beyond", "director" : "Justin Lin", "year" : "2015"} \n { "update" : {"_id" : "3", "_index" : "movies" } } \n { "doc" : {"year" : "2016"} }'
    client.bulk(body=movies)
    # Search for the document.
    q = 'miller'
    query = {
        'size': 5,
        'query': {
            'multi_match': {
                'query': q,
                'fields': ['title^2', 'director']
            }
        }
    }

    response = client.search(
        body=query,
        index=index_name
    )
    print('\nSearch results:')
    print(response)

def fables():
    try:
        os.remove(json_name)
    except OSError:
        pass

    html = open("pg21-images.html", "r")
    soup = BeautifulSoup(html, features="html.parser")
    stories = []
    for chapter in soup.find_all('div', attrs={'class': 'chapter'}):
        title = chapter.find('h2').text
        raw_text = chapter.find_all('p')
        text = ''
        for t in raw_text:
            text += t.text.lstrip()
        if text != '':
            stories.append({'title': title, 'content': text})
    print('done parsing')
    with open(json_name, 'w', encoding='utf-8') as f:
        json.dump(stories, f, ensure_ascii=False, indent=4)
    print('done writing')

def index_fables():
    index_name = 'fables'
    del_index(index_name)

    text = json.load(open(json_name, "r"))
    for i, fable in enumerate(text):
        index = {}
        index['_index'] = index_name
        index['_id'] = i
        response = client.index(
            index = index_name,
            body = fable,
            id = i,
            refresh = True
        )


if __name__ == '__main__':
    #create_index()
    #fables()
    index_fables()
