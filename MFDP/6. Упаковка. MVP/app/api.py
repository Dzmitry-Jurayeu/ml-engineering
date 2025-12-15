from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.home import home_route
from routes.user import user_route
from routes.event import event_route
from routes.model import model_route
from routes.tank import tank_route
from database.database import init_db
from database.config import get_settings
import uvicorn
from loguru import logger

settings = get_settings()


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(home_route, tags=['Home'])
    app.include_router(user_route, prefix='/api/users', tags=['Users'])
    app.include_router(event_route, prefix='/api/events', tags=['Events'])
    app.include_router(model_route, prefix='/api/models', tags=['Models'])
    app.include_router(tank_route, prefix='/api/tanks', tags=['Tanks'])

    return app


app = create_application()


@app.on_event("startup")
def on_startup():
    try:
        logger.info("Initializing database...")
        general_df, premium_df = init_db(drop_all=True)
        app.state.general_df = general_df
        app.state.premium_df = premium_df
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutting down...")


if __name__ == '__main__':
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info"
    )
