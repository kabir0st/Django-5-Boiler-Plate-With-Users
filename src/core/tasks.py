import contextlib
from os import makedirs, path

import openpyxl
import pandas as pd
from django.apps import apps
from django.core.mail import send_mail
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now

from core.celery import celery_app


def get_path(e_path):
    file_path = f"{e_path}/{str(now().date())}/"
    if not path.exists(file_path):
        makedirs(file_path)
    return file_path


@celery_app.task
def write_log_file(log_type, msg, is_error=False):
    file_name = 'error' if is_error else 'yield'
    file = f"{get_path('logs/'+log_type)}/{file_name}.log"

    with open(file, 'a') as f:
        f.write(f"{now()} : {msg}\n")


@celery_app.task
def send_email(to, subject, message=None, html=None, obj_id=None):
    if res := send_mail(
            subject,
            message,
            'contact@freedomadventuretreks.com', [to],
            html_message=html,
    ):
        write_log_file.delay('email', f"Mail sent to: {to} {subject}")
    else:
        write_log_file.delay('email',
                             f"Failed To Send Email, {to} {subject}; {res}")


def generate_data_format(queryset):
    return {}


def extract_field_data(obj):
    data = {}
    exclude_fields_type = [models.ImageField, models.FileField]
    exclude_field_name = ['password', 'groups', 'user_permissions']
    for field in obj._meta.get_fields():
        with contextlib.suppress(Exception):
            if field.name in exclude_field_name:
                continue
            if isinstance(field, models.OneToOneRel):
                if hasattr(obj, field.name):
                    ext = extract_field_data(getattr(obj, field.name))
                    ext = {
                        f'{field.name} : {key}': value
                        for key, value in ext.items()
                    }
                    data = {**ext, **data}
            elif isinstance(field, models.ManyToManyField):
                data[field.name] = []
                names = []
                for in_obj in getattr(obj, field.name).filter():
                    if obj.__class__.__name__ in ['Ticket', 'InvoiceSummary'
                                                  ] and field.name in [
                            'addons']:
                        data[f"Addon {str(in_obj)}"] = getattr(
                            obj, 'addon_quantity').get(str(in_obj.id), 0)
                    names.append(str(in_obj))

                data[field.name] = ", ".join(names)

            elif isinstance(field, (
                    models.ManyToOneRel, models.ManyToManyRel)):
                if names := [
                        str(in_obj)
                        for in_obj in getattr(obj, field.name).filter()
                ]:
                    data[field.name] = ", ".join(names)
            elif not isinstance(field, tuple(exclude_fields_type)):
                if hasattr(obj, field.name):
                    data[field.name] = str(getattr(obj, field.name))
    return data


@celery_app.task
def export_data_task(document_id, ids):
    from users.models import Document
    document = Document.objects.get(id=document_id)
    try:
        model = apps.get_model(document.model)
        models = model.objects.filter(id__in=ids).order_by('id').distinct('id')
        data = [extract_field_data(obj) for obj in models]
        df = pd.DataFrame(data)
        file_path = f"media/reports/{document.model}/"
        df.fillna(0)
        if not path.exists(file_path):
            makedirs(file_path)
        name = slugify(f"{document.name}_{document.created_at}")
        with pd.ExcelWriter(
                f'media/reports/{document.model}/{name}.xlsx') as writer:
            df.to_excel(writer,
                        sheet_name=f'{document.model}',
                        index=False,
                        na_rep='Nan')
            worksheet = writer.sheets[f'{document.model}']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(),
                                   len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(
                    col_idx + 1)].width = column_width

        document.document = str(
            f'{file_path.replace(f"media/", "")}{name}.xlsx')
        document.status = 'Done'
        document.save()
    except Exception as e:
        document.status = f'Error {e}'
        document.save()
