import sys
import argparse
import itertools
import string
import json
import praw
import nltk
import gensim
import pandas as pd


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--scrape", help="scrape data fresh",
                    action="store_true")
parser.add_argument("-r", "--subreddit", help="specify subreddits delimited by +",
                    action="store")
args = parser.parse_args()


subreddits = ['nootropics', 
              'nutrition', 
              'Health', 
              'FixMyDiet', 
              'Dietetics', 
              'supplements', 
              'stackadvice', 
              'afinil', 
              'drugnerds', 
              'foodnerds', 
              'caffeine', 
              'braintraining', 
              'enhance', 
              'tdcs', 
              'selfimprovement', 
              'gainit',
              'advancedfitness', 
              'steroids',
              'longevity', 
              'SENS', 
              'Futurism', 
              'Futurology', 
              'Posthumanism', 
              'Singularitarianism', 
              'Singularity', 
              'Transhuman', 
              'Transhumanism', 
              'Neurophilosophy', 
              'SFStories']

useless_words = {'1', '2', '3', '4', '5', 'actually', 'also', 'always', 'another', 'anyone', 'anything', 'around', 'back', 'bad', 'book', 'cant', 'could', 'cut', 'david', 'day', 'days', 'different', 'doesnt', 'dont', 'downvoting', '10', 'eating', 'enough', 'even', 'every', 'far', 'feel', 'find', 'first', 'future', 'get', 'getting', 'go', 'going', 'good', 'got', 'great', 'guys', 'gym', 'hard', 'help', 'high', 'human', 'id', 'ill', 'im', 'isnt', 'ive', 'keep', 'know', 'less', 'life', 'like', 'little', 'long', 'look', 'looking', 'lot', 'low', 'made', 'make', 'many', 'may', 'maybe', 'mg', 'might', 'months', 'much', 'need', 'never', 'new', 'one', 'people', 'pretty', 'probably', 'put', 'raises', 'really', 'right', 'say', 'see', 'someone', 'something', 'start', 'started', 'still', 'sub', 'sure', 'take', 'taking', 'test', 'thats', 'thing', 'things', 'think', 'though', 'time', 'try', 'two', 'us', 'use', 'using', 'want', 'way', 'week', 'weeks', 'well', 'without', 'wont', 'work', 'world', 'would', 'years', 'youre'}
useless_words = set(nltk.corpus.stopwords.words('english') + list(useless_words))

def scrape_and_extract(subreddits=subreddits):
    """
    pulls down hot 200 posts for each subreddit
    gets title, body, and comments
    returns a dict with these indexed by subreddit

    WARNING: this takes a long ass time 
    """

    r = praw.Reddit(user_agent="comment grabber for viz by /u/charliehack")

    posts_dict = {}

    for subred in subreddits:
        posts_dict[subred] = {}

        print "\n\n====================[ fetching /r/%s ...                       ]====================\n" % (subred)

        try:
            all_posts = r.get_subreddit(subred, fetch=True).get_hot(limit=None)
        except Exception:
            continue

        for p in all_posts:
            sys.stdout.write('.')
            sys.stdout.flush()
            p.replace_more_comments(limit=16)
            flat_comments_list = praw.helpers.flatten_tree(p.comments)
            posts_dict[subred][p.id] = {
                'title':p.title,
                'body':p.selftext,
                'score':p.score if len(p.selftext) > 10 else None,
                'url':p.short_link,
                'comments':{c.id: {'body':c.body, 'score':c.score} for c in flat_comments_list}}

        print "\n====================[ got %s posts.                            ]====================\n\n" % (str(len(posts_dict[subred])))

    return posts_dict


def dump_to_json(posts_dict, fpath="hot_posts.json"):
    """
    dumps crawled posts to a .json file
    """
    print "====================[ saving data to %s ...    ]=====================\n\n" % (fpath)
    
    with open(fpath, "wb") as f:
        json.dump(posts_dict, f)

    print "====================[ done.                                    ]=====================\n\n"

def load_from_json(fpath="hot_posts.json"):
    """
    loads crawled posts from .json file
    returns dict 
    """
    print "\n\n====================[ loading data from %s ... ]====================\n" % (fpath)
    
    with open(fpath, "rb") as f:
        return_dict = json.load(f)
        print "====================[ done.                                        ]=====================\n\n"
        return return_dict

def dump_text_to_json(posts_dict, fpath="data/raw/raw_text.json"):
    """
    extracts just the text from each post and its comments
    prepends a 'sentence' with just the id, for doing lookups later
    writes to a file.
    one 'body' per line (perhaps with multiple sentences.)

    """





def normalize_tokenize_string(raw_string):
    """
    take in a string, return a tokenized and normalized list of words
    """
    table = {ord(c): None for c in string.punctuation}
    assert isinstance(raw_string, unicode)
    return filter(
        lambda x: x not in useless_words, 
        nltk.word_tokenize(raw_string.lower().translate(table))
    )


def load_and_preprocess_dict(posts_dict, subreddits=['nootropics']):
    """
    normalize and tokenize text using nltk
    return a dict
    """
    processed = {}
    for subred in subreddits:
        print "normalizing /r/%s ...\n\n" % (subred)
        processed[subred] = []
        for post in posts_dict[subred]:
            sys.stdout.write('.')
            sys.stdout.flush()
            processed[subred].append(
                {
                    'title': normalize_tokenize_string(post['title']),
                    'body': normalize_tokenize_string(post['body']),
                    'comments': [normalize_tokenize_string(c) for c in post['comments']]
                }
            )

    print "\n\ndone."
    return processed


def flatten_post_to_tokens(post_dict):
    """
    post_dict -> list of tokens
    """
    return post_dict['title'] + post_dict['body'] + list(itertools.chain(*post_dict['comments']))


def flatten_dict_to_tokens(tokens_dict):
    """
    organized tokens_dict -> long list of tokens
    """
    flattened = {}
    for subred in tokens_dict.keys():
        flattened[subred] = list(itertools.chain(*[flatten_post_to_tokens(post) for post in tokens_dict[subred]]))
    return flattened

def get_freqdist(tokenized_doc):
    """
    takes in tokenized dict, concatenates all lists of terms
    returns freqdist
    """
    return nltk.FreqDist(tokenized_doc)


def build_tree(processed_dict):
    """
    taken organized tokens_dict, get freqdist, build tree with tf and sentiment values
    dump to json
    """

    fdist = get_freqdist(flatten_dict_to_tokens(processed_dict))
    nodes = fdist.most_common(200)
    tree = [['term', 'parent', 'frequency (size)', 'sentiment (color)']]
    for n in nodes:
        tree.append([n[0], '/r/nootropics', n[1], 0])

    # TODO: get sentiment

    json.dump(tree, open('data/processed/tree.json', 'wb'))



def flatten_posts_to_list(posts_dict):
    """
    we saved the posts indexed by subreddit, but we might want to train a model on the _whole damn thang_
    this flattens the dict into a single list
    """
    return [item for sublist in [posts_dict[item] for item in subreddits] for item in sublist]



if __name__ == "__main__":
    if args.subreddit is not None:
        subreddits = args.subreddit.split('+')
    if args.scrape:
        raw_posts = scrape_and_extract (subreddits=subreddits)
        dump_to_json (raw_posts, fpath='data/hot_posts_raw_with_id.json')
    else:
        raw_posts = load_from_json (fpath='data/hot_posts_raw_with_id.json')
    
    processed = load_and_preprocess_dict (raw_posts, subreddits=subreddits)
    tree      = build_tree(processed)








    
