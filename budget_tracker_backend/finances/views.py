from rest_framework import viewsets
from .models import Category, Transaction, Budget
from .serializers import CategorySerializer, TransactionSerializer, BudgetSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .models import Transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime
from calendar import monthrange

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_report(request):
    user = request.user
    month_param = request.query_params.get('month')  

    if not month_param:
        return Response({"error": "month query param is required. Format: YYYY-MM"}, status=400)

    try:
        month_start = datetime.strptime(month_param, '%Y-%m').date()
    except ValueError:
        return Response({"error": "Invalid month format. Use YYYY-MM."}, status=400)

    last_day = monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=last_day)

    # Transactions in this month
    expenses = Transaction.objects.filter(
        user=user,
        category__type='expense',
        date__range=(month_start, month_end)
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Get budget for that month
    budget = Budget.objects.filter(user=user, month=month_start).first()

    return Response({
        "month": month_param,
        "budget": budget.monthly_budget if budget else 0,
        "actual_expenses": expenses,
        "status": "under" if budget and expenses < budget.monthly_budget else "over" if budget else "no budget set"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_summary(request):
    user = request.user
    income = Transaction.objects.filter(user=user, category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = income - expenses

    return Response({
        'total_income': income,
        'total_expenses': expenses,
        'balance': balance
    })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['amount', 'date']


    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        return queryset
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
