from pymongo import MongoClient
from config import settings
import boto3
from botocore.exceptions import ClientError

def get_secret():

    secret_name = settings.secret_mongo_db
    region_name = settings.region

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # El secreto es la cadena de conexión que guardamos con Terraform.
    # Debemos devolver solo esta cadena, no el objeto completo.
    return get_secret_value_response['SecretString']


# Creaa la conexion a la base de datos MongoDB
client = MongoClient(get_secret())
db = client[settings.mongo_db]