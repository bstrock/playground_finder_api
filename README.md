# tri-app

Example backend API designed to read data from US EPA TRI datasets, extract/transform/load relevant data, then serve requests from the app's frontend component to inform user queries and accept user reports about individual sites.

The API is currently live and deployed via Heroku.

CONTENTS:

/api:  contains the api source code.  uses PostGIS to process spatial queries.

/models: contains SQLAlchemy database table models and FastAPI schemas.

/utils:

  - create_spatial_db.py contains a class which offers methods to create databases with PostGIS-enabled spatial datatypes.
  - tri_loader.py uses pandas and sqlalchemy models to perform ETL operations on TRI Data and imports them into the spatial database
  - test.py contains an extensive test suite, which provides a continuous integration testing baseline to ensure efficient API development
  
  
