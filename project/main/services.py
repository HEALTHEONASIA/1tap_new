from flask_servicelayer import SQLAlchemyService

from .. import db, models


class ExtFuncsMixin(object):
    def __init__(self):
        self.columns = self.__model__.columns()

    @staticmethod
    def update_from_form(model, form, exclude=[]):
        # fill the models data from the form
        for col in model.columns():
            if col not in exclude and hasattr(form, col):
                setattr(model, col, getattr(form, col).data)


class MedicalDetailsService(ExtFuncsMixin, SQLAlchemyService):
    __model__ = models.MedicalDetails
    __db__ = db


class MemberService(ExtFuncsMixin, SQLAlchemyService):
    __model__ = models.Member
    __db__ = db


class ClaimService(ExtFuncsMixin, SQLAlchemyService):
    __model__ = models.Claim
    __db__ = db


class GuaranteeOfPaymentService(ExtFuncsMixin, SQLAlchemyService):
    __model__ = models.GuaranteeOfPayment
    __db__ = db


class TerminalService(ExtFuncsMixin, SQLAlchemyService):
    __model__ = models.Terminal
    __db__ = db