from flask import Flask, render_template, request, session
from onto_app import app, db
import os

from flask import send_file, send_from_directory, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import json


@app.route('/', methods=["GET", "POST"])
def hello():
    if request.method == 'GET' :
        print("GET")
    if request.method == 'POST' :
    
        """ Returning name and type of links. Does not update with objects. Bias for new yet to be set, will be done so when more of the backend for it is built. """
        a = str(request.data).split(',')    
        temp_buffer = a[0]
        temp_buffer2 = a[1]
        decision  = a[2]

        print(decision[12:-3])

        i = 0
        try:
            while temp_buffer[i] != '>':
                i += 1
        except:
            print(i)
        
        if temp_buffer[-5 :-1] == '</a>' : 
            print(temp_buffer[i+1:-5])
        else  :
            print(temp_buffer[i+1:-8])

        print(temp_buffer2[8 : -1])
        """ End of preliminary return of accept return. """ 

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

@app.route("/loadOntology/<path:filename>", methods = ['GET', 'POST'])
def loadOntology(filename) : 
    uploads = os.path.join(current_app.root_path,"OntoData")
    uploads = uploads + "/" + str(filename) 

    try :
        with open(uploads[:-1],"r") as json_data:
            contents = json.load(json_data)
            print(contents)
    except :
        flash('Oops record not found')
        return redirect(url_for('hello'))
    # contents = f.read()

    # print(contents)
    #return redirect(url_for('hello'))
    return render_template("index.html", OntologyContentJson = contents)