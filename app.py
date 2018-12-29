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
    posts_list=[]
    tags_list=[]
    flat_list=[]
    
    # ig's unofficial MEDIA api
    endpoint = 'https://www.instagram.com/explore/tags/' + parse.quote(searched_tag) + '/?__a=1'
    r = requests.get(endpoint)
    if r.status_code == 200:
        try:
            data = r.json()
            posts_list = [ o['node']['edge_media_to_caption']['edges'][0]['node']['text'] for o in data['graphql']['hashtag']['edge_hashtag_to_media']['edges'] ]
            try:
                posts_list += [ o['node']['edge_media_to_caption']['edges'][0]['node']['text'] for o in data['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges'] ]
            except:
                pass
            p = re.compile("#([^# \n\s]+)")
            tags_list = [ p.findall(o) for o in posts_list ]
            flat_list = [ o.lower() for sublist in tags_list for o in sublist ]
        except:
            pass

    # ig's unofficial TAG api
    endpoint = 'https://www.instagram.com/web/search/topsearch/?context=hashtag&query=' + parse.quote(searched_tag)
    data = requests.get(endpoint).json()
    ig_search_tag_counts = [ {'text': o['hashtag']['name'].lower(), 'count': o['hashtag']['media_count']} for o in data['hashtags'] if o['hashtag']['media_count'] > 0 ]
    ig_search_tags = [ o['text'] for o in ig_search_tag_counts ]

    # return if no posts found
    if len(posts_list) == 0 and len(ig_search_tags) == 0:
        return {
            'searchedHashtag': searched_tag,
            'data': []
        }

    # get a count of tags
    tag_counts = ig_search_tag_counts[:7] + [{'text': o, 'count': flat_list.count(o)} for o in set(flat_list) if not o in ig_search_tags]

    # filter and sorted count of tags
    filtered_tag_counts = [ o for o in tag_counts if not re.search(hashtag_validation, o['text']) ]
    filtered_tag_counts = [ o for o in filtered_tag_counts if o['text'] != searched_tag ]
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