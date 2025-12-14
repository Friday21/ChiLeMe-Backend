import json
import logging
import decimal
import datetime
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from wxcloudrun.models import Transaction, Asset, FixedItem, FutureItem, Loan, AssetCorrection

logger = logging.getLogger('log')

def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields:
        val = f.value_from_object(instance)
        if isinstance(val, decimal.Decimal):
            val = str(val)
        elif isinstance(val, (datetime.date, datetime.datetime)):
            val = val.isoformat()
        data[f.name] = val
    return data

def json_response(data, code=0, msg='success'):
    return JsonResponse({'code': code, 'errorMsg': msg, 'data': data}, json_dumps_params={'ensure_ascii': False})

def get_body(request):
    try:
        return json.loads(request.body)
    except:
        return {}

@method_decorator(csrf_exempt, name='dispatch')
class DashboardView(View):
    def get(self, request, *args, **kwargs):
        # 1. Calculate Assets
        assets = Asset.objects.all()
        cash_assets = assets.filter(type='cash')
        stock_assets = assets.filter(type='stock')
        house_assets = assets.filter(type='house')
        
        cash_total = sum(a.value for a in cash_assets)
        stock_total = sum(a.value for a in stock_assets)
        house_total = sum(a.value for a in house_assets)
        
        # 2. Calculate Liabilities (Loans)
        loans = Loan.objects.all()
        loan_total = sum(l.principal for l in loans)
        
        # 3. Net Worth
        total_assets = cash_total + stock_total + house_total
        net_worth = total_assets - loan_total
        
        # Helper to format money
        def fmt(val):
            return "{:,.0f}".format(val)
            
        # 4. Asset Items Structure
        asset_items = []
        
        # Cash Item
        asset_items.append({
            "id": 1,
            "name": '流动资金',
            "subtitle": '、'.join([a.name for a in cash_assets][:2]) if cash_assets else '暂无',
            "amount": fmt(cash_total),
            "updateDate": datetime.date.today().strftime('%m月%d日 更新'),
            "isNegative": False,
            "expanded": False,
            "children": [
                { "name": a.name, "subtitle": a.desc or '现金', "amount": fmt(a.value), "date": a.updated_at.strftime('%m月%d日') }
                for a in cash_assets
            ]
        })
        
        # Stock Item
        asset_items.append({
            "id": 2,
            "name": '投资',
            "subtitle": '股票',
            "amount": fmt(stock_total),
            "updateDate": datetime.date.today().strftime('%m月%d日 更新'),
            "isNegative": False,
            "expanded": False,
            "children": [
                { "name": a.name, "subtitle": a.stock_code or '股票', "amount": fmt(a.value), "date": a.updated_at.strftime('%m月%d日') }
                for a in stock_assets
            ]
        })
        
        # House Item
        asset_items.append({
            "id": 3,
            "name": '固定资产',
            "subtitle": '房产',
            "amount": fmt(house_total),
            "updateDate": datetime.date.today().strftime('%m月%d日 更新'),
            "isNegative": False,
            "expanded": False,
            "children": [
                { "name": a.name, "subtitle": '自住', "amount": fmt(a.value), "date": a.updated_at.strftime('%m月%d日') }
                for a in house_assets
            ]
        })
        
        # Loan Item
        asset_items.append({
            "id": 4,
            "name": '负债',
            "subtitle": '贷款',
            "amount": fmt(loan_total),
            "updateDate": datetime.date.today().strftime('%m月%d日 更新'),
            "isNegative": True,
            "expanded": False,
            "children": [
                { "name": l.name, "subtitle": '贷款', "amount": fmt(l.principal), "date": l.updated_at.strftime('%m月%d日') }
                for l in loans
            ]
        })

        # 5. Monthly Data (Current Month)
        now = datetime.datetime.now()
        transactions = Transaction.objects.filter(date__year=now.year, date__month=now.month)
        
        monthly_income = sum(t.amount for t in transactions if t.type == 'income')
        monthly_expense = sum(t.amount for t in transactions if t.type == 'expense')
        monthly_balance = monthly_income - monthly_expense
        
        income_percent = 0
        expense_percent = 0
        if monthly_income > 0:
            income_percent = 100
            expense_percent = int((monthly_expense / monthly_income) * 100)
        
        data = {
            "netWorth": fmt(net_worth),
            "netWorthChange": "0", # Placeholder
            "cashAmount": fmt(cash_total),
            "stockAmount": fmt(stock_total),
            "mortgageAmount": fmt(loan_total),
            "houseAmount": fmt(house_total),
            "assetItems": asset_items,
            "monthlyBalance": fmt(monthly_balance),
            "monthlyIncome": fmt(monthly_income),
            "monthlyExpense": fmt(monthly_expense),
            "monthlyStockProfit": "+0", # Placeholder
            "incomePercent": income_percent,
            "expensePercent": expense_percent,
            "savingsProgress": 64, # Placeholder
            "trendData": {
                "categories": ["12月", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月"],
                "series": [
                    { "name": "预测净资产", "data": [123, 125, 128, 130, 133, 135, 138, 140, 143, 145, 148, 150] }
                ]
            },
            "ringData": {
                "series": [
                    { "name": "现金", "data": float(cash_total) },
                    { "name": "股票", "data": float(stock_total) },
                    { "name": "房产", "data": float(house_total) }
                ]
            }
        }
        return json_response(data)

@method_decorator(csrf_exempt, name='dispatch')
class TransactionView(View):
    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        type_ = request.GET.get('type')
        category = request.GET.get('category')
        
        qs = Transaction.objects.all().order_by('-date')
        if month:
            qs = qs.filter(date__startswith=month)
        if type_:
            qs = qs.filter(type=type_)
        if category:
            qs = qs.filter(category=category)
            
        data = [to_dict(t) for t in qs]
        return json_response(data)

    def post(self, request, *args, **kwargs):
        body = get_body(request)
        # Remove id if present
        if 'id' in body:
            del body['id']
        t = Transaction.objects.create(**body)
        return json_response(to_dict(t))

    def put(self, request, pk, *args, **kwargs):
        body = get_body(request)
        Transaction.objects.filter(pk=pk).update(**body)
        t = Transaction.objects.get(pk=pk)
        return json_response(to_dict(t))

    def delete(self, request, pk, *args, **kwargs):
        Transaction.objects.filter(pk=pk).delete()
        return json_response({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class PlanningView(View):
    def get(self, request, *args, **kwargs):
        assets = [to_dict(a) for a in Asset.objects.all()]
        fixed = [to_dict(f) for f in FixedItem.objects.all()]
        future = [to_dict(f) for f in FutureItem.objects.all()]
        loans = [to_dict(l) for l in Loan.objects.all()]
        
        data = {
            "assets": assets,
            "fixed": fixed,
            "futureSteps": future,
            "loans": loans
        }
        return json_response(data)

@method_decorator(csrf_exempt, name='dispatch')
class AssetView(View):
    def post(self, request, *args, **kwargs):
        body = get_body(request)
        if 'id' in body: del body['id']
        obj = Asset.objects.create(**body)
        return json_response(to_dict(obj))

    def put(self, request, pk, *args, **kwargs):
        body = get_body(request)
        Asset.objects.filter(pk=pk).update(**body)
        obj = Asset.objects.get(pk=pk)
        return json_response(to_dict(obj))

    def delete(self, request, pk, *args, **kwargs):
        Asset.objects.filter(pk=pk).delete()
        return json_response({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class FixedItemView(View):
    def post(self, request, *args, **kwargs):
        body = get_body(request)
        if 'id' in body: del body['id']
        obj = FixedItem.objects.create(**body)
        return json_response(to_dict(obj))

    def put(self, request, pk, *args, **kwargs):
        body = get_body(request)
        FixedItem.objects.filter(pk=pk).update(**body)
        obj = FixedItem.objects.get(pk=pk)
        return json_response(to_dict(obj))

    def delete(self, request, pk, *args, **kwargs):
        FixedItem.objects.filter(pk=pk).delete()
        return json_response({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class FutureItemView(View):
    def post(self, request, *args, **kwargs):
        body = get_body(request)
        if 'id' in body: del body['id']
        obj = FutureItem.objects.create(**body)
        return json_response(to_dict(obj))

    def put(self, request, pk, *args, **kwargs):
        body = get_body(request)
        FutureItem.objects.filter(pk=pk).update(**body)
        obj = FutureItem.objects.get(pk=pk)
        return json_response(to_dict(obj))

    def delete(self, request, pk, *args, **kwargs):
        FutureItem.objects.filter(pk=pk).delete()
        return json_response({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class LoanView(View):
    def post(self, request, *args, **kwargs):
        body = get_body(request)
        if 'id' in body: del body['id']
        obj = Loan.objects.create(**body)
        return json_response(to_dict(obj))

    def put(self, request, pk, *args, **kwargs):
        body = get_body(request)
        Loan.objects.filter(pk=pk).update(**body)
        obj = Loan.objects.get(pk=pk)
        return json_response(to_dict(obj))

    def delete(self, request, pk, *args, **kwargs):
        Loan.objects.filter(pk=pk).delete()
        return json_response({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class ProfileView(View):
    def get(self, request, *args, **kwargs):
        # Mock profile data
        data = {
            "userInfo": {
                "name": "FridayLi",
                "days": 128,
                "avatar": "https://img.yzcdn.cn/vant/cat.jpeg"
            },
            "accounts": [
                { "name": "招商银行", "value": "¥20,000", "label": "尾号 8888" },
                { "name": "工商银行", "value": "¥32,300", "label": "尾号 1234" },
                { "name": "股票账户", "value": "¥198,500" }
            ],
            "settings": {
                "currency": "人民币 (CNY)",
                "startDate": "2025-07-01"
            }
        }
        return json_response(data)

@method_decorator(csrf_exempt, name='dispatch')
class AssetCorrectionView(View):
    def get(self, request, *args, **kwargs):
        # Get latest correction or calculate
        last = AssetCorrection.objects.last()
        data = {
            "cashSystem": 50000, # Mock
            "stockSystem": 200000 # Mock
        }
        if last:
            data['cashActual'] = str(last.cash_actual)
            data['stockActual'] = str(last.stock_actual)
            
        return json_response(data)

    def post(self, request, *args, **kwargs):
        body = get_body(request)
        obj = AssetCorrection.objects.create(**body)
        return json_response(to_dict(obj))
