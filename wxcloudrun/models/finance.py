from django.db import models

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()
    account = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_large = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_transaction'

class Asset(models.Model):
    ASSET_TYPES = (
        ('cash', 'Cash'),
        ('stock', 'Stock'),
        ('house', 'House'),
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=ASSET_TYPES)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    desc = models.CharField(max_length=200, blank=True, null=True)
    stock_code = models.CharField(max_length=20, blank=True, null=True)
    shares = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_asset'

class FixedItem(models.Model):
    ITEM_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    type = models.CharField(max_length=10, choices=ITEM_TYPES)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    frequency = models.CharField(max_length=50, default='monthly')
    date_value = models.IntegerField(help_text="Day of the month")
    account = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_fixed_item'

class FutureItem(models.Model):
    ITEM_TYPES = (
        ('cash', 'Cash'),
        ('stock', 'Stock'),
    )
    type = models.CharField(max_length=10, choices=ITEM_TYPES)
    text = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    stock_code = models.CharField(max_length=20, blank=True, null=True)
    shares = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    desc = models.CharField(max_length=200, blank=True, null=True)
    inactive_icon = models.CharField(max_length=50, default='circle')
    active_icon = models.CharField(max_length=50, default='checked')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_future_item'

class Loan(models.Model):
    LOAN_METHODS = (
        ('equal_principal', 'Equal Principal'),
        ('equal_principal_interest', 'Equal Principal and Interest'),
    )
    name = models.CharField(max_length=100)
    principal = models.DecimalField(max_digits=20, decimal_places=2)
    periods = models.IntegerField()
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    method = models.CharField(max_length=50, choices=LOAN_METHODS, default='equal_principal')
    repayment_date = models.IntegerField(help_text="Day of the month (1-28)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_loan'

class AssetCorrection(models.Model):
    cash_actual = models.DecimalField(max_digits=20, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_asset_correction'
