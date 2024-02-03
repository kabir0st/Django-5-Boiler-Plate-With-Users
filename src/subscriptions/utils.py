import random
from django.apps import apps
import hashlib
import hmac
import json

import requests
from core.settings.environments import (DEPLOY_URL, FONEPAY_KEY,
                                        FONEPAY_MERCHANT_CODE,
                                        FONEPAY_PASSWORD, FONEPAY_USERNAME)
from core.tasks import write_log_file


def generate_fonepay_qr(fonepay_obj):
    if len(FONEPAY_USERNAME) < 2 or len(FONEPAY_PASSWORD) < 2 or len(
            FONEPAY_MERCHANT_CODE) < 2:
        raise Exception('Fonepay creds are not set in setting.')
    url = ('https://merchantapi.fonepay.com/api/merchant/'
           'merchantDetailsForThirdParty/thirdPartyDynamicQrDownload')
    data = {
        'amount': float(fonepay_obj.amount),
        'remarks1': f"{fonepay_obj.invoice_number}",
        'remarks2': str(f"{DEPLOY_URL}"),
        'prn': f'{fonepay_obj.invoice_number} Payment {fonepay_obj.id}',
        'merchantCode': int(FONEPAY_MERCHANT_CODE),
        'dataValidation': "",
        'username': FONEPAY_USERNAME,
        'password': FONEPAY_PASSWORD
    }
    to_be_hash = (f'{data["amount"]},{data["prn"]},{data["merchantCode"]},'
                  f'{data["remarks1"]},{data["remarks2"]}')
    key = FONEPAY_KEY
    byte_key = bytes(key, 'UTF-8')
    hashed = hmac.new(byte_key, to_be_hash.encode(), hashlib.sha256)
    data['dataValidation'] = str(hashed.hexdigest())
    res = requests.post(url=url, json=data)
    res = res.json()
    if res['success']:
        fonepay_obj.qr_status = 'requested'
        fonepay_obj.last_response_from_fonepay = json.dumps(res)
        fonepay_obj.save()
        res['fonepay_payment_id'] = fonepay_obj.id
        return (res)
    else:
        fonepay_obj.qr_status = 'failed'
        fonepay_obj.last_response_from_fonepay = str(res.text)
        fonepay_obj.save()
        write_log_file('payments/fonepay/', f"{fonepay_obj.id}: {res}", True)
        return {'status': False, 'msg': res.text}


def verify_qr(fonepay_obj):
    if len(FONEPAY_USERNAME) < 2 or len(FONEPAY_PASSWORD) < 2 or len(
            FONEPAY_MERCHANT_CODE) < 2:
        raise Exception('Fonepay creds are not set in setting.')
    url = ('https://merchantapi.fonepay.com/api/merchant/'
           'merchantDetailsForThirdParty/thirdPartyDynamicQrGetStatus')
    data = {
        'prn': f'{fonepay_obj.invoice_number} Payment {fonepay_obj.id}',
        'merchantCode': int(FONEPAY_MERCHANT_CODE),
        'dataValidation': "",
        'username': FONEPAY_USERNAME,
        'password': FONEPAY_PASSWORD
    }
    to_be_hash = f'{data["prn"]},{data["merchantCode"]}'
    key = FONEPAY_KEY
    byte_key = bytes(key, 'UTF-8')
    hashed = hmac.new(byte_key, to_be_hash.encode(), hashlib.sha256)
    data['dataValidation'] = str(hashed.hexdigest())
    res = requests.post(url=url, json=data)
    res = res.json()
    if res['paymentStatus'] == "success":
        fonepay_obj.is_verified_from_server = True
        fonepay_obj.trace_id = res['fonepayTraceId']
        fonepay_obj.last_response_from_fonepay = json.dumps(res)
        fonepay_obj.save()
        res['status'] = True
        return res
    else:
        write_log_file('payments/fonepay/', f"{fonepay_obj.id}: {res.text}",
                       True)
        return {'status': False, 'msg': res.text}


def generate_check_sum_number(length=6):
    digits = [random.randint(0, 9) for _ in range(length - 1)]
    for i in range(length - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = (10 - sum(digits) % 10) % 10

    digits.append(checksum)
    luhn_number = ''.join(map(str, digits))
    return luhn_number


def generate_unique_cards(discount, count):
    model = apps.get_model('subscriptions', 'Code')
    if discount.count_limit > 0:
        for _ in range(count):
            code = f"{discount.code_prefix}-{generate_check_sum_number()}"
            if not discount.codes.filter(code=code).exists():
                model.objects.create(discount=discount, code=code)
    else:
        raise Exception("Limit must be set to generate"
                        " unique gift codes for the gift card.")


def delete_unique_cards(discount, count):
    cards = discount.codes.filter(is_used=False)
    if len(cards) < count:
        raise Exception('Number of gift cards used is '
                        'greater than the limit you are trying to assign.')
    for i in range(count):
        card = cards[i]
        card.delete()
