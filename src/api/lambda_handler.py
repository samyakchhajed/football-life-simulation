"""
AWS Lambda Entrypoint for The Football Life Engine API.
Uses Mangum ASGI adapter to handle requests from AWS Lambda Function URL and API Gateway.
"""
from mangum import Mangum
from src.api.main import app

# Create serverless handler
handler = Mangum(app, lifespan="off")
