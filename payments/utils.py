"""
JazzCash & EasyPaisa payment gateway helpers.
Sandbox URLs are used by default — switch to live URLs for production.

JazzCash Docs:  https://sandbox.jazzcash.com.pk/
EasyPaisa Docs: https://easypaystg.easypaisa.com.pk/
"""
import hashlib
import hmac
import datetime
from django.conf import settings


# ─────────────────────────────────────────────
#  JAZZCASH
# ─────────────────────────────────────────────

def jazzcash_generate_hash(params: dict) -> str:
    """
    Generates HMAC-SHA256 hash over sorted param values.
    JazzCash requires all params sorted alphabetically.
    """
    sorted_keys   = sorted(params.keys())
    sorted_values = '&'.join(str(params[k]) for k in sorted_keys)
    data          = settings.JAZZCASH_INTEGRITY_SALT + '&' + sorted_values

    return hmac.new(
        settings.JAZZCASH_INTEGRITY_SALT.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()


def jazzcash_build_payload(order) -> dict:
    """
    Builds the full POST payload for JazzCash payment.
    Amount is in paisas (multiply by 100).
    """
    now = datetime.datetime.now()
    exp = now + datetime.timedelta(hours=1)
    txn_ref = f"T{order.id}{int(now.timestamp())}"

    params = {
        'pp_Version':           '1.1',
        'pp_TxnType':           'MWALLET',
        'pp_Language':          'EN',
        'pp_MerchantID':        settings.JAZZCASH_MERCHANT_ID,
        'pp_Password':          settings.JAZZCASH_PASSWORD,
        'pp_TxnRefNo':          txn_ref,
        'pp_Amount':            str(int(order.total * 100)),
        'pp_TxnCurrency':       'PKR',
        'pp_TxnDateTime':       now.strftime('%Y%m%d%H%M%S'),
        'pp_BillReference':     f"ORDER{order.id}",
        'pp_Description':       f"Signatures by Isham Order #{order.id}",
        'pp_TxnExpiryDateTime': exp.strftime('%Y%m%d%H%M%S'),
        'pp_ReturnURL':         settings.JAZZCASH_RETURN_URL,
        'pp_SecureHash':        '',
    }

    # Generate hash over all params except pp_SecureHash
    params['pp_SecureHash'] = jazzcash_generate_hash(
        {k: v for k, v in params.items() if k != 'pp_SecureHash'}
    )
    return params


def jazzcash_verify_callback(data: dict) -> bool:
    """
    Verifies the hash on JazzCash callback.
    Returns True if hash matches — payment is genuine.
    """
    data           = dict(data)
    received_hash  = data.pop('pp_SecureHash', '')
    expected_hash  = jazzcash_generate_hash(data)
    return hmac.compare_digest(received_hash, expected_hash)


# ─────────────────────────────────────────────
#  EASYPAISA
# ─────────────────────────────────────────────

def easypaisa_build_payload(order) -> dict:
    """
    Builds POST payload for EasyPaisa MA (Merchant Account) payment.
    Hash = SHA-256 of specific fields + hash key.
    """
    amount    = f"{order.total:.2f}"
    order_ref = f"EP{order.id}"
    post_url  = settings.JAZZCASH_RETURN_URL.replace('jazzcash', 'easypaisa')

    # Hash string order matters — must follow EasyPaisa docs
    raw_string = (
        settings.EASYPAISA_STORE_ID +
        amount +
        post_url +
        order_ref +
        settings.EASYPAISA_HASH_KEY
    )
    hash_value = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    return {
        'storeId':       settings.EASYPAISA_STORE_ID,
        'amount':        amount,
        'postBackURL':   post_url,
        'orderRefNum':   order_ref,
        'autoRedirect':  '1',
        'paymentMethod': 'MA_PAYMENT',
        'emailAddr':     order.user.email if order.user else '',
        'mobileNum':     order.user.phone if order.user else '',
        'hash':          hash_value,
    }


def easypaisa_verify_callback(data: dict) -> bool:
    """
    Verifies EasyPaisa callback hash.
    """
    received_hash = data.get('hash', '')
    raw_string    = (
        settings.EASYPAISA_STORE_ID +
        data.get('amount', '') +
        data.get('orderRefNum', '') +
        settings.EASYPAISA_HASH_KEY
    )
    expected_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
    return hmac.compare_digest(received_hash, expected_hash)