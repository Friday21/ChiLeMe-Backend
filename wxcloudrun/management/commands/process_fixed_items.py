import datetime
import logging
import decimal
import calendar
from django.core.management.base import BaseCommand
from wxcloudrun.models import FixedItem, Transaction, Asset, Loan

logger = logging.getLogger('log')

class Command(BaseCommand):
    help = 'Process fixed income and expenses'

    def handle(self, *args, **options):
        logger.info('Starting fixed items processing...')
        
        today = datetime.date.today()
        current_year = today.year
        current_month = today.month
        current_day = today.day
        
        # Helper to get scheduled date safely
        def get_scheduled_date(day):
            try:
                # Handle cases where day is larger than month length
                last_day = calendar.monthrange(current_year, current_month)[1]
                target_day = min(day, last_day)
                return datetime.date(current_year, current_month, target_day)
            except Exception as e:
                logger.error(f"Error calculating date for day {day}: {e}")
                return None

        # 1. Process Fixed Items
        # Filter items that should have run by now (inclusive)
        fixed_items = FixedItem.objects.filter(date_value__lte=current_day)
        
        if fixed_items.exists():
            for item in fixed_items:
                try:
                    scheduled_date = get_scheduled_date(item.date_value)
                    if not scheduled_date:
                        continue

                    # Check for duplicate transaction for this month
                    note_identifier = f"Fixed Item: {item.name}"
                    
                    exists = Transaction.objects.filter(
                        user_openId=item.user_openId,
                        date__year=current_year,
                        date__month=current_month,
                        note=note_identifier
                    ).exists()
                    
                    if exists:
                        continue
                    
                    logger.info(f"Processing FixedItem {item.name} (ID: {item.id}) scheduled for {scheduled_date}")

                    # Create Transaction
                    transaction = Transaction.objects.create(
                        user_openId=item.user_openId,
                        type=item.type,
                        category='Fixed Item', 
                        amount=item.amount,
                        date=scheduled_date, # Use the scheduled date
                        account=item.account,
                        note=note_identifier
                    )
                    logger.info(f"Created Transaction {transaction.id}")
                    
                    # Update Asset
                    assets = Asset.objects.filter(user_openId=item.user_openId, name=item.account)
                    if assets.exists():
                        asset = assets.first()
                        original_value = asset.value
                        
                        if item.type == 'income':
                            asset.value += item.amount
                        elif item.type == 'expense':
                            asset.value -= item.amount
                        
                        asset.save()
                        logger.info(f"Updated Asset {asset.name} (ID: {asset.id}) value from {original_value} to {asset.value}")
                    else:
                        logger.warning(f"Asset '{item.account}' not found for user {item.user_openId}. Transaction created but asset not updated.")
                        
                except Exception as e:
                    logger.error(f"Error processing item {item.name}: {e}")
        else:
            logger.info(f'No fixed items scheduled on or before day {current_day}.')

        # 2. Process Loans
        loans = Loan.objects.filter(repayment_date__lte=current_day)
        
        if loans.exists():
            for loan in loans:
                try:
                    if loan.periods <= 0:
                        continue

                    scheduled_date = get_scheduled_date(loan.repayment_date)
                    if not scheduled_date:
                         continue

                    note_identifier = f"Loan Repayment: {loan.name}"
                    
                    # Check for duplicate for this month
                    exists = Transaction.objects.filter(
                        user_openId=loan.user_openId,
                        date__year=current_year,
                        date__month=current_month,
                        note=note_identifier
                    ).exists()
                    
                    if exists:
                        continue
                    
                    logger.info(f"Processing Loan {loan.name} (ID: {loan.id}) scheduled for {scheduled_date}")

                    # Calculate principal payment: Principal / Periods
                    principal_payment = loan.principal / decimal.Decimal(loan.periods)
                    
                    # Update Loan
                    loan.principal -= principal_payment
                    loan.periods -= 1
                    loan.save()
                    
                    # Create Transaction
                    Transaction.objects.create(
                        user_openId=loan.user_openId,
                        type='expense',
                        category='Loan Repayment',
                        amount=principal_payment,
                        date=scheduled_date,
                        account='Loan Account', 
                        note=note_identifier
                    )
                    logger.info(f"Processed Loan {loan.name}: Principal -{principal_payment}, Periods -1")
                    
                except Exception as e:
                    logger.error(f"Error processing loan {loan.name}: {e}")
        else:
            logger.info(f'No loans scheduled on or before day {current_day}.')

        logger.info('Processing completed.')
