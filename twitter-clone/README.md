# Twitter-Clone

This project implements back-end service for microblog clone of Twitter social
network.

How does it work? ⤵

![demo](/readme_support/demo.gif)

***

<!-- Actions and Technologies -->
***Actions***<br>
Any User registered in the Twitter-Clone can perform these actions easily:

    * Add a new tweet;
    * Delete own tweet;
    * Follow / Unfollow other user;
    * Like / Unlike a tweet of other user;
    * Attach a picture to the tweet;
    * Show own feed with tweets sorted by following user names (ascent alphabetically)
    and the most popular tweets (descent by likes amount);

***
***Technologies***

- Server back-end: FastApi (asynchronous)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Static Server: NGINX
- Deployment: Docker

***


<!-- Installation and Run-->

## Installation and Run

Running the project:

    1. Clone repository
    2. Create virtual environment for the repository: python -m venv venv
    3. Activate virtual environment: source venv/bin/activate (for MacOS)
    4. Install dependencies: pip install -r project/server/main/requirements.txt
    5. Run Docker service
    6. Run docker-compose "yml" files in root directory:
        6.1 development environment (with .env.dev): 
            "docker compose -f docker-compose.yml up -d"
        6.2 testing environment (with .env.test):
            6.2.1 run test application: "docker compose -f docker-compose-test.yml up -d"
            6.2.2 navigate to "project/tests" directory
            6.2.3 run tests: "pytest" (complete set), "pytest -m <mark_name> (by marks from pytest.ini)
    7. Access "http://localhost:8080/" in browser
    8. Access to user's data via construction panel using user-api values (u1, u2, u3, test)
    created as dummy in database.


***NOTE*** This project keeps the database and all tweet data stored even if
the server  shutdown or restarted by any reason.
Run these steps in command line if you want to reset the database completely:

    1. docker-compose down -v --rmi all (+ docker system prune -a)
    2. Run a desired configuration in command line (see item 3 above)

<!-- User Manual -->

## Manual

Endpoint's documentation (while application is running): [Get Endpoints Description](http://localhost:8080/docs) <br>
Program Releases: [Get Release Description](./TBD)

<!-- Dependencies -->

## Dependencies

This program depends on interpreter Python 3.10 or higher.<br>
A list of dependencies: [Get Dependencies](./project/server/requirements.txt)

<!-- Support -->

## Support

If you have questions or any difficulties with running this project create
[Discussion](https://github.com/) in current repository or email
to <murashkin.dv@gmail.com>.

## Special Thanks To

***SkillBox Team*** who supported me to create this masterpiece backend! :)
