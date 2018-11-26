# coding=utf-8
from flask import Flask
from flask_restful import Resource, Api
from os import environ
import re
import requests
from urllib import parse

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
    tags_list = [o['tags'] for o in posts_list]
    flat_list = [item for sublist in tags_list for item in sublist]

    # API call for ig's search
    endpoint = 'https://api.instagram.com/v1/tags/search?q=' + parse.quote(searched_tag) + '&access_token=' + environ.get('IG_DEFAULT_ACCESS_TOKEN')
    data = requests.get(endpoint).json()['data']
    ig_search_tag_counts = [{'text': o['name'], 'count': o['media_count'] + 9999} for o in data]
    ig_search_tags = [o['text'] for o in ig_search_tag_counts]

    # return if no posts found
    if (len(posts_list)==0) & (len(ig_search_tags)==0):
        return {
            'searchedHashtag': searched_tag,
            'data': []
        }

    # get a count of tags
    tag_counts = ig_search_tag_counts[:7] + [{'text': o, 'count': flat_list.count(o)} for o in set(flat_list) if not o in ig_search_tags]

    # filter and sorted count of tags
    filtered_tag_counts = [o for o in tag_counts if not re.search(hashtag_validation, o['text'])]
    filtered_tag_counts = [o for o in filtered_tag_counts if o['text'] != searched_tag]
    filtered_tag_counts = sorted(filtered_tag_counts, key=(lambda o: - o['count']))

    return {
        'searchedHashtag': searched_tag,
        'data': filtered_tag_counts[:50]
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