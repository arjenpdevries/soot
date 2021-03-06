from flask import Flask, render_template, request , redirect, session
from soot.backend import *

app = Flask(__name__)

global masto


def is_authenticated():
    return session.get('access_token') is not None


@app.route('/')
def index():
    return render_template('index.html', results=[], registered=is_authenticated())


@app.route('/register')
def register():
    return redirect(creds.sent_oauth_register())




@app.route('/authenticate')
def authenticate():
    auth_code = request.args['access_token']
    masto = creds.dummy_masto()
    access_token = masto.log_in(code=auth_code, scopes=['read'], to_file="soot.token")
    session['access_token'] = access_token
    return redirect('/')



@app.route('/logout')
def logout():
    session.__delitem__('access_token')
    masto = creds.dummy_masto()
    return render_template('index.html', results=[], query=None, registered=is_authenticated())





@app.route('/query')
def query():
    query_raw = request.args['q'].split(" ")
    masto = creds.create_masto(session['access_token'])
    user_interface = TootInterface(masto)

    # Fetch the search query
    print("searching for terms: ", query_raw)

    # parameters for the information retrieval model (BM25)
    query_terms = [q.lower() for q in query_raw]  # normalize query terms for searching


    # Create search model and initialize statistics
    # Currently only statistics for this query are collected
    searcher = Searcher()
    searcher.seed_background_model(user_interface.getHomeToots(), query_terms)

    def getVerb(toot):
        if toot['reblog'] is not None:
             return "boosted"
        elif (toot['in_reply_to_id'] is not None):
            return "replied"
        else:
            return "tooted"


    # rank toots by relevance
    scoredToots = searcher.rank(user_interface.getHomeToots(), query_terms)
    # for (toot, score) in scoredToots[0:10]:
    #     print(toot)


    toot_ranking = [{'content': toot['content']
                        , 'author': toot['account']['username']
                        , 'uri':toot['url']
                        , 'verb':getVerb(toot)
                     } for (toot,score) in scoredToots if not toot['muted']]


    return render_template('index.html', toots=toot_ranking, query=request.args['q'], base_url=creds.domain, registered=is_authenticated())


def main():
    global creds

    creds = Credentials("mastodon.social")
    if not creds.is_client_registered():
        creds.client_register()

    app.secret_key = creds.get_secret_session_key()
    app.run(host="0.0.0.0")

if __name__ == '__main__':
    main()
