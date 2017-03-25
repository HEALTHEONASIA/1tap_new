from flask import request
from .. import db, models

def date_set_to_current_date_on_failure(data):
    from datetime import datetime
    try:
        date_data = datetime.strptime(data, '%m/%d/%Y')
    except Exception as e:
        date_data = datetime.now()
    
    return date_data

def datetime_set_to_current_date_on_failure(data):
    from datetime import datetime
    try:
        date_data = datetime.strptime(data, '%m/%d/%Y %I:%M %p')
    except Exception as e:
        date_data = datetime.now()
    
    return date_data

# prepare models dictionaries
def prepare_member_dict(member):
    """The function takes the Member model object
    and convert it to the python dictionary"""

    if not member:
        return None

    claim_ids = []

    for claim in member.claims:
        claim_ids.append(str(claim.id))

    message_ids = []

    for message in member.messages:
        message_ids.append(str(message.id))

    call_request_ids = []

    for call_request in member.call_requests:
        call_request_ids.append(str(call_request.id))


    member_dict = {
        'id': member.id,
        'photo': member.photo,
        'name': member.name,
        'email': member.email,
        'action': member.action,
        'address': member.address,
        'address_additional': member.address_additional,
        'tel': member.tel,
        'dob': member.dob.strftime('%m/%d/%Y'),
        'gender': member.gender,
        'marital_status': member.marital_status,
        'start_date': member.start_date.strftime('%m/%d/%Y'),
        'effective_date': member.effective_date.strftime('%m/%d/%Y'),
        'mature_date': member.mature_date.strftime('%m/%d/%Y'),
        'exit_date': member.exit_date.strftime('%m/%d/%Y'),
        'product': member.product,
        'plan': member.plan,
        'policy_number': member.policy_number,
        'national_id': member.national_id,
        'card_number': member.card_number,
        'plan_type': member.plan_type,
        'remarks': member.remarks,
        'dependents': member.dependents,
        'sequence': member.sequence,
        'patient_type': member.patient_type,
        'device_uid': member.device_uid,
        'claims': claim_ids,
        'messages': message_ids,
        'call_requests': call_request_ids
    }

    return member_dict

# convert member dictionaries to models
def convert_dict_member_model(member_dict):
    """The function takes the Member python dictionary
    and convert it to the Member model object"""
    
    dob = date_set_to_current_date_on_failure(member_dict['dob'])
    start_date = date_set_to_current_date_on_failure(member_dict['start_date'])
    effective_date = date_set_to_current_date_on_failure(
                            member_dict['effective_date'])
    mature_date = date_set_to_current_date_on_failure(
                        member_dict['mature_date'])
    exit_date = date_set_to_current_date_on_failure(member_dict['exit_date'])
    
    member = models.Member(
                photo=member_dict['photo'],
                name=member_dict['name'],
                email=member_dict['email'],
                action=member_dict['action'],
                address=member_dict['address'],
                address_additional=member_dict['address_additional'],
                tel=member_dict['tel'],
                dob=dob,
                sex=member_dict['sex'],
                marital_status=member_dict['marital_status'],
                start_date=start_date,
                effective_date=effective_date,
                mature_date=mature_date,
                exit_date=exit_date,
                product=member_dict['product'],
                plan=member_dict['plan'],
                policy_number=member_dict['policy_number'],
                national_id=member_dict['national_id'],
                card_number=member_dict['card_number'],
                plan_type=member_dict['plan_type'],
                remarks=member_dict['remarks'],
                dependents=member_dict['dependents'],
                sequence=member_dict['sequence'],
                patient_type=member_dict['sequence']
                )
                
    return member

# prepare user dict
def prepare_user_dict(user):
    """The function takes the User model object
    and convert it to the python dictionary"""

    terminal_ids = []

    for terminal in user.terminals:
        terminal_ids.append(str(terminal.id))

    claim_ids = []

    for claim in user.claims:
        claim_ids.append(str(claim.id))

    message_ids = []

    for message in user.messages:
        message_ids.append(str(message.id))

    call_request_ids = []

    for call_request in user.call_requests:
        call_request_ids.append(str(call_request.id))

    user_dict = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'terminals': terminal_ids,
        'claims': claim_ids,
        'messages': message_ids,
        'call_requests': call_request_ids,
        'setup_serial_number': user.setup_serial_number,
        'setup_server_url': user.setup_server_url,
        'setup_server_port': user.setup_server_port,
        'setup_module_name': user.setup_module_name,
        'setup_proxy_url': user.setup_module_name,
        'setup_proxy_port': user.setup_proxy_port,
        'setup_username': user.setup_username,
        'setup_password': user.setup_password,
        'setup_request_url': user.setup_request_url,
        'setup_default_path': user.setup_default_path,
        'setup_language': user.setup_language
    }

    return user_dict


# prepare terminal dict
def prepare_terminal_dict(terminal):
    """The function takes the Terminal model object
    and convert it to the python dictionary"""

    claim_ids = []

    for claim in terminal.claims:
        claim_ids.append(str(claim.id))

    terminal_dict = {
        'id': terminal.id,
        'status': terminal.status,
        'serial_number': terminal.serial_number,
        'model': terminal.model,
        'user_id': terminal.user_id,
        'claims': claim_ids,
        'location': terminal.location,
        'version': terminal.version,
        'last_update': terminal.last_update.strftime('%m/%d/%Y'),
        'remarks': terminal.remarks
    }

    return terminal_dict


# prepare claim dict
def prepare_claim_dict(claim):
    """The function takes the Claim model object
    and convert it to the python dictionary"""

    claim_dict = {
        'id': claim.id,
        'status': claim.status,
        'claim_number': claim.claim_number,
        'claim_type': claim.claim_type,
        'datetime': claim.datetime.strftime('%m/%d/%Y %I:%M %p'),
        'admitted': claim.admitted,
        'discharged': claim.discharged,
        'location': claim.location,
        'amount': claim.amount,
        'icd_code': claim.icd_code,
        'user_id': claim.user_id,
        'member_id': claim.member_id,
        'terminal_id': claim.terminal_id,
        'medipay_id': claim.medipay_id,

        # temporarily
        'debug': claim.debug
    }

    return claim_dict
    
# convert claim dictionaries to models
def convert_dict_claim_model(claim_dict):
    """The function takes the Claim python dictionary
    and convert it to the Claim model object"""
    
    claim_date_time = datetime_set_to_current_date_on_failure(claim_dict['datetime'])
    
    claim = models.Claim(
                status=claim_dict['status'],
                amount=claim_dict['amount'],
                claim_number=claim_dict['claim_number'],
                claim_type=claim_dict['claim_type'],
                datetime=claim_date_time,
                location=claim_dict['location'],
                user_id=claim_dict['user_id'],
                member_id=claim_dict['member_id'],
                terminal_id=claim_dict['terminal_id'],
                medipay_id=claim_dict['medipay_id']
            )
    
    return claim

# prepare models lists
def prepare_members_list(members):
    """The function takes the Member model objects list and convert it to the
    python dictionary"""

    if not members:
        return []

    # initialize the results list
    results = []

    for member in members:
        results.append(prepare_member_dict(member))

    return results


def prepare_terminals_list(terminals):
    """The function takes the Terminal model objects list and convert it to the
    python dictionary"""

    if not terminals:
        return []

    # initialize the results list
    results = []

    for terminal in terminals:
        results.append(prepare_terminal_dict(terminal))

    return results


def prepare_claims_list(claims):
    """The function takes the Claim model objects list and convert it to the
    python dictionary"""

    if not claims:
        return []

    # initialize the results list
    results = []

    for claim in claims:
        results.append(prepare_claim_dict(claim))

    return results


def prepare_users_list(users):
    """The function takes the User model objects list and convert it to the
    python dictionary"""

    if not users:
        return []

    # initialize the results list
    results = []

    for user in users:
        results.append(prepare_user_dict(user))

    return results


# functions for getting parameters from POST parameters and JSON
def from_post_to_dict(dest_dict, overwrite=False):
    for key, value in dest_dict.iteritems():
        if not overwrite:
            # if it is the adding operation,
            # the all parameters are required
            if request.form.get(key):
                dest_dict[key] = request.form.get(key)

            else:
                raise ValueError('Missing the required parameter "%s"', key)

        else:
            # in case it is the editing operaition, we change only
            # those parameters, that are available in the POST request
            if request.form.get(key):
                dest_dict[key] = request.form.get(key)

    return dest_dict


def from_json_to_dict(json_dict, dest_dict, overwrite=False):
    for key, value in dest_dict.iteritems():
        if not overwrite:
            # if it is the adding operation,
            # the all parameters are required
            if key in json_dict:
                dest_dict[key] = json_dict[key]

            else:
                raise ValueError('Missing the required parameter "%s"' % key)

        else:
            # in case it is the editing operaition, we change only
            # those parameters, that are available in the JSON
            if key in json_dict:
                dest_dict[key] = json_dict[key]

    return dest_dict


def authorize_api_key():
    api_key = request.args.get('api_key')

    if not api_key:
        # failure, return error, no user object
        return (False, 'API key is missing', None)

    user = models.User.query.filter_by(api_key=api_key).first()

    if not user:
        # failure, return error, no user object
        return (False, 'API key is wrong', None)

    # success, no errors, return user object
    return (True, None, user)


def exclude_keys(keys, dest):
    if keys:
        if type(dest) is dict:
            for key in keys:
                del dest[key]
        elif type(dest) is list:
            for row in dest:
                for key in keys:
                    del row[key]

    return dest
