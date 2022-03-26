from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, DB_connection, email, password, new_email=None, new_password=None):
        self.email = email
        self.new_email = new_email if new_email else None
        self.password = password
        self.new_password = new_password if new_password else None

        self.engine = DB_connection

    def __execute_query(self, query, return_data):
        """
        :param query: Formatted query string provided by caller
        :param return_data: Boolean. True = Fetches Row (ex. for authentication), False = Upload Data
        :return: Result if return_data = True
        """
        with self.engine.connect() as conn:
            if return_data:
                result = conn.execute(query).fetchone()
                return result
            else:
                try:
                    conn.execute(query)
                    return True
                except ConnectionError:
                    return False

    def check_if_exists(self):
        query = f"""
            select ID
            from ti_users
            where email = '{self.email}'
        """
        user = self.__execute_query(query, True)

        if user:
            return {'RespCode': 200, 'user_exists': True}

        else:
            return {'RespCode': 200, 'user_exists': False}

    def create_credentials(self):
        query = f"""
            insert into ti_users (email, hashed_password)
            values ('{self.email}', '{generate_password_hash(self.password)}')
            """
        result = self.check_if_exists()

        if result['user_exists']:
            return {'RespCode': 200, 'message': 'user_already_exists'}

        else:
            query_success = self.__execute_query(query=query, return_data=False)
            if query_success:
                return {'RespCode': 200, 'message': 'user_created_successfully'}
            else:
                return {'RespCode': 400, 'message': 'SQL error'}

    def authenticate(self):
        query = f"""
                select ID, hashed_password
                from ti_users
                where email = '{self.email}'
            """

        user = self.__execute_query(query=query, return_data=True)

        if user:
            if check_password_hash(user[1], self.password):
                return {'RespCode': 200, 'user_exist': True, 'password_correct': True}
            elif not check_password_hash(user[1], self.password):
                return {'RespCode': 200, 'user_exist': True, 'password_correct': False}

        elif not user:
            return {'RespCode': 200, 'user_exist': False}

    def modify_credentials(self):
        update_query_pwd = f"""
                UPDATE ti_users
                SET email='{self.email if self.new_email is None else self.new_email}', 
                hashed_password='{
                    generate_password_hash(self.password) if self.new_password is None
                    else generate_password_hash(self.new_password)}'
                WHERE email = '{self.email}'
        """

        auth_result = self.authenticate()

        if auth_result['user_exist']:
            if auth_result['password_correct']:
                query_result = self.__execute_query(query=update_query_pwd, return_data=False)
                if query_result:
                    auth_result['user_updated'] = True
                    return auth_result
                else:
                    auth_result['user_updated'] = False
                    return auth_result
            else:
                return auth_result