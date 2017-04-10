from flask import request
from flask_servicelayer import SQLAlchemyService

from .. import db, models


class ExtFuncsMixin(object):
    def __init__(self):
        self.columns = self.__model__.columns()

    def update_from_form(self, model, form, exclude=[]):
        # fill the models data from the form
        for col in model.columns():
            if col not in exclude and hasattr(form, col):
                setattr(model, col, getattr(form, col).data)

        self.__db__.session.add(model)
        self.__db__.session.commit()

    @staticmethod
    def prepare_pagination(items):
        # pagination
        pagination = items.paginate(per_page=10)

        page = request.args.get('page')

        # if some page is chosen otherwise than the first
        if page or pagination.pages > 1:
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
            items = items.paginate(page=page, per_page=10).items

        return (pagination, items)


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