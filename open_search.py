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

stories_vector_index = 'stories_v'
stories_pipeline = {
    "description": "Stories NLP ingest pipeline",
    "processors": [
        {
            "text_chunking": {
                "algorithm": {
                    "fixed_token_length": {
                        "token_limit": 10,
                        "overlap_rate": 0.2,
                        "tokenizer": "standard"
                    }
                },
                "field_map": {
                    "content": "passage_chunk"
                }
            }
        },
        {
            "text_embedding": {
                "model_id": "{{model_id}}",
                "field_map": {
                    "passage_chunk": "passage_chunk_embedding"
                }
            }
        }
    ]
}
stories_vector_schema = {
    "settings": {
        "index.knn": True,
        "default_pipeline": "stories_pipeline"
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
            "passage_chunk_embedding": {
                "type": "nested",
                "properties": {
                    "knn": {
                        "type": "knn_vector",
                        "dimension": 768
                    }
                }
            }
        }
    }
}
query = {
  "query": {
    "nested": {
      "score_mode": "max",
      "path": "passage_chunk_embedding",
      "query": {
        "neural": {
          "passage_chunk_embedding.knn": {
            "query_text": "{{query}}",
            "model_id": "{{model_id}}"
          }
        }
      }
    }
  },
  "stored_fields": ["series", "url", "title", "author"]
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


def index_stories(stories, author, series, url, is_vector):
    for i, story in enumerate(stories):
        story['author'] = author
        story['series'] = series
        story['url'] = url
        if is_vector:
            url = '/' + stories_vector_index + '/_doc/' + str(i) + '?pipeline=stories_pipeline'
            client.http.put(url, body=story)
        else:
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


def aesop(is_vector=False):
    url = 'https://www.gutenberg.org/cache/epub/21/pg21-images.html'
    author = 'Aesop'
    series = "Aesop's Fables"
    fables = gutenberg_parse("data/pg21-images.html")
    print("{0}: {1}".format(series, len(fables)))
    index_stories(fables, author, series, url, is_vector)


def brothers_grimm(is_vector=False):
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
        index_stories(stories, author, g['name'], g['url'], is_vector)


def re_init_schema(name, body):
    del_index(name)
    response = client.indices.create(index=name, body=body)
    print(response)


def os_idx():
    re_init_schema(stories_index, stories_schema)
    aesop()
    brothers_grimm()


def vector():
    re_init_schema(stories_vector_index, stories_vector_schema)
    aesop(True)
    brothers_grimm(True)


def query_search(model, text):
    url = '/' + stories_vector_index + '/_search/'
    body = query
    body['query']['nested']['query']['neural']['passage_chunk_embedding.knn']['query_text'] = text
    body['query']['nested']['query']['neural']['passage_chunk_embedding.knn']['model_id'] = model
    response = client.http.get(url, body=body)
    items = response['hits']['hits']
    for i, item in enumerate(items):
        fields = item['fields']
        print("{0}: {1} from {2} by {3}".format(i+1, fields['title'][0], fields['series'][0], fields['author'][0]))

def search():
    model = input('Input the model to use: ')
    print('Type q to quit...')
    while True:
        input_query = input('\nEnter a query: ')
        if input_query == 'q':
            break
        query_search(model, input_query)