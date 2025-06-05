from django.db import models
from django.contrib.auth.models import User
import datetime

class Category(models.Model):
    CATEGORY_TYPE = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=CATEGORY_TYPE)

    def __str__(self):
        return f"{self.name} ({self.type})"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount}"
    


def default_month():
    return datetime.date(2025, 5, 1)

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField(default=default_month)
    class Meta:
        unique_together = ['user', 'month']  

    def __str__(self):
        return f"{self.user.username} - {self.month} - {self.monthly_budget}"
    
    
