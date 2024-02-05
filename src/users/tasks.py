from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string

from core.celery import celery_app
from core.settings.environments import DEPLOY_URL
from core.tasks import write_log_file


@celery_app.task
def send_otp_email(id):
    try:
        model = apps.get_model('users.VerificationCode')
        obj = model.objects.get(id=id)
        # if DEBUG:
        #     redirect = ('http://api.localhost:8000/api/users/verify/'
        #                 f'?request={obj.hash}')
        # else:
        #     redirect = (f'https://api.{DEPLOY_URL}.com/api/users/verify/'
        #                 f'?request={obj.hash}')
        if msg_html := render_to_string(f'{obj.otp_for}',
                                        {'redirect': obj.code}):
            if _ := send_mail(subject="Verify Account",
                              message="",
                              from_email=f'{DEPLOY_URL} '
                              f'<no-reply@{DEPLOY_URL}.com>',
                              recipient_list=[obj.email],
                              html_message=msg_html,
                              fail_silently=False):
                obj.is_email_sent = True
                obj.save()
    except Exception as exp:
        write_log_file('otp', f'error for {obj.email} : {exp}', True)


@celery_app.task
def process_global_notifications(notification_id):
    n_class = apps.get_model('users', 'GlobalNotification')
    UserBase = apps.get_model('users', 'UserBase')
    notification = n_class.objects.get(id=notification_id)
    users = UserBase.objects.filter(is_verified=True, is_active=True)

    if notification.trigger_type == n_class.AGENTS:
        users = users.filter(is_agent=True)
    elif notification.trigger_type == n_class.SUBSCRIBED:
        users = users.filter(subscription__status='active')
    emails = [user.email for user in users]
    status = True
    # send notification emails here
    print(emails)
    notification.is_processed = status
    notification.save()
    return True
