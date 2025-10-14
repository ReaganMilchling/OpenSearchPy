from opensearchpy import NotFoundError, OpenSearch

host = 'localhost'
port = 9200

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_compress=True,
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
