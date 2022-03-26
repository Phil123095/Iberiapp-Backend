import boto3
import pandas as pd
import io
import data_handling as dh
import DB_manager as db


def load_codes(s3_client, bucket, filepath):
    object = s3_client.get_object(Bucket=bucket, Key=filepath)
    df = pd.read_excel(io.BytesIO(object['Body'].read()), header=0)
    df = df.drop(columns=['Departamento Desc.']).set_index('Departamento Código')
    code_to_departments = df.to_dict()['Ruta Departamentos - Desc.2']
    return code_to_departments


def lambda_handler(event, context):
    # Let's use Amazon S3
    s3 = boto3.client("s3", aws_access_key_id='AKIAVFTGGPRVW2HU76QT',
                            aws_secret_access_key='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',
                            region_name="eu-central-1")

    bucket = 'iberiapp-files'
    orgmap_file = '../Archive/Data_Processor/org_map.xlsx'

    dept_codes = load_codes(s3_client=s3, bucket=bucket, filepath=orgmap_file)
    database = db.DBManager()
    handle_file = dh.FileHandler(codes=dept_codes, s3_handler=s3, s3_bucket=bucket)
    handle_file.clean_files()

    database.report_to_db(handle_file)
    return
