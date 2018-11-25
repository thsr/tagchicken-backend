from flask import Flask
from flask_restful import Resource, Api
from os import environ
import re
import requests
from urllib import parse
from werkzeug.routing import NotFound

app = Flask(__name__)
api = Api(app, catch_all_404s=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', environ.get('ACCESS_CONTROL_ALLOW_ORIGIN_HB'))
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

def get_search_tag(searched_tag):
    # return if tag contains character other than one of these
    hashtag_validation = r'[^a-zA-Z0-9_ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]'
    match = re.search(hashtag_validation, searched_tag)
    if match:
        return {
            'searchedHashtag': searched_tag,
            'data': []
        }
    
    # chain API calls to get a few pages
    endpoint = 'https://api.instagram.com/v1/tags/' + parse.quote(searched_tag) + '/media/recent?access_token=' + environ.get('IG_DEFAULT_ACCESS_TOKEN')
    params = { 'count': 30 }
    posts_list=[]
    for i in range(3):
        r = requests.get(endpoint, params=params)
        data = r.json()
        posts_list += data['data']
        if hasattr(data, 'pagination'):
            if hasattr(data['pagination'], 'next_url'):
                endpoint = data['pagination']['next_url']
        else:
            break

    # return if no posts found
    if len(posts_list)==0:
        return {
            'searchedHashtag': searched_tag,
            'data': []
        }

    # get a count of tags
    tags_list = list(map((lambda o: o['tags']), posts_list))
    flat_list = [item for sublist in tags_list for item in sublist]
    tag_counts = [{'text': x, 'count': flat_list.count(x)} for x in set(flat_list)]

    # filter and sorted count of tags
    # filtered_tag_counts = [tag for tag in tag_counts if tag['text'] != searched_tag]
    # filtered_tag_counts = sorted(filtered_tag_counts, key=(lambda o: -o['count']))
    filtered_tag_counts = sorted(tag_counts, key=(lambda o: - o['count']))

    return {
        'searchedHashtag': searched_tag,
        'data': filtered_tag_counts[1:51]
    }

class SearchTag(Resource):
    def get(self, tag):
        try:
            return get_search_tag(tag)
        except Exception as e:
            return {'error': str(e)}, 500

api.add_resource(SearchTag, '/hb/search/<tag>')

if __name__ == '__main__':
    app.run(debug=True, port=3000)