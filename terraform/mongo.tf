resource "aws_docdb_cluster" "amaris_docdb" {
  cluster_identifier      = "amaris-docdb-cluster"
  engine                  = "docdb"
  master_username         = "amarisadmin"
  master_password         = aws_secretsmanager_secret_version.mongo_secret_version.secret_string
  db_subnet_group_name    = aws_docdb_subnet_group.amaris_docdb_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.amaris_docdb_sg.id]
  skip_final_snapshot     = true
  tags = {
    Name       = "amaris-docdb-cluster"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

# Subnet 1 en la primera zona de disponibilidad
resource "aws_subnet" "amaris-subnet-public-az1" {
  vpc_id            = aws_vpc.amaris-vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1d"
  tags = {
    Name = "amaris-subnet-public-az1"
  }
}

# Subnet 2 en la segunda zona de disponibilidad para alta disponibilidad de DocDB
resource "aws_subnet" "amaris-subnet-public-az2" {
  vpc_id            = aws_vpc.amaris-vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1e"
  tags = {
    Name = "amaris-subnet-public-az2"
  }
}

resource "aws_docdb_subnet_group" "amaris_docdb_subnet_group" {
  name       = "amaris-docdb-subnet-group"
  subnet_ids = [
    aws_subnet.amaris-subnet-public-az1.id,
    aws_subnet.amaris-subnet-public-az2.id
  ]
  tags = {
    Name = "amaris-docdb-subnet-group"
  }
}

resource "aws_security_group" "amaris_docdb_sg" {
  name        = "amaris-docdb-sg"
  description = "Allow traffic to DocDB"
  vpc_id      = aws_vpc.amaris-vpc.id

  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.amaris-public-http-traffic.id]
  }

  tags = {
    Name = "amaris-docdb-sg"
  }
}

resource "random_password" "mongo_password" {
  length           = 16
  special          = true
  override_special = "_%@"
}

resource "aws_security_group" "lambda_sg" {
  name        = "amaris-lambda-seeder-sg"
  description = "SG for Lambda seeder in VPC"
  vpc_id      = aws_vpc.amaris-vpc.id

  # Lambda necesita salida hacia DocDB (dentro de la VPC)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "amaris-lambda-seeder-sg" }
}

# 2) Permite que ESA Lambda entre al puerto 27017 del DocDB
#    (agregamos este SG como fuente al SG del cluster)
resource "aws_security_group_rule" "docdb_ingress_from_lambda" {
  type                     = "ingress"
  from_port                = 27017
  to_port                  = 27017
  protocol                 = "tcp"
  security_group_id        = aws_security_group.amaris_docdb_sg.id
  source_security_group_id = aws_security_group.lambda_sg.id
  description              = "Lambda seeder to DocDB 27017"
}

# 3) Role y políticas para Lambda
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "amaris-lambda-seeder-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Básico de ejecución + logs
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Acceso a VPC
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lectura de Secrets Manager
resource "aws_iam_role_policy" "lambda_secrets_read" {
  name = "lambda-secrets-read"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "ReadMongoSecret",
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = aws_secretsmanager_secret.mongo_secret.arn
      }
    ]
  })
}

# 4) Descarga del bundle TLS para DocDB (RDS CA)
data "http" "rds_ca_bundle" {
  url = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
}

# 5) Construcción del paquete de la Lambda (zip) con pymongo y handler
#    - Crea una carpeta ./lambda_build con dependencias y handler
#    - Requiere que tengas Python y pip disponibles localmente.
#    - Si usas Apple Silicon, esto igual funciona (pymongo puro Python).
resource "null_resource" "build_lambda_zip" {
  # Si el endpoint cambia o el bundle CA cambia, podríamos reconstruir
  triggers = {
    rds_ca_sha = sha1(data.http.rds_ca_bundle.response_body)
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      BUILD_DIR="${path.module}/lambda_build"
      rm -rf "$BUILD_DIR"
      mkdir -p "$BUILD_DIR"

      # Guardar el bundle TLS
      echo '${replace(data.http.rds_ca_bundle.response_body, "'", "'\\''")}' > "$BUILD_DIR/global-bundle.pem"

      # Crear requirements y handler
      cat > "$BUILD_DIR/requirements.txt" << 'REQ'
pymongo==4.7.3
REQ

      cat > "$BUILD_DIR/handler.py" << 'PY'
import os
import json
import base64
import boto3
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import botocore

def get_secret(secret_id: str) -> str:
    sm = boto3.client("secretsmanager")
    resp = sm.get_secret_value(SecretId=secret_id)
    if "SecretString" in resp:
        return resp["SecretString"]
    return base64.b64decode(resp["SecretBinary"]).decode("utf-8")

def lambda_handler(event, context):
    """
    Ejecuta el seed de la colección 'funds' en el DB 'amaris' (o el que venga en event["db_name"]).
    Requiere:
      - event["cluster_endpoint"]  (p.ej. docdb-xxx.cluster-xxxxxx.us-east-1.docdb.amazonaws.com)
      - event["secret_id"]         (nombre/ARN del secret con la password)
      - event.get("db_name", "amaris")
      - event.get("username", "amarisadmin")
    """
    cluster_endpoint = event["cluster_endpoint"]
    secret_id        = event["secret_id"]
    db_name          = event.get("db_name", "amaris")
    username         = event.get("username", "amarisadmin")

    # Leer password del secret
    password = get_secret(secret_id)

    # Ruta al bundle TLS empaquetado
    ca_path = os.path.join(os.path.dirname(__file__), "global-bundle.pem")

    # Simplifica la cadena de conexión a una sola línea
    mongo_uri = f"mongodb://{username}:{password}@{cluster_endpoint}:27017/?tls=true&tlsCAFile={ca_path}&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"

    client = None
    try:
        print(f"Connecting to MongoDB at {cluster_endpoint}:27017 (TLS)")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
        client.admin.command('ismaster')
        print("MongoDB connection successful.")

        db = client[db_name]
        coll = db["funds"]

        if coll.count_documents({}) > 0:
            msg = "Funds collection already has data. Skipping."
            print(msg)
            return {"status": "ok", "message": msg}

        funds_data = [
            {"fund_id": 1, "name": "FPV_BTG_PACTUAL_RECAUDADORA", "min_amount": 75000,  "category": "FPV"},
            {"fund_id": 2, "name": "FPV_BTG_PACTUAL_ECOPETROL",  "min_amount": 125000, "category": "FPV"},
            {"fund_id": 3, "name": "DEUDAPRIVADA",               "min_amount": 50000,  "category": "FIC"},
            {"fund_id": 4, "name": "FDO-ACCIONES",               "min_amount": 250000, "category": "FIC"},
            {"fund_id": 5, "name": "FPV_BTG_PACTUAL_DINAMICA",   "min_amount": 100000, "category": "FPV"},
        ]
        res = coll.insert_many(funds_data)
        msg = f"Inserted {len(res.inserted_ids)} docs into '{db_name}.funds'"
        print(msg)
        return {"status": "ok", "message": msg}

    except (ConnectionFailure, OperationFailure) as e:
        print(f"Mongo error: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if client:
            client.close()
PY

      # Instalar dependencias vendorizadas
      python3 -m pip install --upgrade pip >/dev/null
      python3 -m pip install -r "$BUILD_DIR/requirements.txt" -t "$BUILD_DIR" >/dev/null
    EOT
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_build"
  output_path = "${path.module}/lambda_seeder.zip"

  depends_on = [null_resource.build_lambda_zip]
}

# 6) Crear Lambda en VPC
resource "aws_lambda_function" "docdb_seeder" {
  function_name = "amaris-docdb-seeder"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout = 100

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = [
    aws_subnet.amaris-subnet-public-az1.id,
    aws_subnet.amaris-subnet-public-az2.id
    ]
  }

  environment {
    variables = {
      # (Opcional) por si quieres defaults en el código
      DEFAULT_DB = "amaris"
    }
  }

  depends_on = [
    aws_security_group_rule.docdb_ingress_from_lambda
  ]

  tags = { Name = "amaris-docdb-seeder" }
}

resource "null_resource" "invoke_seed" {
  # Triggers never change => se ejecuta una vez y luego queda estable
  triggers = {
    run_once = "true"
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Add a wait period to ensure the Lambda is fully available
      echo "Waiting 20 seconds for Lambda to be ready..."
      sleep 20
      
      # The rest of your command remains the same
      aws lambda invoke \
        --function-name ${aws_lambda_function.docdb_seeder.function_name} \
        --payload '{"cluster_endpoint":"${aws_docdb_cluster.amaris_docdb.endpoint}","secret_id":"${aws_secretsmanager_secret.mongo_secret.id}","db_name":"amaris","username":"${aws_docdb_cluster.amaris_docdb.master_username}"}' \
        --cli-binary-format raw-in-base64-out \
        "${path.module}/lambda_invoke_output.json" >/dev/null
      echo "Seed invoked."
    EOT
  }

  depends_on = [aws_lambda_function.docdb_seeder]
}

# (Opcional) Output útil
output "docdb_endpoint" {
  value = aws_docdb_cluster.amaris_docdb.endpoint
}

output "seeder_lambda_name" {
  value = aws_lambda_function.docdb_seeder.function_name
}


resource "aws_secretsmanager_secret" "mongo_secret" {
  name = "MONGO_SECRET"
}

resource "aws_secretsmanager_secret_version" "mongo_secret_version" {
  secret_id     = aws_secretsmanager_secret.mongo_secret.id
  secret_string = random_password.mongo_password.result
}

output "MONGO_URI" {
  description = "MongoDB connection URI"
  value       = "mongodb://${aws_docdb_cluster.amaris_docdb.master_username}:${aws_secretsmanager_secret_version.mongo_secret_version.secret_string}@${aws_docdb_cluster.amaris_docdb.endpoint}:27017"
  sensitive   = true
}

output "MONGO_DB" {
  description = "MongoDB database name"
  value       = "amaris"
}

