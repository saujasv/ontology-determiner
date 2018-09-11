import os

from flask import Flask, request, render_template


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
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

    return app
