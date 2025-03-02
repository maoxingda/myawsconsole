from pynamodb import attributes, models


class AccountTransaction(models.Model):
    class Meta:
        table_name = "bi-oltp-account_transaction"

    main_transaction_rn = attributes.UnicodeAttribute(hash_key=True)
    account_rn = attributes.UnicodeAttribute(range_key=True)
    type = attributes.NumberAttribute()
    account_id = attributes.UnicodeAttribute()
    name = attributes.UnicodeAttribute()
    currency = attributes.NumberAttribute()
    amount = attributes.NumberAttribute()
    main_transaction_id = attributes.NumberAttribute()
    external_payment_info = attributes.UnicodeAttribute()


class AccountTransactionDetail(models.Model):
    class Meta:
        table_name = "bi-oltp-account_transaction_detail"

    main_transaction_rn = attributes.UnicodeAttribute()
    main_transaction_id = attributes.NumberAttribute()
    account_transaction_detail_rn = attributes.UnicodeAttribute(hash_key=True)
    account_transaction_detail_id = attributes.NumberAttribute()
    account_rn = attributes.UnicodeAttribute()
    account_id = attributes.UnicodeAttribute()
    name = attributes.UnicodeAttribute()
    amount = attributes.NumberAttribute()
    currency = attributes.NumberAttribute()
    status = attributes.NumberAttribute()
    transaction_time = attributes.NumberAttribute()
    updated_at = attributes.NumberAttribute()
    external_payment_info = attributes.UnicodeAttribute()
    account_type = attributes.NumberAttribute()
