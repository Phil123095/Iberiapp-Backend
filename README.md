# Iberiapp-Backend

## Main Modules:
### SERVER_Backend (/PythonFiles) - Hosted on AWS Lightsail:
  - api.py -> Flask Backend API. Routes to user registration, user authentication, and data pulling for the dashboard.
  - User_Manager -> Just one script, representing the User Datamodel (I know I should have used the official way of doing a user datamodel with SQLAlchemy, but I got hooked with GitHub Actions right before the deadline :D)
  - Data_APIs -> Three scripts that handle SQL generating logic (based on the frontend filters), Datacleaning, and a main file (data_retriever_clean.py)
  - Others: 
    - DockerFile (self-explanatory), 
    - getconnection.py -> Creates & returns a connection (with AWS RDS). 
### LAMBDA_DataProcessor - Runs on AWS Lambda:
  - s3dbprocessor.py -> Main function, that has the lambda_handler function to trigger the process. Is triggered by an object being added to S3. 
  - datahandling.py -> Loads the files, verifies them, and processes the data into two summary tables. 
  - DBmanager.py -> Handles **upserting** data to the Database. Upsert = Update Row if Exists OR Insert

#### .github/workflows
  - As I said before, I caught a late obsession for CI/CD and decided to build my own deployment script for Lightsail. Pretty cool stuff. Next step is using the serverles framework for Lambda, will save me a ton of time in other projects too.

P.S. Sorry for not writing a more extensive documentation, and for the 0 comments in the code. If you have any questions, feel free to reach out. 
  
