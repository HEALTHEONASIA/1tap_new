import re
from flask_wtf import Form
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms import FileField, RadioField, HiddenField, SelectMultipleField
from wtforms import BooleanField, PasswordField, ValidationError
from wtforms.validators import Required, Email, Length, URL
from ..models import Payer, Patient, User, Provider


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

def validate_phone(form, field):
    if field.data:
        match = re.match(r"^\+?[0-9]+$", field.data)
        if match == None:
            raise ValidationError('Invalid phone number.')

def validate_comma_sep_dec(form, field):
    field.data = field.data.replace(',' ,'').replace('-','')
    try:
        field.data = float(field.data)
    except ValueError:
        field.data = 0.0
        raise ValidationError('Fee Cannot Be Zero')
        
def validate_empty_fee(form, field):
    try:
        field.data = float(field.data)
        if field.data <= 0:
            raise ValidationError('Fee Cannot Be Zero')
    except ValueError:
        field.data = 0.0
        raise ValidationError('Fee Cannot Be Zero')

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


class GOPForm(BaseForm):
    patient_medical_no = StringField('Patient medical no.',
                                     validators=[Required()])
    payer = SelectField('Payer Select', coerce=int)
    policy_number = StringField('Policy Number', validators=[Required()])
    name = StringField('Name', validators=[Required()])
    dob = StringField('Date of birth', validators=[Required()])
    gender = RadioField('Sex', validators=[Required()],
                            choices=[('male', 'Male'),
                                     ('female', 'Female')])
    tel = StringField('Patient phone nr.', validators=[Required(),
                                                       validate_phone])

    current_national_id = HiddenField('Current Patient ID')

    patient_action_plan = TextAreaField('Plan of action',
                                        validators=[Required()])
    national_id = StringField('Patient ID', validators=[Required()])
    patient_photo = FileField('Patient photo')
    medical_details_symptoms = StringField('Symptoms')
    medical_details_temperature = StringField('Temperature')
    medical_details_heart_rate = StringField('Heart rate')
    medical_details_respiration = StringField('Respiration')
    medical_details_blood_pressure = StringField('Blood pressure')
    medical_details_physical_finding = StringField('Physical finding')
    medical_details_health_history = TextAreaField('Health history')
    medical_details_previously_admitted = StringField('Previously admitted')
    medical_details_diagnosis = StringField('Diagnosis')
    medical_details_in_patient = BooleanField('In patient indication')
    medical_details_test_results = TextAreaField('Test results')
    medical_details_current_therapy = StringField('Current therapy')
    medical_details_treatment_plan = TextAreaField('Treatment plan')

    doctor_name = SelectField('Doctor name', validators=[Required()],
                              coerce=int)
    admission_date = StringField('Admission date', validators=[Required()])
    admission_time = StringField('Admission time', validators=[Required()])

    icd_codes = SelectMultipleField('ICD codes', validators=[Required()],
                                    coerce=int)

    room_price = StringField('Room price', validators=[Required(), 
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee])
    room_type = SelectField('Room type', validators=[Required()],
                            choices=[(False, 'SELECT ROOM'),
                                     ('na', 'NA'),
                                     ('i', 'I'),
                                     ('ii', 'II'),
                                     ('iii', 'III'),
                                     ('iv', 'IV'),
                                     ('vip', 'VIP')])

    reason = RadioField('Reason', validators=[Required()],
                        choices=[('general', 'General'),
                                 ('specialist', 'Specialist'),
                                 ('emergency', 'Emergency'),
                                 ('scheduled', 'Scheduled')])

    doctor_fee = StringField('Doctor fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee])
    surgery_fee = StringField('Surgery fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee])
    medication_fee = StringField('Medication fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee])
    quotation = StringField('Quotation', validators=[Required(),
                                                     validate_comma_sep_dec,
                                                     validate_empty_fee])
    submit = SubmitField('Send GOP request')

    def validate_national_id(self, field):
        if field.data != self.current_national_id.data and \
          Patient.query.filter_by(national_id=field.data).first():
            raise ValidationError('Patient ID already exists.')

    def validate_patient_photo(self, field):
        if field.data:
            filename = secure_filename(field.data.filename)
            allowed = ['jpg', 'jpeg', 'png', 'gif']
            if not ('.' in filename and filename.rsplit('.', 1)[1] in allowed):
              raise ValidationError("Only image files are allowed.")


class MemberForm(BaseForm):
    photo = FileField('Photo')
    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required()])
    action = StringField('Action')
    address = StringField('Address')
    address_additional = StringField('Address 2')
    telephone = StringField('Telephone', validators=[Required()])
    dob = StringField('Date of birth')
    gender = SelectField('Gender', validators=[Required()],
                      choices=[('male', 'Male'),
                               ('female', 'Female')])
    marital_status = SelectField('Marital status', validators=[Required()],
                                 choices=[('married', 'Married'),
                                          ('single', 'Single')])
    start_date = StringField('Start date')
    effective_date = StringField('Effective date')
    mature_date = StringField('Mature date')
    exit_date = StringField('Exit date')
    product = StringField('Product')
    plan = StringField('Plan')
    policy_number = StringField('Policy number')
    national_id = StringField('Client ID number')
    card_number = StringField('Card number')
    plan_type = StringField('Plan type')
    remarks = StringField('Remarks')
    dependents = StringField('Dependents')
    sequence = StringField('Sequence')
    patient_type = SelectField('Patient type', validators=[Required()],
                               choices=[('in', 'In'),
                                        ('out', 'Out')])
    submit = SubmitField('Save')

class SMSVerificationForm(BaseForm):
    verification_code = StringField('Verification Code', validators=[Required()])
    submit = SubmitField('Verify')
