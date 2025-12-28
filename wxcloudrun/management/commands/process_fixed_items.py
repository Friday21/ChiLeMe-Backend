import datetime
import logging
import decimal
from django.core.management.base import BaseCommand
from wxcloudrun.models import FixedItem, Transaction, Asset, Loan

logger = logging.getLogger('log')

class Command(BaseCommand):
    help = 'Process fixed income and expenses'

    def handle(self, *args, **options):
        logger.info('Starting fixed items processing...')
        
        today = datetime.date.today()
        day_of_month = today.day
        
        # 1. Process Fixed Items
        fixed_items = FixedItem.objects.filter(date_value=day_of_month)
        
        if fixed_items.exists():
            for item in fixed_items:
                logger.info(f"Processing FixedItem {item.name} (ID: {item.id}) for user {item.user_openId}")
                
                # Check for duplicate transaction
                note_identifier = f"Fixed Item: {item.name}"
                
                exists = Transaction.objects.filter(
                    user_openId=item.user_openId,
                    date=today,
                    note=note_identifier,
                    amount=item.amount,
                    type=item.type,
                    account=item.account
                ).exists()
                
                if exists:
                    logger.info(f"Transaction for {item.name} already exists for today. Skipping.")
                    continue
                
                try:
                    transaction = Transaction.objects.create(
                        user_openId=item.user_openId,
                        type=item.type,
                        category='Fixed Item', 
                        amount=item.amount,
                        date=today,
                        account=item.account,
                        note=note_identifier
                    )
                    logger.info(f"Created Transaction {transaction.id}")
                    
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
            logger.info(f'No fixed items scheduled for day {day_of_month}.')

        # 2. Process Loans
        logger.info('Starting loan processing...')
        loans = Loan.objects.filter(repayment_date=day_of_month)
        
        if loans.exists():
            for loan in loans:
                if loan.periods <= 0:
                    continue

                logger.info(f"Processing Loan {loan.name} (ID: {loan.id}) for user {loan.user_openId}")
                note_identifier = f"Loan Repayment: {loan.name}"
                
                # Check for duplicate
                exists = Transaction.objects.filter(
                    user_openId=loan.user_openId,
                    date=today,
                    note=note_identifier
                ).exists()
                
                if exists:
                    logger.info(f"Loan repayment for {loan.name} already processed for today. Skipping.")
                    continue
                
                try:
                    # Calculate principal payment: Principal / Periods
                    # Ensure we use Decimal for precision
                    principal_payment = loan.principal / decimal.Decimal(loan.periods)
                    
                    # Update Loan
                    loan.principal -= principal_payment
                    loan.periods -= 1
                    loan.save()
                    
                    # Create Transaction (for record and dedup)
                    Transaction.objects.create(
                        user_openId=loan.user_openId,
                        type='expense',
                        category='Loan Repayment',
                        amount=principal_payment,
                        date=today,
                        account='Loan Account', # Placeholder as Loan doesn't have linked account
                        note=note_identifier
                    )
                    logger.info(f"Processed Loan {loan.name}: Principal -{principal_payment}, Periods -1")
                    
                except Exception as e:
                    logger.error(f"Error processing loan {loan.name}: {e}")
        else:
            logger.info(f'No loans scheduled for repayment on day {day_of_month}.')

        logger.info('Processing completed.')
