// Runtime configuration for the frontend
// When deployed to AWS S3, set window.__API_BASE__ to the Lambda Function URL or API Gateway endpoint.
// Leave as empty string "" for local development to use localhost:8000.
window.__API_BASE__ = window.__API_BASE__ || "";
