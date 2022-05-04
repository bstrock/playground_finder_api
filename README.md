<h1>Eden Prairie Playground Finder API</h1>
This repo is for the backend component for my MS Capstone Project.  This API package is designed to serve data from the custom dataset gathered to inform the application experience, which catalogs all of the playgrounds in Eden Prairie.  Attributes include address, georeferenced playground polygons (spatial data), and inventories of equipment, amenities, and sports facilities available at each site.

<h2>Link to project demo</h2>

[View a 5 minute overview walkthrough here](https://youtu.be/jYbpUzD-KjI)
[Check out the frontend Swift app repo here](https://github.com/bstrock/tri_nearby_swift_mapkit)

<h2>Tech Stack</h2>

* FastAPI
* SQLAlchemy
* GeoAlchemy2
* Heroku (deployment)

<h2>Project Features</h2>

* Programatically generated spatial database using SQLAlchemy/GeoAlchemy2
* Fully asynchronous operations using FastAPI and SQLAlchemy 2.0 style
* Allows users to perform spatial and attribute-based queries to explore playground sites in their vicinity
* Joined table inheretance structure allows easy loading of attribute tables for storing secondary characteristics
* Complete package- one toolkit to create the database, perform ETL on the data, service queries from the endpoints, and test the API before deployment

<h2>Project Structure and Contents</h2>

```playground_api/
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
