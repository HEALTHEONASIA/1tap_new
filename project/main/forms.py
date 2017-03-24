import re
from flask_wtf import Form
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms import FileField
from wtforms import BooleanField, PasswordField, ValidationError
from wtforms.validators import Required, Email, Length, URL


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


def validate_numeric(form, field):
    if field.data:
        match = re.match(r"^[0-9]+$", field.data)
        if match == None:
            raise ValidationError('Only digits are allowed.')

def validate_dropdown(form, field):
    if field.data:
        if field.data == -1:
            raise ValidationError('Please select an Option From The DropDown.')


class TerminalForm(BaseForm):
    status = StringField('Status', validators=[Required()])
    serial_number = StringField('Serial number', validators=[Required()])
    model = StringField('Model', validators=[Required()])
    location = StringField('Location', validators=[Required()])
    version = StringField('Version', validators=[Required()])
    last_update = StringField('Last update')
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Save')


class ClaimForm(BaseForm):
    status = StringField('Status')
    amount = StringField('Amount', validators=[Required()])
    claim_number = StringField('Claims Number')
    claim_type = StringField('Claims Type')
    date = StringField('Date')
    time = StringField('Time')
    admitted = BooleanField('Admitted')
    discharged = BooleanField('Discharged')
    member_id = SelectField('Member', validators=[validate_dropdown], coerce=int)
    terminal_id = SelectField('Terminal', validators=[validate_dropdown], coerce=int)
    submit = SubmitField('Save')


class MemberForm(BaseForm):
    photo = FileField('Photo')
    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required()])
    action = StringField('Action')
    address = StringField('Address')
    address_additional = StringField('Address 2')
    telephone = StringField('Telephone', validators=[Required()])
    dob = StringField('Date of birth')
    sex = SelectField('Gender', validators=[Required()],
                      choices=[('Male', 'Male'),
                               ('Female', 'Female')])
    marital_status = SelectField('Marital status', validators=[Required()],
                                 choices=[('Married', 'Married'),
                                          ('Single', 'Single')])
    start_date = StringField('Start date')
    effective_date = StringField('Effective date')
    mature_date = StringField('Mature date')
    exit_date = StringField('Exit date')
    product = StringField('Product')
    plan = StringField('Plan')
    client_policy_number = StringField('Client policy number')
    client_id_number = StringField('Client ID number')
    card_number = StringField('Card number')
    plan_type = StringField('Plan type')
    remarks = StringField('Remarks')
    dependents = StringField('Dependents')
    sequence = StringField('Sequence')
    patient_type = SelectField('Patient type', validators=[Required()],
                               choices=[('In', 'In'),
                                        ('Out', 'Out')])
    submit = SubmitField('Save')

class SMSVerificationForm(BaseForm):
    verification_code = StringField('Verification Code', validators=[Required()])
    submit = SubmitField('Verify')
