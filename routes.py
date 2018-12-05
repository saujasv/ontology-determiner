from flask import Flask, render_template, request, session
from onto_app import app, db
import os

from flask import send_file, send_from_directory, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
import json
from onto_app.onto import *

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.oauth2 import id_token
from google.auth.transport import requests

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret_395200844618-bnei4qvc8203ieoic6hpkbrkdnvmdq49.apps.googleusercontent.com.json"
CLIENT_ID = "395200844618-bnei4qvc8203ieoic6hpkbrkdnvmdq49.apps.googleusercontent.com"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/plus.me", "https://www.googleapis.com/auth/userinfo.profile"]
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

# prevent cached responses
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "-1"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/')
def home():
    add_new_ontologies()
    return render_template('login.html')

""" Loads ontology to database """
@app.route('/hello', methods=["GET", "POST"])
def hello():
    if request.method == 'GET' :
        add_onto_file(1, "pizza", "./data/owl/pizza.owl", "./data/json/pizza.json", "./data/new/pizza.txt")
        return "Pizza ontology has been added to database"
    if request.method == 'POST' :
        """ Remanants of testing code, will be removed later when they will be no longer be used with certainity. """
        """ Returning name and type of links. Does not update with objects. Bias for new yet to be set, will be done so when more of the backend for it is built. """
        a = str(request.data).split(',')
        Prop = a[0]
        Type = a[1]
        Decision  = a[2]
        Domain = a[3]
        Range = a[4]

        print(Decision[12:-3])

        i = 0
        try:
            while Prop[i] != '>':
                i += 1
        except:
            print(i)

        if Prop[-5 :-1] == '</a>' :
            print(Prop[i+1:-5])
        else  :
            print(Prop[i+1:-8])

        print(Type[8 : -1])
        """ End of preliminary return of accept return. """

    return render_template("index.html")

@app.route('/login', methods=["GET"])
def login():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = url_for('authenticated', _external=True)

    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      prompt='consent',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

@app.route('/authenticated')
def authenticated():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('authenticated', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    s = flow.authorized_session()
    idinfo = s.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    userid = idinfo['sub']
    email = idinfo['email']
    # print("Hello", userid, email)
    result = db.engine.execute("SELECT * FROM users WHERE id = :id", {'id': userid})
    if not result.fetchone():
        db.engine.execute("""INSERT INTO users (id, username, privilege) VALUES
                            (:id, :username, :privilege)""", {'id': userid, 'username': email, 'privilege': 0})
    session['userid'] = userid
    session['username'] = email

    return redirect(url_for('user'))

@app.route('/user')
def user():
    if not 'credentials' in session:
        return redirect(url_for('home'))

    ontologies = get_ontologies_on_server()

    try:
        add_onto_file(1, "pizza", "./data/owl/pizza.owl", "./data/json/pizza.json", "./data/new/pizza.txt")
    except:
        pass
    # return redirect(url_for('loadOntology', filename='pizza.json'))
    return render_template("ontologies.html", ontologies=ontologies, username=session['username'])

@app.route('/logout')
def logout():
    if 'credentials' in session:
        del session['credentials']
        del session['username']
        del session['userid']
    return redirect(url_for('home'))

""" Stores decisions taken in frontend corresponding to relationships accept/reject into database """
@app.route('/decision', methods=["POST"])
def decision() :
    if request.method == 'POST' :
        """ Decisions stored """
        """ Index numbers used to extract specific content from already existing inner html. This will hold through across cases."""
        data = str(request.data).split(',')
        # if flag is 1, then relation, else node
        user_id = session['userid']
        onto_id = session['ontology']
        print(data)
        if data[0][-1] == "1" :
            #when a relationship is accepted/rejected
            Prop = data[1][8:-1]
            Type = data[5][8:-1]
            Decision  = data[2][12:-1]
            Domain = data[3][10:-1]
            Range = data[4][9:-1]

            print("Prop : ", Prop)
            print("Domain : ", Domain)
            print("Range : ", Range)
            print("Decision : ", Decision)
            print("Type : ", Type)

            """ Call add_decision from onto.py to store decision """
            if Prop == "Subclass of" :
                add_relation_decision(user_id, None, Domain, Range, str(RDFS.subClassOf), onto_id, {'Accept': 1, 'Reject':0}[Decision] )
            else :
                add_relation_decision(user_id, Prop, Domain, Range, Type, onto_id, {'Accept': 1, 'Reject':0}[Decision])

        elif data[0][-1] == "0" :
            # When a node is accpeted or rejected.
            name = data[1][8:-1]
            Decision = data[2][12:-1]

            # print("Name : ", Name)
            # print("Decision :", Decision)

            """ Call add_decision on node from onto.py to store decision """
            add_node_decision(user_id, name, onto_id, {'Accept': 1, 'Reject':0}[Decision])

    return render_template("index.html")


""" Serve file and new relationships from backend corresponding to the filename given in the URL """
@app.route("/loadOntology/<path:file>/", methods = ['GET'])
def loadOntology(file) :
    """ Serve files and new relations from the backend """
    """ Ontologies ready to be rendered saved in data/json """

    if 'credentials' not in session:
        return redirect('login')

    filename = file + '.json'
    uploads = os.path.join(current_app.root_path,"data/json")
    uploads = uploads + "/" + str(filename)

    fname = str(filename)
    fname = fname.split(".")[0]
    fname = fname + ".txt"

    result = db.engine.execute("SELECT id FROM ontologies WHERE name = :name", {'name': file})
    onto_id = result.fetchone()['id']
    session['ontology'] = onto_id
    """ Corresponding new relations for given ontology are stored in data/new. """

    # new_relations, new_nodes = get_new_relations(os.path.join(current_app.root_path,"data/new")+ "/" + fname)
    # print(new_relations)
    result = db.engine.execute("""SELECT * FROM class_relations WHERE quantifier != :subclass""",
        {'subclass': str(RDFS.subClassOf)})
    new_relations = [(r['domain'], r['property'], r['quantifier'], r['range']) for r in result.fetchall()]

    result = db.engine.execute("""SELECT * FROM nodes""")
    new_nodes = [n['name'] for n in result.fetchall()]

    result = db.engine.execute("""SELECT * FROM class_relations WHERE quantifier = :subclass""",
        {'subclass': str(RDFS.subClassOf)})
    new_subclasses = [(r['domain'], r['range']) for r in result.fetchall()]
    # print(new_subclasses)

    try :
        with open(uploads,"r") as json_data:
            contents = json.load(json_data)
            # print(contents)
    except :
        flash('Oops record not found')
        return redirect(url_for('hello'))

    # print(new_relations) 

    return render_template("index.html", OntologyContentJson=contents, hiddenJSONRel=new_relations, 
                        hiddenJSONNode=new_nodes, hiddenJSONSubclass=new_subclasses,
                        userId=session['userid'], username=session['username'] )


# @app.route('/return-files/<path:filename>/', methods = ['GET', 'POST'])
# def return_files(filename):
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#     try:
#         print("######################################")
#         uploads = os.path.join(current_app.root_path, "OntoData") # change with a app.config thing
#         print(uploads)

#         # f = open(uploads + '/' + filename + '1' , 'w')
#         # f.write(a)
#         # print(repr(a))
#         # f.close()
#         return send_from_directory(uploads, filename,as_attachment=True, attachment_filename=filename)
#     except Exception as e:
#         return str(e)

#     # @app.route('/uploadfile/')
#     # def upload_files(filename) :
#     #     try :
#     # @app.route('/uploadFile/', methods=['GET', 'POST'])
#     # def upload_file():
#     #     if request.method == 'POST':
#     #         # check if the post request has the file part
#     #         if 'file' not in request.files:
#     #             flash('No file part')
#     #             return redirect(request.url)
#     #         file = request.files['file']
#     #         # if user does not select file, browser also
#     #         # submit an empty part without filename
#     #         if file.filename == '':
#     #             flash('No selected file')
#     #             return redirect(request.url)
#     #         if file:
#     #             filename = secure_filename(file.filename)
#     #             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#     #             return redirect(url_for('uploaded_file',
#     #                                     filename=filename))
