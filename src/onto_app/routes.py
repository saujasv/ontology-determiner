from flask import Flask, render_template, request, session
from onto_app import app, db
import os

from flask import send_file, send_from_directory, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import json
from onto_app.onto import *

@app.route('/', methods=["GET", "POST"])
def hello():
    if request.method == 'GET' :
        add_onto_file(1, "pizza", "./data/owl/pizza.owl", "./data/json/pizza.json", "./data/new/pizza.txt")
        return "Pizza ontology has been added"
    if request.method == 'POST' :
    
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

@app.route('/decision', methods=["POST"])
def decision() : 
    if request.method == 'POST' : 
        """ Decisions stored """
        data = str(request.data).split(',')
        print(data)
        Prop = data[0][11:-1]
        Type = data[4][8:-1]
        Decision  = data[1][12:-1]
        Domain = data[2][10:-1]
        Range = data[3][9:-1]

        print("Prop : ", Prop) 
        print("Domain : ", Domain)
        print("Range : ", Range) 
        print("Decision : ", Decision) 
        print("Type : ", Type)
        user_id = 1
        onto_id = 1
        add_decision(user_id, Prop, Domain, Range, Type, onto_id, {'Accept': 1, 'Reject':0}[Decision])

    return render_template("index.html")


# prevent cached responses
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "-1"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/return-files/<path:filename>/', methods = ['GET', 'POST'])
def return_files(filename):
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    try:
        print("######################################")
        uploads = os.path.join(current_app.root_path, "OntoData") # change with a app.config thing
        print(uploads)
        
        # f = open(uploads + '/' + filename + '1' , 'w')
        # f.write(a)
        # print(repr(a))
        # f.close()
        return send_from_directory(uploads, filename,as_attachment=True, attachment_filename=filename)
    except Exception as e:
        return str(e)

    # @app.route('/uploadfile/')
    # def upload_files(filename) :
    #     try :
    # @app.route('/uploadFile/', methods=['GET', 'POST'])
    # def upload_file():
    #     if request.method == 'POST':
    #         # check if the post request has the file part
    #         if 'file' not in request.files:
    #             flash('No file part')
    #             return redirect(request.url)
    #         file = request.files['file']
    #         # if user does not select file, browser also
    #         # submit an empty part without filename
    #         if file.filename == '':
    #             flash('No selected file')
    #             return redirect(request.url)
    #         if file:
    #             filename = secure_filename(file.filename)
    #             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #             return redirect(url_for('uploaded_file',
    #                                     filename=filename))

@app.route("/loadOntology/<path:filename>/", methods = ['GET', 'POST'])
def loadOntology(filename) : 
    uploads = os.path.join(current_app.root_path,"data/json")
    uploads = uploads + "/" + str(filename) 

    fname = str(filename) 
    fname = fname.split(".")[0]
    fname = fname + ".txt"
    new_relations = get_new_relations(os.path.join(current_app.root_path,"data/new")+ "/" + fname)
    print(new_relations)

    try :
        with open(uploads,"r") as json_data:
            contents = json.load(json_data)
            # print(contents)
    except :
        flash('Oops record not found')
        return redirect(url_for('hello'))

    # try :
    #     with open(new_relations[:-1],"r") as json_data:
    #         NewRelcontents = json.load(json_data)
    #         print(NewRelcontents)
    # except :
    #     flash('Oops new rel text not found')
    #     return redirect(url_for('hello'))

    # contents = f.read()

    # print(contents)
    #return redirect(url_for('hello'))
    return render_template("index.html", OntologyContentJson = contents, hiddenJSON = new_relations)