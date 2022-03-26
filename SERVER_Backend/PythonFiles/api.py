from flask import Flask, request
import json
from flask_cors import CORS
from User_Manager.user_manager import User
from Data_APIs.data_retriever_clean import get_data
from getconnection import get_db_connections
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, jwt_required, JWTManager

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = "hello-change-me"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)
DB_engine = get_db_connections(local=False)
CORS(app)

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response

    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@app.route("/authenticate-user", methods=["POST"])
def auth_user():
    action_inputs = request.json
    user = User(
        DB_connection=DB_engine,
        email=action_inputs['email'],
        password=action_inputs['password']
        )
    result = user.authenticate()

    if result['user_exist'] and result['password_correct']:
        token = create_access_token(identity=action_inputs['email'])
        print(token)
        result['access_token'] = token
        print(result)
    return result


@app.route("/new-user", methods=["POST"])
def new_user():
    action_inputs = request.json
    user = User(
        DB_connection=DB_engine,
        email=action_inputs['email'],
        password=action_inputs['password']
    )
    result = user.create_credentials()
    return result


@app.route("/get-dashboard-data", methods=["POST"])
@jwt_required()
def all_dashboard_data():
    current_user = get_jwt_identity()
    input_params = request.json
    start_date = input_params['start_date']
    end_date = input_params['end_date']
    customer_comp_group = input_params['customer_group']
    granularity = input_params['granularity']
    data = get_data(connection=DB_engine, start_date=start_date,
                    end_date=end_date, customer_company_group=customer_comp_group, granularity=granularity)
    data['logged_in_as'] = current_user
    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
