import os, random

from calendar import month_abbr
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from flask import flash, render_template, redirect, request, url_for
from flask import jsonify, send_from_directory, session
from flask_login import current_user, login_user
from werkzeug.utils import secure_filename
from flask_mail import Message

from .forms import ClaimForm, MemberForm, TerminalForm, GOPForm
from .forms import SMSVerificationForm
from .twillo_2_factor_authentication import send_confirmation_code
from ..api.helpers import convert_dict_claim_model, convert_dict_member_model
from ..api.helpers import prepare_claim_dict, prepare_member_dict
from . import main
from .. import config, db, models, mail
from ..models import monthdelta, login_required

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config['production'].ALLOWED_EXTENSIONS

def to_float_or_zero(value):
    try:
        if value is not None:
            value = float(value)
        else:
            value = 0.00
    except ValueError:
        value = 0.0
    return value

def photo_file_name_santizer(photo):
    filename = secure_filename(photo.data.filename)

    if filename and allowed_file(filename):
        filename = str(random.randint(100000, 999999)) + filename
        photo.data.save(
            os.path.join(config['production'].UPLOAD_FOLDER, filename))

    if not filename:
        filename = ''

    if filename:
        photo_filename = '/static/uploads/' + filename
    else:
        photo_filename = '/static/img/person-solid.png'

    return photo_filename

def datetime_set_to_current_date_on_failure(data):
    try:
        date_data = datetime.strptime(data, '%m/%d/%Y %I:%M %p')
    except Exception as e:
        date_data = datetime.now()

    return date_data

def date_set_to_current_date_on_failure(data):
    try:
        date_data = datetime.strptime(data, '%m/%d/%Y')
    except Exception as e:
        date_data = datetime.now()

    return date_data

def safe_div(dividend, divisor):
    try:
        result = dividend / divisor
    except ZeroDivisionError:
        result = 0.00
    return result

def percent_of(part, total):
    return safe_div(float(part), float(total)) * 100

def in_patients_for(claims):
    """Returns the in-patients for the given claims."""
    result = []

    for claim in claims:
        if claim.member.patient_type == 'In':
            result.append(claim.member.id)

    result = list(set(result))

    return result

def out_patients_for(claims):
    """Returns the out-patients for the given claims."""
    result = []

    for claim in claims:
        if claim.member.patient_type == 'Out':
            result.append(claim.member)

    result = list(set(result))

    return result


@main.route('/')
@login_required()
def index():
    if current_user.get_type() == 'provider':
        providers = []
        members = current_user.provider.members.all()
        claims_query = current_user.provider.claims.filter(models.Claim.id != False)
        claims = claims_query.all()

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment]
        providers = models.Provider.query.join(models.Claim, models.Provider.claims)\
            .filter(models.Claim.id.in_(claim_ids)).all()
        members = models.Member.query.join(models.Claim, models.Member.claims)\
            .filter(models.Claim.id.in_(claim_ids)).all()
        claims_query = models.Claim.query.filter(models.Claim.id.in_(claim_ids))
        claims = claims_query.all()

    if current_user.get_role() == 'admin':
        providers = models.Provider.query.all()
        members = models.Member.query.all()
        # filtering to get the query object, rather than objects list
        # it needs to make apply a pagination on that query object
        claims_query = models.Claim.query.filter(models.Claim.id != False)
        claims = claims_query.all()

    total_claims = len(claims)

    page = request.args.get('page')

    # get the claims in the given month ranges
    historical = {
        '0': models.Claim.for_months(0),
        '1': models.Claim.for_months(1),
        '3': models.Claim.for_months(3),
        '5': models.Claim.for_months(5),
        '6': models.Claim.for_months(6),
        '24': models.Claim.for_months(24)
    }

    in_patients = {
        'total': len(in_patients_for(claims)),
        '1_month': len(in_patients_for(historical['1'][0])),
        '3_months': len(in_patients_for(historical['3'][0])),
        '6_months': len(in_patients_for(historical['6'][0])),
        '24_months': len(in_patients_for(historical['24'][0]))
    }

    out_patients = {
        'total': len(out_patients_for(claims)),
        '1_month': len(out_patients_for(historical['1'][0])),
        '3_months': len(out_patients_for(historical['3'][0])),
        '6_months': len(out_patients_for(historical['6'][0])),
        '24_months': len(out_patients_for(historical['24'][0]))
    }

    amount_summary = {
        'total': models.Claim.amount_sum(0)[0],
        '0': models.Claim.amount_sum(0),
        '1': models.Claim.amount_sum(1),
        '2': models.Claim.amount_sum(2),
        '3': models.Claim.amount_sum(3),
        '4': models.Claim.amount_sum(4),
        '5': models.Claim.amount_sum(5),
        '6': models.Claim.amount_sum(6),
        '24': models.Claim.amount_sum(24),
    }

    by_cost = {}
    by_icd = {}

    # calculate values for the Historical Claims section table
    for key, value in historical.items():
        for claim in value[0]:
            # calculate values for the Medical Summary By Cost table
            if not claim.amount in by_cost:
                by_cost[claim.amount] = {}

            if not key in by_cost[claim.amount]:
                by_cost[claim.amount][key] = 1
            else:
                by_cost[claim.amount][key] += 1

            # calculate values for the Medical Summary By ICD Code table
            if not claim.icd_code in by_icd:
                by_icd[claim.icd_code] = {}

            if not key in by_icd[claim.icd_code]:
                by_icd[claim.icd_code][key] = 1
            else:
                by_icd[claim.icd_code][key] += 1

    in_patients_perc = percent_of(in_patients['total'],
                            out_patients['total'] + in_patients['total'])

    out_patients_perc = percent_of(out_patients['total'],
                            out_patients['total'] + in_patients['total'])

    open_claims = claims_query.filter_by(status="Open").all()
    open_claims_perc = percent_of(len(open_claims), len(claims))

    closed_claims =  claims_query.filter_by(status="Closed").all()
    closed_claims_perc = percent_of(len(closed_claims), len(claims))

    amount_chart_data = {
        'labels': [],
        'values': []
    }
    # fill in the chart data for the 5 months
    for months in reversed(range(6)):
        month_name = month_abbr[monthdelta(datetime.now(), months * -1).month]
        amount_chart_data['labels'].append(month_name)
        amount_chart_data['values'].append(amount_summary[str(months)][2])

    in_patients_data = [
        len(in_patients_for(historical['5'][0])),
        len(in_patients_for(historical['3'][0])),
        len(in_patients_for(historical['0'][0]))
    ]
    out_patients_data = [
        len(out_patients_for(historical['5'][0])),
        len(out_patients_for(historical['3'][0])),
        len(out_patients_for(historical['0'][0]))
    ]

    # claims pagination
    pagination = claims_query.paginate(per_page=10)

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        claims = claims_query.paginate(page=page, per_page=10).items

    context = {
        'providers': providers,
        'members': members,
        'claims': claims,
        'pagination': pagination,
        'historical': historical,
        'out_patients': out_patients,
        'in_patients': in_patients,
        'amount_summary': amount_summary,
        'total_claims': total_claims,
        'by_cost': by_cost,
        'by_icd': by_icd,
        'in_patients_perc': in_patients_perc,
        'out_patients_perc': out_patients_perc,
        'open_claims':open_claims,
        'open_claims_perc':open_claims_perc,
        'closed_claims':closed_claims,
        'closed_claims_perc':closed_claims_perc,
        'in_patients_data': in_patients_data,
        'out_patients_data': out_patients_data,
        'today': datetime.now(),
        'amount_chart_data': amount_chart_data
    }

    return render_template('index.html', **context)


@main.route('/static/uploads/<filename>')
@login_required()
def block_unauthenticated_url(filename):
    return send_from_directory(os.path.join('static','uploads'),filename)


@main.route('/terminals')
@login_required()
def terminals():
    if current_user.get_type() != 'provider' and \
      current_user.get_role() != 'admin':
        return redirect(url_for('main.index'))

    # retreive the all current user's terminals
    if current_user.get_type() == 'provider':
        terminals = current_user.provider.terminals

    if current_user.get_role() == 'admin':
        terminals = models.Terminal.query.filter(models.Terminal.id != False)

    # pagination
    pagination = terminals.paginate(per_page=10)

    page = request.args.get('page')

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        terminals = terminals.paginate(page=page, per_page=10).items

    # render the "terminals.html" template with the given terminals
    return render_template('terminals.html', terminals=terminals,
                                             pagination=pagination)


@main.route('/terminal/<int:terminal_id>')
@login_required()
def terminal(terminal_id):
    if current_user.get_type() != 'provider' and \
      current_user.get_role() != 'admin':
        return redirect(url_for('main.index'))

    if current_user.get_type() == 'provider':
        terminal = current_user.provider.terminals.filter_by(
            id=terminal_id).first()

    if current_user.get_role() == 'admin':
        terminal = models.Terminal.query.get(terminal_id)

    claims = terminal.claims

    # pagination
    pagination = claims.paginate(per_page=10)

    page = request.args.get('page')

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        claims = claims.paginate(page=page, per_page=10).items

    # render the "terminal.html" template with the given terminal
    return render_template('terminal.html', terminal=terminal, claims=claims,
                                            pagination=pagination)


@main.route('/terminal/add', methods=['GET', 'POST'])
@login_required()
def terminal_add():
    if current_user.get_type() != 'provider':
        return redirect(url_for('main.index'))

    form = TerminalForm()

    # if the form was sent
    if form.validate_on_submit():
        terminal = models.Terminal(
            status=form.status.data,
            serial_number=form.serial_number.data,
            model=form.model.data,
            provider_id=current_user.provider.id,
            location=form.location.data,
            version=form.version.data,
            last_update=datetime.now(),
            remarks=form.remarks.data)

        # commit the database changes
        db.session.add(terminal)
        db.session.commit()
        flash('The terminal has been added')
        return redirect(url_for('main.terminals'))

    return render_template('terminal-form.html', form=form)


@main.route('/terminal/<int:terminal_id>/edit', methods=['GET', 'POST'])
@login_required()
def terminal_edit(terminal_id):
    if current_user.get_type() != 'provider' and \
      current_user.get_role() != 'admin':
        return redirect(url_for('main.index'))

    # retreive the current user's terminal by its ID
    if current_user.get_type() == 'provider':
        terminal = current_user.terminals.filter_by(id=terminal_id).first()

    if current_user.get_role() == 'admin':
        terminal = models.Terminal.query.get(terminal_id)

    form = TerminalForm()

    # if the form was sent
    if form.validate_on_submit():

        # update the database with the data from the form fields
        terminal.status = form.status.data
        terminal.serial_number = form.serial_number.data
        terminal.model = form.model.data
        terminal.location = form.location.data
        terminal.version = form.version.data
        terminal.remarks = form.remarks.data 

        # commit the database changes
        db.session.add(terminal)
        db.session.commit()
        flash('Data has been updated.')

     # if the form was just opened
    if request.method != 'POST':

        # fill in the form fields with the data from the database
        form.status.data = terminal.status
        form.serial_number.data = terminal.serial_number
        form.model.data = terminal.model
        form.location.data = terminal.location
        form.version.data = terminal.version
        form.remarks.data = terminal.remarks

    # render the "terminal-form.html" template with the given terminal
    return render_template('terminal-form.html', form=form, terminal=terminal)


@main.route('/claims')
@login_required()
def claims():
    if current_user.get_type() == 'provider':
        claims = current_user.provider.claims.filter(models.Claim.id != False)

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment]
        claims = models.Claim.query.filter(models.Claim.id.in_(claim_ids))

    if current_user.get_role() == 'admin':
        claims = models.Claim.query.filter(models.Claim.id != False)

    # pagination
    pagination = claims.paginate(per_page=10)

    page = request.args.get('page')

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        claims = claims.paginate(page=page, per_page=10).items

    # render the "claims.html" template with the given transactions
    return render_template('claims.html', claims=claims,
                                          pagination=pagination)


@main.route('/claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required()
def claim(claim_id):
    if current_user.get_type() == 'provider':
        claim = current_user.provider.claims.filter_by(id=claim_id).first()

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment]
        claim = models.Claim.query.filter(models.Claim.id==claim_id and \
                models.Claim.id.in_(claim_ids)).first()

    # retreive the current user's claim by its ID
    # claim = current_user.claims.filter_by(id=claim_id).first()
    if current_user.get_role() == 'admin':
        claim = models.Claim.query.get(claim_id)

    form = GOPForm()

    if current_user.get_type() == 'provider':
        form.payer.choices = [('0', 'None')]
        form.payer.choices += [(p.id, p.company) for p in \
                               current_user.provider.payers]

        form.icd_codes.choices = [(i.id, i.code) for i in \
            models.ICDCode.query.filter(models.ICDCode.code != 'None' and \
            models.ICDCode.code != '')]
        
        form.doctor_name.choices = [('0', 'None')]
        form.doctor_name.choices += [(d.id, d.name + ' (%s)' % d.doctor_type) \
                                    for d in current_user.provider.doctors]

        form.name.data = claim.member.name
        form.dob.data = claim.member.dob.strftime('%d/%m/%Y')
        form.policy_number.data = claim.member.policy_number
        form.admission_date.data = claim.datetime.strftime('%d/%m/%Y')
        form.admission_time.data = claim.datetime.strftime('%I:%M %p')
        form.quotation.data = claim.amount
        form.gender.data = claim.member.gender
        form.national_id.data = claim.member.client_id_number
        form.tel.data = claim.member.telephone

    if form.validate_on_submit():
        dob = datetime.strptime(form.dob.data, '%d/%m/%Y')
        admission_date = datetime.strptime(form.admission_date.data + ' ' + \
            form.admission_time.data, '%d/%m/%Y %I:%M %p')
        admission_time = admission_date

        if form.medical_details_previously_admitted.data:
            previously_admitted = datetime.strptime(
                form.medical_details_previously_admitted.data, '%d/%m/%Y')
        else:
            previously_admitted = None

        filename = secure_filename(form.patient_photo.data.filename)

        if filename and allowed_file(filename):
            filename = str(random.randint(100000, 999999)) + filename
            form.patient_photo.data.save(
                os.path.join(config['development'].UPLOAD_FOLDER, filename))

        if not filename:
            filename = ''

        patient = models.Patient.query.filter_by(
            national_id=form.national_id.data).first()

        if not patient:
            if filename:
                photo_filename = '/static/uploads/' + filename
            else:
                photo_filename = '/static/img/person-solid.png'

            medical_details = models.MedicalDetails(
                symptoms=form.medical_details_symptoms.data,
                temperature=form.medical_details_temperature.data,
                heart_rate=form.medical_details_heart_rate.data,
                respiration=form.medical_details_respiration.data,
                blood_pressure=form.medical_details_blood_pressure.data,
                physical_finding=form.medical_details_physical_finding.data,
                health_history=form.medical_details_health_history.data,
                previously_admitted=previously_admitted,
                diagnosis=form.medical_details_diagnosis.data,
                in_patient=form.medical_details_in_patient.data,
                test_results=form.medical_details_test_results.data,
                current_therapy=form.medical_details_current_therapy.data,
                treatment_plan=form.medical_details_treatment_plan.data
            )

            patient = models.Patient(
                name=form.name.data,
                dob=dob,
                gender=form.gender.data,
                national_id=form.national_id.data,
                tel=form.tel.data,
                photo=photo_filename,
                policy_number=form.policy_number.data)

        # try to convert the values to float or, if error, convert to zero
        room_price = to_float_or_zero(form.room_price.data)
        doctor_fee = to_float_or_zero(form.doctor_fee.data)
        surgery_fee = to_float_or_zero(form.surgery_fee.data)
        medication_fee = to_float_or_zero(form.medication_fee.data)
        quotation = to_float_or_zero(form.quotation.data)

        payer = models.Payer.query.get(form.payer.data)
        gop = models.GuaranteeOfPayment(
                provider=current_user.provider,
                claim=claim,
                payer=payer,
                patient=patient,
                patient_action_plan=form.patient_action_plan.data,
                doctor_name=models.Doctor.query.get(int(form.doctor_name.data)).name,
                admission_date=admission_date,
                admission_time=admission_time,
                reason=form.reason.data,
                room_price=room_price,
                status='pending',
                room_type=form.room_type.data,
                patient_medical_no=form.patient_medical_no.data,
                doctor_fee=doctor_fee,
                surgery_fee=surgery_fee,
                medication_fee=medication_fee,
                timestamp=datetime.now(),
                quotation=quotation,
                medical_details=medical_details
                )

        for icd_code_id in form.icd_codes.data:
            icd_code = models.ICDCode.query.get(int(icd_code_id))
            gop.icd_codes.append(icd_code)
        
        db.session.add(gop)
        db.session.commit()
        
        # initializing user and random password 
        user = None
        rand_pass = None
        
        # if the payer is registered as a user in our system
        if gop.payer.user:
            if gop.payer.pic_email:
                recipient_email = gop.payer.pic_email
            elif gop.payer.pic_alt_email:
                recipient_email = gop.payer.pic_alt_email
            else:
                recipient_email = gop.payer.user.email
            # getting payer id for sending notification    
            notification_payer_id = gop.payer.user.id
            
        # if no, we register him, set the random password and send
        # the access credentials to him
        else:
            recipient_email = gop.payer.pic_email
            rand_pass = pass_generator(size=8)
            user = models.User(email=gop.payer.pic_email,
                    password=rand_pass,
                    user_type='payer',
                    payer=gop.payer)
            db.session.add(user)
            # getting payer id for sending notification 
            notification_payer_id = user.id

        msg = Message("Request for GOP - %s" % gop.provider.company,
                      sender=("MediPay",
                              "request@app.medipayasia.com"),
                      recipients=[recipient_email])

        msg.html = render_template("request-email.html", gop=gop,
                                   root=request.url_root, user=user,
                                   rand_pass = rand_pass, gop_id=gop.id)

        
        # send the email
        try:
            mail.send(msg)
        except Exception as e:
            pass
        
        # Creating notification message
        notification_message = "Request for Intial GOP - %s" % gop.provider.company
        notification_message = notification_message + "<BR>"
        notification_message = notification_message + "<a href=/request/%s>Go To GOP</a>" %(str(gop.id))
        
        notification = models.Notification(message=notification_message,user_id=notification_payer_id)
        db.session.add(notification)
        db.session.commit()
        
        flash('Your GOP request has been sent.')

    if form:
        return render_template('claim.html', claim=claim, form=form)
    else:
        return render_template('claim.html', claim=claim)


@main.route('/claim/add', methods=['GET', 'POST'])
@login_required()
def claim_add():
    if current_user.get_type() != 'provider':
        return redirect(url_for('main.index'))

    terminals = current_user.provider.terminals
    members = current_user.provider.members

    terminal_list = [(terminal.id,terminal.serial_number) \
                        for terminal in terminals]
    terminal_list.insert(0, (-1, 'Please select a terminal'))

    member_list = [(member.id,member.name) for member in members]
    member_list.insert(0, (-1, 'Please select a member'))

    form = ClaimForm()
    form.terminal_id.choices = terminal_list
    form.member_id.choices = member_list

    # if the form was sent
    if form.validate_on_submit():
        claim_date_time = datetime_set_to_current_date_on_failure(
                                    form.date.data + ' ' + form.time.data)

        claim = models.Claim(
            status=form.status.data,
            amount=form.amount.data,
            claim_number=form.claim_number.data,
            claim_type=form.claim_type.data,
            datetime=claim_date_time,
            provider_id=current_user.provider.id,
            member_id=form.member_id.data,
            terminal_id=form.terminal_id.data)
        
        member = models.Member.query.get(form.member_id.data)

        # 2 Factor Authentication Code
        if member is not None:
            pass
            # if member.telephone:
            #     verification_code = send_confirmation_code(member.telephone)
            #     session['redirect_from'] = 'claim'
            #     session['claim'] = prepare_claim_dict(claim)
            #     return redirect(url_for('main.sms_verify', verification_phone_number=member.telephone))
            # else:
            #     flash('No Member Telephone Data Present. Data Not Saved.')
        else:
            flash('No member data present. Data not saved.')

        # commit the database changes
        db.session.add(claim)
        db.session.commit()

        flash('The claim has been added.')
        return redirect(url_for('main.claims'))

    return render_template('claim-form.html', form=form)


def commit_claims():
    # commit the database changes
    claim = convert_dict_claim_model(session['claim'])
    db.session.add(claim)
    db.session.commit()

    # removing passed on values
    for key in session.keys():
        if key in ['redirect_from','claim', 'verification_code']:
            session.pop(key, None)

    flash('The Claim Has Been Added.')

@main.route('/claim/<int:claim_id>/edit', methods=['GET', 'POST'])
@login_required()
def claim_edit(claim_id):
    if current_user.get_type() != 'provider' and \
      current_user.get_role() != 'admin':
        return redirect(url_for('main.index'))

    if current_user.get_type() == 'provider':
        claim = current_user.provider.claims.filter_by(id=claim_id).first()
        terminals = current_user.provider.terminals

    if current_user.get_role() == 'admin':
        claim = models.Claim.query.get(claim_id)
        terminals = models.Terminal.query.all()

    members = models.Member.query.all()

    terminal_list = [(terminal.id,terminal.serial_number) \
                        for terminal in terminals]
    terminal_list.insert(0, (-1, 'Please select a terminal'))

    member_list = [(member.id,member.name) for member in members]
    member_list.insert(0, (-1, 'Please select a member'))

    form = ClaimForm()
    form.terminal_id.choices = terminal_list
    form.member_id.choices = member_list

    # if the form was sent
    if form.validate_on_submit():

        # update the database with the data from the form fields
        claim_date_time = datetime_set_to_current_date_on_failure(
                                form.date.data + ' ' + form.time.data)

        claim.status = form.status.data
        claim.amount = form.amount.data
        claim.claim_number = form.claim_number.data
        claim.claim_type = form.claim_type.data
        claim.datetime = claim_date_time
        claim.member_id = form.member_id.data
        claim.terminal_id = form.terminal_id.data

        # commit the database changes
        db.session.add(claim)
        db.session.commit()

        flash('Data has been updated.')

     # if the form was just opened
    if request.method != 'POST':

        # fill in the form fields with the data from the database
        form.status.data = claim.status
        form.amount.data = claim.amount
        form.claim_number.data = claim.claim_number
        form.claim_type.data = claim.claim_type
        form.date.data = claim.datetime.strftime('%m/%d/%Y')
        form.time.data = claim.datetime.strftime('%I:%M %p')
        form.member_id.data  = claim.member_id
        form.terminal_id.data = claim.terminal_id

    # render the "transaction-form.html" template with the given terminal
    return render_template('claim-form.html', form=form, claim=claim)


@main.route('/claim/<int:claim_id>/gop_redirect', methods=['GET', 'POST'])
@login_required()
def claim_gop_redirect(claim_id):
    if current_user.get_type() != 'provider':
        return redirect(url_for('main.index'))

    claim = current_user.provider.claims.filter_by(id=claim_id).first()

    return redirect("https://medipayasia.com/request/%d" % \
                    claim.guarantee_of_payment.id)


@main.route('/members')
@login_required()
def members():
    if current_user.get_type() == 'provider':
        members = current_user.provider.members

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment]
        members = models.Member.query.join(models.Claim, models.Member.claims)\
            .filter(models.Claim.id.in_(claim_ids))

    if current_user.get_role() == 'admin':
        members = models.Member.query.filter(models.Member.id != False)

    # pagination
    pagination = members.paginate(per_page=10)

    page = request.args.get('page')

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        members = members.paginate(page=page, per_page=10).items

    # render the "members.html" template with the given members
    return render_template('members.html', members=members,
                                           pagination=pagination)


@main.route('/member/<int:member_id>')
@login_required()
def member(member_id):
    if current_user.get_type() == 'provider':
        claim_ids = [claim.id for claim in current_user.provider.claims]
        member = current_user.provider.members.filter_by(id=member_id).first()
        claims = member.claims.filter(models.Claim.id.in_(claim_ids))

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment]
        member = models.Member.query.join(models.Claim, models.Member.claims)\
            .filter(models.Claim.id.in_(claim_ids)).filter(models.Member.id==member_id).first()
        claims = member.claims.filter(models.Claim.id.in_(claim_ids))

    if current_user.get_role() == 'admin':
        member = models.Member.query.get(member_id)
        claims = member.claims

    # pagination
    pagination = claims.paginate(per_page=10)

    page = request.args.get('page')

    # if some page is chosen otherwise than the first
    if page or pagination.pages > 1:
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        claims = claims.paginate(page=page, per_page=10).items

    # render the "member.html" template with the given member
    return render_template('member.html', member=member, claims=claims,
                                          pagination=pagination)


@main.route('/member/add', methods=['GET', 'POST'])
@login_required()
def member_add():
    if current_user.get_type() != 'provider':
        return redirect(url_for('main.index'))

    form = MemberForm()

    # if the form was sent
    if form.validate_on_submit():

        photo_filename = photo_file_name_santizer(form.photo)

        dob = date_set_to_current_date_on_failure(form.dob.data)
        start_date = date_set_to_current_date_on_failure(form.start_date.data)
        effective_date = date_set_to_current_date_on_failure(
                            form.effective_date.data)
        mature_date = date_set_to_current_date_on_failure(
                        form.mature_date.data)
        exit_date = date_set_to_current_date_on_failure(form.exit_date.data)

        member = models.Member(
            photo=photo_filename,
            name=form.name.data,
            email=form.email.data,
            action=form.action.data,
            address=form.address.data,
            address_additional=form.address_additional.data,
            telephone=form.telephone.data,
            dob=dob,
            gender=form.gender.data,
            marital_status=form.marital_status.data,
            start_date=start_date,
            effective_date=effective_date,
            mature_date=mature_date,
            exit_date=exit_date,
            product=form.product.data,
            plan=form.plan.data,
            policy_number=form.policy_number.data,
            client_id_number=form.client_id_number.data,
            card_number=form.card_number.data,
            plan_type=form.plan_type.data,
            remarks=form.remarks.data,
            dependents=form.dependents.data,
            sequence=form.sequence.data,
            patient_type=form.patient_type.data)

        member.providers.append(current_user.provider)

        # 2 Factor Authentication Code
        # if form.telephone.data:
        #     # verification_code = send_confirmation_code(form.telephone.data)
        #     session['redirect_from'] = 'member'
        #     session['member'] = prepare_member_dict(member)
        #     return redirect(url_for('main.sms_verify', verification_phone_number=form.telephone.data))
        # else:
        #     flash('No Telephone Data Present. Data Not Saved.')

        # commit the database changes
        db.session.add(member)
        db.session.commit()

        return redirect(url_for('main.members'))

    return render_template('member-form.html', form=form)

def commit_members():
    # commit the database changes
    member = convert_dict_member_model(session['member'])
    db.session.add(member)
    db.session.commit()

    # removing passed on values
    for key in session.keys():
        if key in ['redirect_from','member', 'verification_code']:
            session.pop(key, None)


@main.route('/member/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required()
def member_edit(member_id):
    if current_user.get_type() != 'provider':
        return redirect(url_for('main.index'))

    # retreive the current user's member by its ID
    member = current_user.provider.members.filter_by(id=member_id).first()

    form = MemberForm()

    if form.validate_on_submit():
        pass

    # if the form was sent
    if form.validate_on_submit():

        dob = date_set_to_current_date_on_failure(form.dob.data)
        start_date = date_set_to_current_date_on_failure(form.start_date.data)
        effective_date = date_set_to_current_date_on_failure(
                            form.effective_date.data)
        mature_date = date_set_to_current_date_on_failure(
                        form.mature_date.data)
        exit_date = date_set_to_current_date_on_failure(form.exit_date.data)

        # update the database with the data from the form fields
        member.name = form.name.data
        member.email = form.email.data
        member.action = form.action.data
        member.address = form.address.data
        member.address_additional = form.address_additional.data
        member.telephone = form.telephone.data
        member.dob = dob 
        member.gender = form.gender.data
        member.marital_status = form.marital_status.data
        member.start_date = start_date 
        member.effective_date = effective_date 
        member.mature_date = mature_date 
        member.exit_date = exit_date 
        member.product = form.product.data
        member.plan = form.plan.data
        member.policy_number = form.policy_number.data
        member.client_id_number = form.client_id_number.data
        member.card_number = form.card_number.data
        member.plan_type = form.plan_type.data
        member.remarks = form.remarks.data
        member.dependents = form.dependents.data
        member.sequence = form.sequence.data
        member.patient_type = form.patient_type.data

        if form.photo.data:
            photo_filename = photo_file_name_santizer(form.photo)
            member.photo = photo_filename

        # commit the database changes
        db.session.add(member)
        db.session.commit()

        return redirect(url_for('main.member', member_id=member.id))

     # if the form was just opened
    if request.method != 'POST':
        form.marital_status.default = member.marital_status
        form.patient_type.default = member.patient_type
        form.gender.default = member.gender
        form.process()

        # fill in the form fields with the data from the database
        form.name.data = member.name
        form.email.data = member.email
        form.action.data = member.action
        form.address.data = member.address
        form.address_additional.data = member.address_additional
        form.telephone.data = member.telephone

        if member.dob:
            form.dob.data = member.dob.strftime('%m/%d/%Y')
        else:
            form.dob.data = member.dob

        if member.start_date:
            form.start_date.data = member.start_date.strftime('%m/%d/%Y')
        else:
            form.start_date.data = member.start_date

        if member.effective_date:
            form.effective_date.data = member.effective_date\
                                        .strftime('%m/%d/%Y')
        else:
            form.effective_date.data = member.effective_date

        if member.mature_date:
            form.mature_date.data = member.mature_date.strftime('%m/%d/%Y')
        else:
            form.mature_date.data = member.mature_date

        if member.exit_date:
            form.exit_date.data = member.exit_date.strftime('%m/%d/%Y')
        else:
            form.exit_date.data = member.exit_date

        form.product.data = member.product
        form.plan.data = member.plan
        form.policy_number.data = member.policy_number
        form.client_id_number.data = member.client_id_number
        form.card_number.data = member.card_number
        form.plan_type.data = member.plan_type
        form.remarks.data = member.remarks
        form.dependents.data = member.dependents
        form.sequence.data = member.sequence
        form.patient_type.data = member.patient_type

    return render_template('member-form.html', form=form, member=member)


@main.route('/setup', methods=['GET', 'POST'])
@login_required()
def setup():
    return render_template('setup.html')


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500


@main.route('/search', methods=['GET'])
def search():
    found = {
        'results': []
    }
    query = request.args.get('query')
    if not query or not current_user.is_authenticated:
        return jsonify(found)

    query = query.lower()

    claim_all = models.Claim.query.all()
    claim_current = []
    claim_current = claim_all

    for claim in claim_current:
        # initialazing location variable to put the claim's terminal data here,
        # if no terminal in a claim's object, it remains None
        location = None

        if claim.terminal:
            location = claim.terminal.location

        if query in str(claim.status).lower() \
        or query in str(claim.claim_number).lower() \
        or query in str(claim.claim_type).lower() \
        or query in str(claim.datetime) \
        or query in str(claim.admitted) \
        or query in str(claim.discharged) \
        or query in str(location).lower() \
        or query in str(claim.amount) :
            found['results'].append(claim.id)
            continue

    return jsonify(found)


@main.route('/icd-code/search', methods=['GET'])
def icd_code_search():
    found = []
    query = request.args.get('query')
    query = query.lower()
    
    if not query:
        return render_template('icd-code-search-results.html',
                               icd_codes=None, query=query)

    icd_codes = models.ICDCode.query.all()

    for icd_code in icd_codes:
        if query in icd_code.code.lower() \
        or query in icd_code.description.lower() \
        or query in icd_code.common_term.lower():
            found.append(icd_code)
            continue

    return render_template('icd-code-search-results.html', icd_codes=found,
                               query=query)


@main.route('/sms-verify-form', methods=['GET', 'POST'])
@login_required()
def sms_verify():
    form = SMSVerificationForm()
    verification_phone_number = request.args.get('verification_phone_number')

    # if the form was sent
    if form.validate_on_submit():

        if form.verification_code.data == session['verification_code']:
            if session['redirect_from'] == 'member':
                commit_members()
                return redirect(url_for('main.members'))

            if session['redirect_from'] == 'claim':
                commit_claims()
                return redirect(url_for('main.claims'))

        else:
            flash('Wrong code. Please try again.')

    return render_template('sms-verify-form.html', form=form,
        verification_phone_number=verification_phone_number)