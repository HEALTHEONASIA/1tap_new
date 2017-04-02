import json, re, requests

from datetime import datetime
from flask import jsonify, request, render_template

from .helpers import *
from . import api
from .. import db, models


@api.route('/members', methods=['GET'])
def members():
    """The function returns all the members"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    members = models.Member.query.all()

    # return the result in a JSON format
    return jsonify(prepare_members_list(members))


@api.route('/member/<int:member_id>', methods=['GET'])
def member_get(member_id):
    """The function returns the member by its ID"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    member = models.Member.query.get(member_id)

    if not member:
        return 'Error: no member #%d is found' % member_id

    # return the result in a JSON format.
    # The one request is returned like a list
    # with the single element
    return jsonify([prepare_member_dict(member)])


@api.route('/users', methods=['GET'])
def users():
    """The function returns all the users"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    users = models.User.query.all()

    # return the result in a JSON format
    return jsonify(prepare_users_list(users))


@api.route('/user/<int:user_id>', methods=['GET'])
def user_get(user_id):
    """The function returns the user by its ID"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    user = models.User.query.get(user_id)

    if not user:
        return 'Error: no user #%d is found' % user_id

    # return the result in a JSON format.
    # The one request is returned like a list
    # with the single element
    return jsonify([prepare_user_dict(user)])


@api.route('/terminals', methods=['GET'])
def terminals():
    """The function returns all the terminals"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    terminals = models.Terminal.query.all()

    # return the result in a JSON format
    return jsonify(prepare_terminals_list(terminals))


@api.route('/terminal/<int:terminal_id>', methods=['GET'])
def terminal_get(terminal_id):
    """The function returns the terminal by its ID"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    terminal = models.Terminal.query.get(terminal_id)

    if not terminal:
        return 'Error: no terminal #%d is found' % terminal_id

    # return the result in a JSON format.
    # The one request is returned like a list
    # with the single element
    return jsonify([prepare_terminal_dict(terminal)])


@api.route('/claim', methods=['GET'])
def claim():
    """The function returns all the claims"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    claims = models.Claim.query.all()

    # return the result in a JSON format
    return jsonify(prepare_claims_list(claims))


@api.route('/claim/<int:claim_id>', methods=['GET'])
def claim_get(claim_id):
    """The function returns the claim by its ID"""

    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    claim = models.Claim.query.get(claim_id)

    if not claim:
        return 'Error: no claim #%d is found' % claim_id

    # return the result in a JSON format.
    # The one request is returned like a list
    # with the single element
    return jsonify([prepare_claim_dict(claim)])


@api.route('/member/add/json', methods=['POST'])
def member_add_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    members_list = []

    for row in json:
        member_dict = {
            'photo': None,
            'name': None,
            'email': None,
            'action': None,
            'address': None,
            'address_additional': None,
            'tel': None,
            'dob': None,
            'gender': None,
            'marital_status': None,
            'start_date': None,
            'effective_date': None,
            'mature_date': None,
            'exit_date': None,
            'product': None,
            'plan': None,
            'policy_number': None,
            'national_id': None,
            'card_number': None,
            'plan_type': None,
            'remarks': None,
            'dependents': None,
            'sequence': None,
            'patient_type': None
        }

        member_dict = from_json_to_dict(row, member_dict)
        members_list.append(member_dict)

    for row_num, row in enumerate(members_list):
        if not row['name']:
            return 'Error: the "name" parameter cannot be empty'

        member = models.Member(photo=row['photo'],
                               name=row['name'],
                               email=row['email'],
                               action=row['action'],
                               address=row['address'],
                               address_additional=row['address_additional'],
                               tel=row['tel'],
                               dob=datetime.strptime(row['dob'], '%m/%d/%Y'),
                               gender=row['gender'],
                               marital_status=row['marital_status'],
                               start_date=datetime.strptime(row['start_date'],
                                                            '%m/%d/%Y'),
                               effective_date=datetime.strptime(
                                                row['effective_date'],
                                                '%m/%d/%Y'),
                               mature_date=datetime.strptime(
                                                row['mature_date'],
                                                '%m/%d/%Y'),
                               exit_date=datetime.strptime(row['exit_date'],
                                                           '%m/%d/%Y'),
                               product=row['product'],
                               plan=row['plan'],
                               policy_number=\
                                   row['policy_number'],
                               national_id=row['national_id'],
                               card_number=row['card_number'],
                               plan_type=row['plan_type'],
                               remarks=row['remarks'],
                               dependents=row['dependents'],
                               sequence=row['sequence'],
                               patient_type=row['patient_type'])

        db.session.add(member)
        db.session.commit()

        members_list[row_num]['id'] = member.id

    return jsonify(members_list)


@api.route('/member/edit/json', methods=['POST'])
def member_edit_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    members_list = []

    # the keys of the json dictionary are the IDs of the objects
    for key, value in json.iteritems():
        member_id = key
        member = models.Member.query.get(member_id)

        if not member:
            return 'The Member with the ' + \
                    'id = %s is not found.' % member_id

        # put the found object's data in a dictionary
        member_dict = prepare_member_dict(member)

        member_dict = from_json_to_dict(value, member_dict, overwrite=True)
        members_list.append(member_dict)

    for row in members_list:
        member = models.User.query.get(row['id'])

        if not row['name']:
            return 'Error: the "name" parameter cannot be empty'

        member.photo = row['photo']
        member.name = row['name']
        member.email = row['email']
        member.action = row['action']
        member.address = row['address']
        member.address_additional = row['address_additional']
        member.tel = row['tel']
        member.dob = datetime.strptime(row['dob'], '%m/%d/%Y')
        member.gender = row['gender']
        member.marital_status = row['marital_status']
        member.start_date = datetime.strptime(row['start_date'], '%m/%d/%Y')
        member.effective_date = datetime.strptime(row['effective_date'],
                                                  '%m/%d/%Y')
        member.mature_date = datetime.strptime(row['mature_date'], '%m/%d/%Y')
        member.exit_date = datetime.strptime(row['exit_date'], '%m/%d/%Y')
        member.product = row['product']
        member.plan = row['plan']
        member.policy_number = row['policy_number']
        member.national_id = row['national_id']
        member.card_number = row['card_number']
        member.plan_type = row['plan_type']
        member.remarks = row['remarks']
        member.dependents = row['dependents']
        member.sequence = row['sequence']
        member.patient_type = row['patient_type']

        db.session.add(member)

    return jsonify(members_list)


@api.route('/member/login', methods=['POST'])
def member_login():
    """Authorizes a member and returns a token"""
    json = request.get_json()

    if not json:
        return jsonify({'msg': 'missing json'})

    if 'email' not in json or 'password' not in json:
        return jsonify({'msg': 'missing required parameters'})

    user = models.User.query.filter_by(email=json['email'],
                                       user_type='member').first()

    if user is not None and user.verify_password(json['password']):
        member = user.member

        claims_list = []
        for claim in member.claims:
            if claim.datetime:
                claim_datetime = claim.datetime.strftime('%d/%m/%Y %I:%M %p')
            else
                claim_datetime = None
            claim_dict = {
                'id': claim.id,
                'status': claim.status,
                'datetime': claim_datetime,
                'amount': claim.amount
            }
            claims_list.append(claim_dict)

        if member.dob:
            member_dob = member.dob.strftime('%d/%m/%Y')
        else:
            member_dob = None

        member_dict = {
            'id': member.id,
            'name': member.name,
            'photo': member.photo,
            'dob': member_dob,
            'gender': member.gender,
            'tel': member.tel,
            'national_id': member.national_id,
            'claims': claims_list
        }

        return jsonify({'msg': 'success', 'member': member_dict})
    else:
        return jsonify({'msg': 'error'})


@api.route('/member/register', methods=['POST'])
def member_register():
    """Registers a new member"""
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()


@api.route('/member/logout', methods=['POST'])
def member_logout():
    """Deletes a member's token from a database"""
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()


@api.route('/member/check-in', methods=['POST'])
def member_check_in():
    """Registers a member's visit to the hospital,
    namely, adds a new claim to the system"""
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()


@api.route('/member/info', methods=['GET'])
def member_info():
    """Returns member's info, including visits history"""
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()


@api.route('/member/info/update', methods=['POST'])
def member_info_update():
    """Updates general member's info"""
    json = request.get_json()

    if not json:
        return jsonify({'msg': 'missing json'})

    if 'id' not in json:
        return jsonify({'msg': 'missing member_id'})

    member = models.Member.query.get(json['id'])

    if not member:
        return jsonify({'msg': 'no such member'})

    member.name = json['name']
    member.photo = json['photo']
    try:
        member.dob = datetime.strptime(json['dob'], '%m/%d/%Y')
    except:
        member.dob = None
    member.gender = json['gender']
    member.tel = json['tel']
    member.national_id = json['national_id']

    db.session.add(member)
    db.session.commit()

    claims_list = []
    for claim in member.claims:
        if claim.datetime:
            claim_datetime = claim.datetime.strftime('%d/%m/%Y %I:%M %p')
        else
            claim_datetime = None
        claim_dict = {
            'id': claim.id,
            'status': claim.status,
            'datetime': claim_datetime,
            'amount': claim.amount
        }
        claims_list.append(claim_dict)

    if member.dob:
        member_dob = member.dob.strftime('%d/%m/%Y')
    else:
        member_dob = None

    member_dict = {
        'id': member.id,
        'name': member.name,
        'photo': member.photo,
        'dob': member_dob,
        'gender': member.gender,
        'tel': member.tel,
        'national_id': member.national_id,
        'claims': claims_list
    }

    return jsonify({'msg': 'success', 'member': member_dict})


@api.route('/user/add/json', methods=['POST'])
def user_add_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    users_list = []

    for row in json:
        user_dict = {
            'name': None,
            'email': None,
            'role': None,
            'password': None,
            'setup_serial_number': None,
            'setup_server_url': None,
            'setup_server_port': None,
            'setup_module_name': None,
            'setup_proxy_url': None,
            'setup_proxy_port': None,
            'setup_username': None,
            'setup_password': None,
            'setup_request_url': None,
            'setup_default_path': None,
            'setup_language': None,
        }

        user_dict = from_json_to_dict(row, user_dict)
        users_list.append(user_dict)

    for row_num, row in enumerate(users_list):
        if not row['name']:
            return 'Error: the "name" parameter cannot be empty'

        if not row['email']:
            return 'Error: the "email" parameter cannot be empty'

        if not row['password']:
            return 'Error: the "password" parameter cannot be empty'

        if models.User.query.filter_by(
          email=row['email']).first():
            return 'Error: the "email" is already registered'

        user = models.User(name=row['name'],
                           email=row['email'],
                           role=row['role'],
                           password=row['password'],
                           setup_serial_number=row['setup_serial_number'],
                           setup_server_url=row['setup_server_url'],
                           setup_server_port=row['setup_server_port'],
                           setup_module_name=row['setup_module_name'],
                           setup_proxy_url=row['setup_proxy_url'],
                           setup_proxy_port=row['setup_proxy_port'],
                           setup_username=row['setup_username'],
                           setup_password=row['setup_password'],
                           setup_request_url=row['setup_request_url'],
                           setup_default_path=row['setup_default_path'],
                           setup_language=row['setup_language'])

        db.session.add(user)
        db.session.commit()

        users_list[row_num]['id'] = user.id

    return jsonify(users_list)


@api.route('/user/edit/json', methods=['POST'])
def user_edit_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    users_list = []

    # the keys of the json dictionary are the IDs of the objects
    for key, value in json.iteritems():
        user_id = key
        user = models.User.query.get(user_id)

        if not user:
            return 'The User with the ' + \
                    'id = %s is not found.' % user_id

        # put the found object's data in a dictionary
        user_dict = prepare_user_dict(user)

        user_dict = from_json_to_dict(value, user_dict, overwrite=True)
        users_list.append(user_dict)

    for row in users_list:
        user = models.User.query.get(row['id'])

        if not row['name']:
            return 'Error: the "name" parameter cannot be empty'

        if not row['email']:
            return 'Error: the "email" parameter cannot be empty'

        if not row['password']:
            return 'Error: the "password" parameter cannot be empty'

        if models.User.query.filter_by(
          email=row['email']).first():
            return 'Error: the "email" is already registered'

        user.name = row['name']
        user.email = row['email']
        user.role = row['role']
        user.password = row['password']
        user.setup_serial_number = row['setup_serial_number']
        user.setup_server_url = row['setup_server_url']
        user.setup_server_port = row['setup_server_port']
        user.setup_module_name = row['setup_module_name']
        user.setup_proxy_url = row['setup_proxy_url']
        user.setup_proxy_port = row['setup_proxy_port']
        user.setup_username = row['setup_username']
        user.setup_password = row['setup_password']
        user.setup_request_url = row['setup_request_url']
        user.setup_default_path = row['setup_default_path']
        user.setup_language = row['setup_language']

        db.session.add(user)

    return jsonify(users_list)


@api.route('/terminal/add/json', methods=['POST'])
def terminal_add_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    terminals_list = []

    for row in json:
        terminal_dict = {
            'status': None,
            'serial_number': None,
            'model': None,
            'user_id': None,
            'location': None,
            'version': None,
            'last_update': None,
            'remarks': None,
        }

        terminal_dict = from_json_to_dict(row, terminal_dict)
        terminals_list.append(terminal_dict)

    for row_num, row in enumerate(temrinals_list):
        if not models.User.query.get(row['user_id']):
            return 'Error: no user #%d is found' % row['user_id']

        terminal = models.Terminal(status=row['status'],
                                   serial_number=row['serial_number'],
                                   model=row['model'],
                                   user_id=row['user_id'],
                                   location=row['location'],
                                   version=row['version'],
                                   last_update=datetime.strptime(
                                                 row['last_update'],
                                                 '%m/%d/%Y'),
                                   remarks=row['remarks'])

        db.session.add(terminal)
        db.session.commit()

        terminals_list[row_num]['id'] = terminal.id

    return jsonify(terminals_list)


@api.route('/terminal/edit/json', methods=['POST'])
def terminal_edit_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    terminals_list = []

    # the keys of the json dictionary are the IDs of the objects
    for key, value in json.iteritems():
        terminal_id = key
        terminal = models.Terminal.query.get(terminal_id)

        if not terminal:
            return 'The Terminal with the ' + \
                    'id = %s is not found.' % terminal_id

        # put the found object's data in a dictionary
        terminal_dict = prepare_terminal_dict(terminal)

        terminal_dict = from_json_to_dict(value, terminal_dict, overwrite=True)
        terminals_list.append(terminal_dict)

    for row in terminals_list:
        terminal = models.Terminal.query.get(row['id'])

        if not models.User.query.get(row['user_id']):
            return 'Error: no user #%d is found' % row['user_id']

        terminal.status = row['status']
        terminal.serial_number = row['serial_number']
        terminal.model = row['model']
        terminal.user_id = row['user_id']
        terminal.location = row['location']
        terminal.version = row['version']
        terminal.last_update = datetime.strptime(row['last_update'],
                                                 '%m/%d/%Y')
        terminal.remarks = row['remarks']

        db.session.add(terminal)

    return jsonify(terminals_list)


@api.route('/terminal/add', methods=['POST'])
def terminal_add():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json_ = request.get_json()

    # find the terminal with the given device uid
    terminal = models.Terminal.query.filter_by(device_uid=json_['uid']).first()

    # if no terminal is found, it is a new terminal and we add it
    if not terminal:
        terminal = models.Terminal(device_uid=json_['uid'],
                                   provider_id=user.provider.id)
        db.session.add(terminal)
        db.session.commit()
    elif terminal not in user.provider.terminals:
        user.provider.terminals.append(terminal)
        db.session.add(user.provider)
        db.session.commit()

    # returns the url on the current terminal's edit page
    # it will redirect the user of the 1TAP desktop app to this page
    return jsonify({
        'redirect_url': 'https://1tapsystem.com/terminal/%d/edit' % terminal.id
    })


@api.route('/claim/add', methods=['POST'])
def claim_add():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json_ = request.get_json()

    # find the member with the given device uid
    member = models.Member.query.filter_by(device_uid=json_['uid']).first()

    # if no member is found, it is the first member visit and we add him
    if not member:
        member = models.Member(device_uid=json_['uid'])
        member.providers.append(user.provider)
        db.session.add(member)
        db.session.commit()
    elif user.provider not in member.providers:
        member.providers.append(user.provider)
        db.session.add(member)
        db.session.commit()

    # add new claim
    claim = models.Claim(datetime=datetime.now(),
                         provider_id=user.provider.id,
                         member_id=member.id)

    db.session.add(claim)
    db.session.commit()

    # returns the url on the current claim's edit page
    # it will redirect the user of the 1TAP desktop app to this page
    return jsonify({
        'redirect_url': 'https://1tapsystem.com/claim/%d' % claim.id
    })


@api.route('/claim/add-by-terminal', methods=['POST'])
def claim_add_by_terminal():
    json = request.get_json()

    if 'user_id' not in json or 'terminal_uid' not in json:
        return jsonify({'msg': 'error: not enough parameters'})

    # find the member with the given id
    member = models.Member.query.filter_by(id=json['user_id']).first()

    # find the terminal with the given device_uid
    terminal = models.Terminal.query.filter_by(
                    device_uid=json['terminal_uid']).first()

    # if there is no member or terminal, do nothing
    if not member or not terminal:
        return jsonify({'msg': 'error'})

    provider = terminal.provider

    # if it's the first visit to the hospital,
    # add the provider to member's providers list
    if provider not in member.providers:
        member.providers.append(provider)
        db.session.add(member)
        db.session.commit()

    # add new claim
    claim = models.Claim(datetime=datetime.now(),
                         provider_id=provider.id,
                         terminal_id=terminal.id,
                         member_id=member.id)

    db.session.add(claim)
    db.session.commit()

    claim_dict = {
        'id': claim.id,
        'status': claim.status,
        'datetime': claim.datetime,
        'amount': claim.amount
    }

    # returns successful json
    return jsonify({'msg': 'success', 'claim': claim_dict})


@api.route('/claim/add/json', methods=['POST'])
def claim_add_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    claims_list = []

    for row in json:
        claim_dict = {
            'status': None,
            'claim_number': None,
            'claim_type': None,
            'datetime': None,
            'admitted': None,
            'discharged': None,
            'amount': None,
            'icd_code': None,
            'user_id': None,
            'member_id': None,
            'terminal_id': None,
            'medipay_id': None
        }

        claim_dict = from_json_to_dict(row, claim_dict)
        claims_list.append(claim_dict)

    for row_num, row in enumerate(claims_list):
        if not models.User.query.get(row['user_id']):
            return 'Error: no user #%d is found' % row['user_id']

        if not models.Member.query.get(row['member_id']):
            return 'Error: no member #%d is found' % row['member_id']

        if not models.Terminal.query.get(row['terminal_id']):
            return 'Error: no terminal #%d is found' % row['terminal_id']

        if 'datetime' in row and row['datetime']:
            claim_datetime = datetime.strptime(row['datetime'],
                                                 '%m/%d/%Y')
        else:
            claim_datetime = datetime.now()

        claim = models.Claim(status=row['status'],
                             claim_number=row['claim_number'],
                             claim_type=row['claim_type'],
                             datetime=claim_datetime,
                             admitted=row['admitted'],
                             discharged=row['discharged'],
                             amount=row['amount'],
                             icd_code=row['icd_code'],
                             user_id=row['user_id'],
                             member_id=row['member_id'],
                             terminal_id=row['terminal_id'],
                             medipay_id=row['medipay_id'])

        db.session.add(claim)
        db.session.commit()

        claims_list[row_num]['id'] = claim.id

    return jsonify(claims_list)


@api.route('/claim/edit/json', methods=['POST'])
def claim_edit_json():
    authorized, error, user = authorize_api_key()

    if not authorized:
        return error

    json = request.get_json()

    claims_list = []

    # the keys of the json dictionary are the IDs of the objects
    for key, value in json.iteritems():
        claim_id = key
        claim = models.Claim.query.get(claim_id)

        if not claim:
            return 'The Claim with the ' + \
                    'id = %s is not found.' % claim_id

        # put the found object's data in a dictionary
        claim_dict = prepare_claim_dict(claim)

        claim_dict = from_json_to_dict(value, claim_dict,
                                             overwrite=True)
        claim_list.append(claim_dict)

    for row in claims_list:
        claim = models.Claim.query.get(row['id'])

        if not models.User.query.get(row['user_id']):
            return 'Error: no user #%d is found' % row['user_id']

        if not models.Member.query.get(row['member_id']):
            return 'Error: no member #%d is found' % row['member_id']

        if not models.Terminal.query.get(row['terminal_id']):
            return 'Error: no terminal #%d is found' % row['terminal_id']

        claim.status = row['status']
        claim.claim_number = row['claim_number']
        claim.claim_type = row['claim_type']
        claim.datetime = datetime.strptime(row['datetime'], '%m/%d/%Y')
        claim.admitted = row['admitted']
        claim.discharged = row['discharged']
        claim.amount = row['amount']
        claim.icd_code = row['icd_code']
        claim.user_id = row['user_id']
        claim.member_id = row['member_id']
        claim.medipay_id = row['medipay_id']
        claim.terminal_id = row['terminal_id']

        db.session.add(claim)

    return jsonify(claims_list)

