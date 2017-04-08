from flask_servicelayer import SQLAlchemyService

from .. import db, models


class MedicalDetailsService(SQLAlchemyService):
    __model__ = models.MedicalDetails
    __db__ = db

    columns = __model__.columns()