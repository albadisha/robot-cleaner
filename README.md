# Robot Cleaner Backend

Backend service that simulates a robot cleaning an office.

## Tech Stack

The service uses Flask framework for the api, SqlAlchemy as an ORM, Alembic for database migrations and Poetry to manage dependencies. 

## How to run

Make sure to have Docker (*version >= 24.0.0*) and Docker-Compose (*version >= 2.19.0*) installed in your machine.

Set the proper env variables:

```
export POSTGRES_HOST=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_DB=robot_db
export POSTGRES_PORT=5432
export AUTH_API_KEY=production-api-token
export IS_PRODUCTION=false
```
I have included a .localenv file with the right variables for easibility so you can also do:

```
source .localenv
```

### Run the backend server

```
docker-compose -f deploy.yml up --build
````

After setting up you can send api requests to: `localhost:5555`

To clean up the resources that were used for *deployment* run:
```
docker-compose -f deploy.yml down
```

### Run tests

```
docker-compose -f test.yml up --build
````

To clean up the resources that were used for *testing* run:
```
docker-compose -f test.yml down
```

## Notes
Ideally tests should run as a preliminary step in a CI/CD pipeline before deploying new changes. I have included a small example for linting with github actions.

Production environment variables won't be included in the repo in a real case scenario.

You can import the src/api.yaml file in swagger editor to check api specifications.
