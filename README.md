# Ontology Determiner

# Setup
- Ensure `python3` and `pip` are installed
- Open the `src` folder in the terminal, and run `pip install -r requirements.txt` to install the required Python modules

# Starting the server
- `cd` to the `onto_app` directory and set `FLASK_APP=routes.py`
- Start the server with `flask run`
    - You can set the host using the `--host=X.X.X.X` flag, and the port with `--port=X`
    - You may choose to deploy the flask application in a different way

# Preparing an ontology to be served
- Two files are required. The first is the OWL file that has to be verified, and the other file is a
text file that identifies the new relationships in the ontology.
- The OWL file has to be placed in the `data/owl/` directory, and the text file in `data/new/` directory.
- To generate the text file, the new RDF triples in the file need to be identified. These RDF triples
can be accessed by opening the OWL file using an RDF processing library like RDFLib in Python. 
- Once the new triples have been identified, the triples should be written into a file, one triple per line,
and a single space separating each element of the triple.
    - NOTE: The file in /data/owl should be named `<file>.owl`, and the file in `/data/new/` `<file>.txt`. The names
        of the file **have to be the same, except for extension.**
- Once the files have been placed in the respective folders, they will be loaded into the database when
    the `/` route is visited. They are then accessible to an expert.

# Getting a verified ontology once users have decided
- To apply changes based on decisions made by experts, the following command has to be executed:
    `python get_verified_ontology.py <ontology_name>`
- `ontology_name` is the name of the ontology file in `/data/owl/` without the `.owl` extension. Once the script
    is run, the new `.owl` file will be stored in `/data/final/`. 
    - NOTE: **The new relations file `/data/new` will not be changed on running the script.** The database will be 
    updated to remove those relations which have been decided upon by at least one 
    expert. **The file in `/data/owl/` will not change.**

# Changing the WebVOWL interface code
- To update/make changes to the visualization software, WebVOWL, the source code of the WebVOWL software being used needs to be updated,
and all necessary files need to be rebuilt into the deploy directory of the WebVOWL folder, which itself is located inside the src folder.
- Run `npm run-script release` to (re-)build all necessary files into the deploy directory.
- The new files created in the deploy directory of WebVOWL must then be transferred into src/onto_app/static/js for javascript updated, and src/onto_app/static/css for updating CSS.
- To see these changes reflected now, refresh window on which app is being viewed.
- For any further queries regarding the visualization software, please visit https://github.com/AnirudhaRamesh/Ontology-Determiner/tree/master/SSAD22/src/WebVOWL 

# Changing the way decisions are written into OWL files
- The code for writing changes into OWL files now resides in `src/OWL_JARS`
- The `Class_Removal` folder contains code to remove a class definition axioms and all class reference axioms pertaining to a specified class
- The `Restriction_Removal` folder contains code to remove a specified restriction on a property
- The `SubClass_Removal` folder contains code to remove a specified subclass axiom
- The instructions for compiling the code to `.jar` files and using the JARs to execute are in `src/OWL_JARS/Instructions.txt`

