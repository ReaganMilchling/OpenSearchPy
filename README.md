## Quickstart for OpenSearch
This repo is a collection of quickstarts to familiarize myself with OpenSearch. Run docker-compose first.

Use OpenSearch Python API to insert Aesop Fables data. [Download here](https://www.gutenberg.org/ebooks/21) and save the html file to root.

Bruno API Client repo added here as well.

The following is from OpenSearch tutorials.

### Ecommerce Index
Taken from [OpenSearch Guides](https://docs.opensearch.org/latest/getting-started/ingest-data/)
~~~
curl -O https://raw.githubusercontent.com/opensearch-project/documentation-website/3.2/assets/examples/ecommerce-field_mappings.json \
&& curl -O https://raw.githubusercontent.com/opensearch-project/documentation-website/3.2/assets/examples/ecommerce.ndjson \
&& curl -H "Content-Type: application/json" -X PUT "http://localhost:9200/ecommerce" --data-binary "@ecommerce-field_mappings.json" \
&& curl -H "Content-Type: application/x-ndjson" -X PUT "http://localhost:9200/ecommerce/_bulk" --data-binary "@ecommerce.ndjson"
~~~
~~~
curl -XGET "http://localhost:9200/ecommerce/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "customer_first_name": "Sonya"
    }
  }
}
'
~~~

### Hotel Vector Index
Taken from [OpenSearch Guides](https://docs.opensearch.org/latest/vector-search/getting-started/index/)
~~~
curl -XPUT "http://localhost:9200/hotels-index" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.knn": true
  },
  "mappings": {
    "properties": {
      "location": {
        "type": "knn_vector",
        "dimension": 2,
        "space_type": "l2"
      }
    }
  }
}
' \ &&
curl -XPOST "http://localhost:9200/_bulk" -H 'Content-Type: application/json' -d'
{ "index": { "_index": "hotels-index", "_id": "1" } }
{ "location": [5.2, 4.4] }
{ "index": { "_index": "hotels-index", "_id": "2" } }
{ "location": [5.2, 3.9] }
{ "index": { "_index": "hotels-index", "_id": "3" } }
{ "location": [4.9, 3.4] }
{ "index": { "_index": "hotels-index", "_id": "4" } }
{ "location": [4.2, 4.6] }
{ "index": { "_index": "hotels-index", "_id": "5" } }
{ "location": [3.3, 4.5] }
'
~~~
~~~
curl -XPOST "http://localhost:9200/hotels-index/_search" -H 'Content-Type: application/json' -d'
{
  "size": 3,
  "query": {
    "knn": {
      "location": {
        "vector": [5, 4],
        "k": 3
      }
    }
  }
}
'
~~~