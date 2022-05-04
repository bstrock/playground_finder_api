<h1>Eden Prairie Playground Finder API</h1>
This repo is for the backend component for my MS Capstone Project.  This API package is designed to serve data from the custom dataset gathered to inform the application experience, which catalogs all of the playgrounds in Eden Prairie.  Attributes include address, georeferenced playground polygons (spatial data), and inventories of equipment, amenities, and sports facilities available at each site.

<h2>Link to live project</h2>

[epplay.today](https://epplay.today)

<h2>Project Materials</h2>

[Watch a short project overview walkthrough](https://youtu.be/EvkzLfWa2Ko)

[Check out the frontend React app repo](https://github.com/bstrock/eden_prairie_playground_finder)

[Use the interactive API documentation](https://eden-prairie-playgrounds.herokuapp.com/docs#/)

<h2> Supporting Documents</h2>

[Project Proposal](https://github.com/bstrock/playground_planner/blob/master/data/docs/Brian%20Strock%20-%20Project%20Proposal.docx)

[Project Plan](https://github.com/bstrock/playground_planner/blob/master/data/docs/Brian%20Strock%20Project%20Plan.pdf)

[Project Executive Summary](https://github.com/bstrock/playground_planner/blob/master/data/docs/Brian%20Strock%20778%20Executive%20Summary.docx)


<h2>Tech Stack</h2>

* FastAPI
* SQLAlchemy
* GeoAlchemy2
* Heroku (deployment)

<h2>API Features</h2>

* Programatically generated spatial database using SQLAlchemy/GeoAlchemy2
* Fully asynchronous operations using FastAPI and SQLAlchemy 2.0 style
* Allows users to perform spatial and attribute-based queries to explore playground sites in their vicinity
* Joined table inheretance structure allows easy loading of attribute tables for storing secondary characteristics
* Complete package- one toolkit to create the database, perform ETL on the data, service queries from the endpoints, and test the API before deployment

<h2>Project Structure and Contents</h2>

```playground_planner/
├── heroku.yml
├── Procfile
├── requirements.txt
├── api/
│       ├── __init__.py
|       ├── dependencies.py
│       ├── main.py
|       └── /routers
|           ├── __init__.py
|           ├── submit.py
|           └── users.py
├── models/
│       ├── __init__.py
│       ├── enums.py
│       ├── schemas.py
│       └── tables.py
├── utils/
│       ├── __init__.py
│       ├── create_spatial_db.py
│       └── playground_data_to_db.py
└── test/
        ├── __init__.py
        ├── conftest.py
        ├── test_api.py
        └── test_db_schema.py
        
```

`/api` contains the api source code.  uses PostGIS to process spatial queries.

`/api/routers` contains a FastAPI implementation for user authentication, using password hashing and JWTs.  Currently not implemented in the site.

`/models` contains SQLAlchemy database table models and FastAPI schemas, along with a useful utility to define and unpack custom PostgreSQL ENUM types.

`/utils`

  - `create_spatial_db.py` contains a class which offers methods to create databases with PostGIS-enabled spatial datatypes, based on the SQLAlchemy models defined in `models/tables.py`
  - `playground_data_to_db.py` uses pandas and sqlalchemy models to perform ETL operations on the playground data and imports it into the database, including the spatial data components.

`/test` Contains an extensive pytest test suite, which provides a continuous integration testing baseline to ensure efficient API development
