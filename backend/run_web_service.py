"""
ToStructured AI - Backend Web Service Entry Point

Registers all controllers with their resource managers, wiring together the
4-layer architecture (abstractions -> controllers -> managers -> services).
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database.DatabaseService import DatabaseService
from utils.json_utils import AppJSONProvider

# Controllers — kept from zerve-app
from controllers.auth.AuthController import AuthController
from controllers.users.UserController import UserController
from controllers.organizations.OrganizationController import OrganizationController
from controllers.billing.BillingController import BillingController
from controllers.notifications.NotificationController import NotificationController

# Controllers — new for document processing
from controllers.documents.DocumentController import DocumentController
from controllers.models.ModelController import ModelController
from controllers.pipelines.PipelineController import PipelineController
from controllers.queries.QueryController import QueryController
from controllers.outputs.OutputController import OutputController
from controllers.pipeline_types.PipelineTypeController import PipelineTypeController
from controllers.connections.ConnectionController import ConnectionController
from controllers.sources.SourceController import SourceController

# Resource Managers — kept from zerve-app
from managers.auth.AuthResourceManager import AuthResourceManager
from managers.users.UserResourceManager import UserResourceManager
from managers.organizations.OrganizationResourceManager import OrganizationResourceManager
from managers.billing.BillingResourceManager import BillingResourceManager
from managers.notifications.NotificationResourceManager import NotificationResourceManager

# Resource Managers — new for document processing
from managers.documents.DocumentResourceManager import DocumentResourceManager
from managers.models.ModelResourceManager import ModelResourceManager
from managers.pipelines.PipelineResourceManager import PipelineResourceManager
from managers.queries.QueryResourceManager import QueryResourceManager
from managers.outputs.OutputResourceManager import OutputResourceManager
from managers.pipeline_types.PipelineTypeResourceManager import PipelineTypeResourceManager
from managers.connections.ConnectionResourceManager import ConnectionResourceManager
from managers.sources.SourceResourceManager import SourceResourceManager

# Services
from services.email.EmailService import EmailService
from services.user.UserService import UserService
from services.ai.AIService import AIService
from services.ai.LangChainServiceManager import LangChainServiceManager
from services.ai.EmbeddingsService import EmbeddingsService
from services.processing.DocumentProcessorService import DocumentProcessorService
from services.vector_db.VectorDBService import VectorDBService
from services.pipeline_types.PipelineTypeService import PipelineTypeService
from services.stripe.StripeService import StripeService
from services.notification.NotificationService import NotificationService
from services.export.ExportService import ExportService

# Utils
from utils.register_components import register_controller


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.json_provider_class = AppJSONProvider
    app.json = AppJSONProvider(app)

    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    # App configuration
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")) * 1024 * 1024
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

    # Initialize database via DatabaseService
    db_service = DatabaseService()
    try:
        db_service.initialize()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("The app will start but database operations may fail.")

    # ----- Initialize Services -----

    # Email Service
    email_service = EmailService()
    try:
        email_service.initialize()
        print("Email service initialized.")
    except Exception as e:
        print(f"Warning: Email service initialization failed: {e}")

    # User Service (Cognito admin operations)
    user_service = UserService()
    user_service.initialize()
    print("User service initialized.")

    # Storage Service
    uploads_bucket = os.getenv("UPLOADS_BUCKET")
    if uploads_bucket:
        from services.storage.S3StorageService import S3StorageService
        storage_service = S3StorageService(config={
            "bucket_name": uploads_bucket,
            "region": os.getenv("AWS_REGION_NAME", "us-east-1"),
        })
        storage_service.initialize()
        print(f"Storage: S3 bucket '{uploads_bucket}'")
    else:
        from services.storage.LocalStorageService import LocalStorageService
        storage_service = LocalStorageService(
            base_dir=os.getenv("UPLOAD_DIR", "uploads")
        )
        print("Storage: Local filesystem")

    # AI Service (basic AI helper)
    ai_service = AIService()
    ai_service.set_db(db_service)
    ai_service.initialize()
    print("AI service initialized.")

    # LangChain Service Manager (LLM orchestration)
    langchain_service = LangChainServiceManager()
    print("LangChain service manager initialized.")

    # Embeddings Service
    embeddings_service = EmbeddingsService()
    print("Embeddings service initialized.")

    # Document Processor Service
    processor_service = DocumentProcessorService()
    print("Document processor service initialized.")

    # Vector DB Service (Pinecone)
    vector_db_service = VectorDBService()
    print("Vector DB service initialized.")

    # Pipeline Type Service
    pipeline_type_service = PipelineTypeService()
    print("Pipeline type service initialized.")

    # Stripe Service
    stripe_service = StripeService()
    stripe_service.set_db(db_service)
    stripe_service.initialize()
    print("Stripe service initialized.")

    # Notification Service
    notification_service = NotificationService()
    notification_service.set_db(db_service)
    notification_service.initialize()
    notification_service.set_email_service(email_service)
    print("Notification service initialized.")

    # Export Service
    export_service = ExportService()
    export_service.initialize()
    print("Export service initialized.")

    # ----- Service Managers Dictionary -----
    service_managers = {
        "db": db_service,
        "email": email_service,
        "storage": storage_service,
        "user": user_service,
        "ai": ai_service,
        "langchain": langchain_service,
        "embeddings": embeddings_service,
        "processor": processor_service,
        "vector_db": vector_db_service,
        "pipeline_types": pipeline_type_service,
        "stripe": stripe_service,
        "notification": notification_service,
        "export": export_service,
    }

    # ----- Register Controllers with Resource Managers -----

    # Auth (Cognito)
    auth_manager = AuthResourceManager(service_managers=service_managers)
    register_controller(app, AuthController, auth_manager)

    # Users
    user_manager = UserResourceManager(service_managers=service_managers)
    register_controller(app, UserController, user_manager)

    # Organizations
    org_manager = OrganizationResourceManager(service_managers=service_managers)
    register_controller(app, OrganizationController, org_manager)

    # Billing (Stripe)
    billing_manager = BillingResourceManager(service_managers=service_managers)
    register_controller(app, BillingController, billing_manager)

    # Notifications
    notification_manager = NotificationResourceManager(service_managers=service_managers)
    register_controller(app, NotificationController, notification_manager)

    # Documents
    document_manager = DocumentResourceManager(service_managers=service_managers)
    register_controller(app, DocumentController, document_manager)

    # Models (AI model configuration)
    model_manager = ModelResourceManager(service_managers=service_managers)
    register_controller(app, ModelController, model_manager)

    # Pipelines
    pipeline_manager = PipelineResourceManager(service_managers=service_managers)
    register_controller(app, PipelineController, pipeline_manager)

    # Queries (RAG Q&A)
    query_manager = QueryResourceManager(service_managers=service_managers)
    register_controller(app, QueryController, query_manager)

    # Outputs
    output_manager = OutputResourceManager(service_managers=service_managers)
    register_controller(app, OutputController, output_manager)

    # Pipeline Types
    pipeline_type_manager = PipelineTypeResourceManager(service_managers=service_managers)
    register_controller(app, PipelineTypeController, pipeline_type_manager)

    # Database Connections
    connection_manager = ConnectionResourceManager(service_managers=service_managers)
    register_controller(app, ConnectionController, connection_manager)

    # Sources
    source_manager = SourceResourceManager(service_managers=service_managers)
    register_controller(app, SourceController, source_manager)

    # ----- Health Check -----
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "tostructured-ai-backend",
            "version": "1.0.0",
        }), 200

    # ----- Error Handlers -----
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({"success": False, "error": "File too large"}), 413

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"Starting ToStructured AI Backend on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
