import re
from flask import flash
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import RadioField, HiddenField
from wtforms.validators import Required, Email, Length, EqualTo
from wtforms import ValidationError
from ..models import User


class BaseForm(Form):
    class Meta:
        def bind_field(self, form, unbound_field, options):
            filters = unbound_field.kwargs.get('filters', [])
            filters.append(strip_filter)
            return unbound_field.bind(form=form, filters=filters, **options)


def strip_filter(value):
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value


def validate_email_address(form, field):
    if field.data:
        match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"\
          ,field.data)
        if match == None:
            flash('The email address you entered is wrong.')
            raise ValidationError('Invalid Email address.')


class LoginForm(BaseForm):
    email = StringField('Your e-mail', validators=[Required(), Length(1, 64),
                                             validate_email_address])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Remember me')
    #user_type = HiddenField('User type')
    submit = SubmitField('Sign In')


class ForgotPasswordForm(BaseForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError('The email is not found.')

