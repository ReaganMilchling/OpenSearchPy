import html2text
from bs4 import BeautifulSoup
from opensearchpy import OpenSearch, NotFoundError

fables_json = 'fables.json'
grimm_json = 'grimm.json'

stories_index = 'stories'
stories_schema = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "_source": {
            "enabled": False
        },
        "dynamic": False,
        "properties": {
            "url": {
                "type": "text",
                "store": True,
                "index": False
            },
            "author": {
                "type": "text",
                "store": True
            },
            "series": {
                "type": "text",
                "store": True
            },
            "title": {
                "type": "text",
                "store": True
            },
            "content": {
                "type": "text",
                "store": False
            }
        }
    }
}

host = 'localhost'
port = 9200

# Create the client with SSL/TLS and hostname verification disabled.
client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_compress=True,  # enables gzip compression for request bodies
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)


def del_index(name):
    try:
        client.indices.delete(index=name)
    except NotFoundError:
        print('{} did not exist'.format(name))


def create_index_temp():
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


def index_stories(stories, author, series, url):
    for story in stories:
        story['author'] = author
        story['series'] = series
        story['url'] = url
        client.index(index=stories_index, body=story)


def gutenberg_parse(file_name):
    html = open(file_name, "r")
    soup = BeautifulSoup(html, features="html.parser")
    documents = []
    for chapter in soup.find_all('div', attrs={'class': 'chapter'}):
        title_tag = chapter.find('h2')
        if title_tag is None:
            title_tag = chapter.find('h3')
            title = title_tag.text
            chapter.h3.decompose()
        else:
            title = title_tag.text
            chapter.h2.decompose()

        soup_text = chapter.get_text()
        text = html2text.html2text(str(soup_text))

        if text != '':
            documents.append({'title': title.strip(), 'content': text})
    return documents


def aesop():
    url = 'https://www.gutenberg.org/cache/epub/21/pg21-images.html'
    author = 'Aesop'
    series = "Aesop's Fables"
    fables = gutenberg_parse("data/pg21-images.html")
    print("{0}: {1}".format(series, len(fables)))
    index_stories(fables, author, series, url)


def brothers_grimm():
    gutenberg = [
        {"url": "http://www.gutenberg.org/files/19068/19068-h/19068-h.htm", "name": "HOUSEHOLD STORIES BY THE BROTHERS GRIMM"},
        {"url": "http://www.gutenberg.org/files/11027/11027-h/11027-h.htm", "name": "GRIMM'S FAIRY STORIES"},
        {"url": "http://www.gutenberg.org/files/37381/37381-h/37381-h.htm", "name": "SNOWDROP AND OTHER TALES"},
    ]
    gutenberg_easy = [
        {"url": "http://www.gutenberg.org/files/2591/2591-h/2591-h.htm", "name": "THE BROTHERS GRIMM FAIRY TALES",
         "file": "data/grimm/Grimms’ Fairy Tales, by Jacob Grimm and Wilhelm Grimm.html"},
        {"url": "http://www.gutenberg.org/files/52521/52521-h/52521-h.htm", "name": "GRIMM'S FAIRY TALES",
         "file": "data/grimm/Grimm’s Fairy Tales, by Frances Jenkins Olcott (Editor).html"},
        {"url": "http://www.gutenberg.org/files/5314/5314-h/5314-h.htm", "name": "HOUSEHOLD TALES BY BROTHERS GRIMM",
         "file": "data/grimm/Household Tales by Brothers Grimm, by Jacob Grimm and Wilhelm Grimm.html"}
    ]
    author = 'Jacob Grimm and Wilhelm Grimm'
    for g in gutenberg_easy:
        stories = gutenberg_parse(g['file'])
        print("{0}: {1}".format(g['name'], len(stories)))
        index_stories(stories, author, g['name'], g['url'])


def init_stories():
    del_index(stories_index)
    response = client.indices.create(index=stories_index, body=stories_schema)
    print(response)


if __name__ == '__main__':
    init_stories()
    aesop()
    brothers_grimm()
