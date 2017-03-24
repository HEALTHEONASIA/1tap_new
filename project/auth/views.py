import string
import random
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from . import auth
from .. import mail
from ..models import db, User
from .forms import LoginForm, ForgotPasswordForm


def pass_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def login_validation(form):
    user = User.query.filter_by(email=form.email.data).first()

    if user is not None and user.verify_password(form.password.data):
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('main.index'))
    else:
        flash('Invalid username or password.')
        return render_template('auth/login.html', form=form, menu_unpin=True)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        return login_validation(form)

    return render_template('auth/login.html', form=form, menu_unpin=True)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    #flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        rand_pass = pass_generator(size=8)
        user.password = rand_pass
        db.session.add(user)

        msg = Message("Forgot password email",
                      sender=("MediPay",
                              "request@app.medipayasia.com"),
                      recipients=[user.email])

        msg.html = """
        <h3>You have requested a new password for your MediPay account.</h3>
        <p>Here is your access credentials:</p>
        <p>Login: %s<br>
        Password: %s</p>
        """ % (user.email, rand_pass)

        mail.send(msg)
        flash('Please, check your email for a new password.')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

