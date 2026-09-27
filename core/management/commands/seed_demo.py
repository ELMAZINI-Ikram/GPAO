from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from core.models import *
from core.services import compute_abc

class Command(BaseCommand):
    help = 'Charge des données de démonstration GPAO.'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        if Article.objects.exists():
            compute_abc()
            self.stdout.write(self.style.SUCCESS('Données déjà présentes.'))
            return

        cust = Customer.objects.create(name='ElectroAtlas')
        sup = Supplier.objects.create(name='Fournitures Maroc', lead_time_days=10)

        raw1 = Article.objects.create(code='MP-CUIVRE', designation='Fil cuivre', article_type='RAW', current_stock=80, safety_stock=30, annual_demand=1200, ordering_cost=250, carrying_rate=0.18, unit_cost=12, lead_time_days=14)
        raw2 = Article.objects.create(code='MP-BOITIER', designation='Boîtier aluminium', article_type='RAW', current_stock=25, safety_stock=20, annual_demand=600, ordering_cost=180, carrying_rate=0.15, unit_cost=35, lead_time_days=10)
        comp1 = Article.objects.create(code='CP-CARTE', designation='Carte de commande', article_type='COMP', current_stock=18, safety_stock=10, annual_demand=520, ordering_cost=300, carrying_rate=0.22, unit_cost=90, lead_time_days=21)
        comp2 = Article.objects.create(code='CP-CONN', designation='Connecteur 6 broches', article_type='COMP', current_stock=60, safety_stock=25, annual_demand=1500, ordering_cost=120, carrying_rate=0.20, unit_cost=8, lead_time_days=7)
        fg = Article.objects.create(code='PF-CTRL100', designation='Boîtier de contrôle CTRL100', article_type='FG', current_stock=5, safety_stock=8, annual_demand=240, ordering_cost=500, carrying_rate=0.20, unit_cost=480, lead_time_days=14)

        m1 = Machine.objects.create(code='MC-CAB', name='Poste câblage', weekly_capacity_hours=42)
        m2 = Machine.objects.create(code='MC-ASSY', name='Poste assemblage', weekly_capacity_hours=40)
        m3 = Machine.objects.create(code='MC-TEST', name='Banc de test', weekly_capacity_hours=24)

        BOM.objects.create(parent=fg, component=raw1, quantity=4)
        BOM.objects.create(parent=fg, component=raw2, quantity=1)
        BOM.objects.create(parent=fg, component=comp1, quantity=1)
        BOM.objects.create(parent=fg, component=comp2, quantity=2, scrap_rate=0.05)

        RoutingOperation.objects.create(article=fg, sequence=10, label='Câblage', machine=m1, setup_time_hours=0.4, unit_time_hours=0.30)
        RoutingOperation.objects.create(article=fg, sequence=20, label='Assemblage', machine=m2, setup_time_hours=0.5, unit_time_hours=0.40)
        RoutingOperation.objects.create(article=fg, sequence=30, label='Test final', machine=m3, setup_time_hours=0.3, unit_time_hours=0.20)

        today = date.today()
        for i, qty in enumerate([18, 22, 26, 24, 20, 18, 12, 10]):
            MPSItem.objects.create(article=fg, week_start=today + timedelta(days=(7 * i)), quantity=qty, source='PDP')

        ScheduledReceipt.objects.create(article=raw1, due_date=today + timedelta(days=7), quantity=120, source='achat')
        ScheduledReceipt.objects.create(article=comp2, due_date=today + timedelta(days=14), quantity=200, source='achat')
        ScheduledReceipt.objects.create(article=fg, due_date=today + timedelta(days=7), quantity=12, source='OF')

        order = CustomerOrder.objects.create(number='CC-001', customer=cust, due_date=today + timedelta(days=10), status='CONFIRMED')
        CustomerOrderLine.objects.create(order=order, article=fg, quantity=15)
        order2 = CustomerOrder.objects.create(number='CC-002', customer=cust, due_date=today + timedelta(days=21), status='CONFIRMED')
        CustomerOrderLine.objects.create(order=order2, article=fg, quantity=18)

        InventoryMovement.objects.create(article=raw1, movement_type='IN', quantity=80, reference='INIT')
        InventoryMovement.objects.create(article=fg, movement_type='IN', quantity=5, reference='INIT')

        MaintenanceTicket.objects.create(machine=m3, title='Calibration préventive', description='Arrêt planifié 1 jour', status='OPEN')
        m3.status='MAINT'
        m3.save(update_fields=['status'])

        compute_abc()
        self.stdout.write(self.style.SUCCESS('Données de démonstration chargées. Admin/admin123'))
