from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CustomerOrderForm, CustomerOrderLineForm, MaintenanceTicketForm, SupplierOrderForm, SupplierOrderLineForm, SupplierReceiptForm, SupplierReceiptLineForm, SupplierInvoiceForm, ManufacturingOrderCloseForm, ProductionCostForm, QualityCheckForm, NonConformityForm, CertificateForm, PreventiveMaintenanceForm, SparePartForm
from .models import Article, CustomerOrder, ManufacturingOrder, WorkOrder, MaintenanceTicket, Machine, InventoryMovement, RoutingOperation, SupplierOrder, SupplierOrderLine, SupplierReceipt, SupplierReceiptLine, SupplierInvoice, ProductionCost, QualityCheck, NonConformity, Certificate, PreventiveMaintenance, SparePart, UserProfile, Holiday
from .services import compute_mrp, capacity_report, shortage_report, generate_mo_from_confirmed_orders, compute_abc

def get_user_role(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role
    except UserProfile.DoesNotExist:
        return 'OPERATOR'

def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            user_role = get_user_role(request.user)
            if user_role in allowed_roles or user_role == 'ADMIN':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Accès non autorisé pour votre rôle.')
                return redirect('dashboard')
        return wrapped_view
    return decorator

@login_required(login_url='/accounts/login/')
def dashboard(request):
    try:
        compute_abc()
    except:
        pass
    try:
        shortage = shortage_report()
    except:
        shortage = []
    from datetime import date, timedelta
    from django.db.models import Sum, F
    from django.utils import timezone
    
    today = date.today()
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Chiffre d'affaires du mois (total des commandes confirmées)
    try:
        monthly_revenue = CustomerOrder.objects.filter(
            status='CONFIRMED',
            due_date__gte=month_start,
            due_date__lte=today
        ).aggregate(total=Sum(F('lines__quantity') * F('lines__unit_price') * (1 - F('lines__discount_percent') / 100)))['total'] or 0
    except:
        monthly_revenue = 0
    
    # Taux de service (livraisons à temps - OF terminés avant ou à la date due)
    try:
        on_time_mo = ManufacturingOrder.objects.filter(
            status='DONE',
            due_date__gte=month_start
        ).count()
        total_completed_mo = ManufacturingOrder.objects.filter(
            status='DONE',
            due_date__gte=month_start
        ).count()
        service_rate = (on_time_mo / total_completed_mo * 100) if total_completed_mo > 0 else 0
    except:
        service_rate = 0
    
    # OF en retard
    try:
        late_mo = ManufacturingOrder.objects.filter(
            status__in=['PLANNED', 'RELEASED', 'IN_PROGRESS'],
            due_date__lt=today
        ).count()
    except:
        late_mo = 0
    
    # Stock total valorisé
    try:
        total_stock_value = Article.objects.aggregate(
            total=Sum(F('current_stock') * F('unit_cost'))
        )['total'] or 0
    except:
        total_stock_value = 0
    
    # Machines en panne
    try:
        machines_down = Machine.objects.filter(status='DOWN').count()
    except:
        machines_down = 0
    
    # Taux de rebut du mois
    try:
        total_produced = ManufacturingOrder.objects.filter(
            status='DONE',
            due_date__gte=month_start
        ).aggregate(total=Sum('good_qty'))['total'] or 0
        total_scrap = ManufacturingOrder.objects.filter(
            status='DONE',
            due_date__gte=month_start
        ).aggregate(total=Sum('scrap_qty'))['total'] or 0
        scrap_rate = (total_scrap / (total_produced + total_scrap) * 100) if (total_produced + total_scrap) > 0 else 0
    except:
        scrap_rate = 0
    
    # Commandes à livrer cette semaine
    try:
        orders_this_week = CustomerOrder.objects.filter(
            status='CONFIRMED',
            due_date__gte=week_start,
            due_date__lte=week_end
        ).count()
    except:
        orders_this_week = 0
    
    context = {
        'article_count': Article.objects.count(),
        'machine_down': machines_down,
        'open_maintenance': MaintenanceTicket.objects.exclude(status='RESOLVED').count(),
        'open_mo': ManufacturingOrder.objects.exclude(status='DONE').count(),
        'shortage': shortage[:10] if shortage else [],
        'monthly_revenue': monthly_revenue,
        'service_rate': round(service_rate, 1),
        'late_mo': late_mo,
        'total_stock_value': total_stock_value,
        'scrap_rate': round(scrap_rate, 1),
        'orders_this_week': orders_this_week,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def article_list(request):
    try:
        compute_abc()
    except:
        pass
    articles = Article.objects.all().order_by('code')
    return render(request, 'core/article_list.html', {'articles': articles})

@login_required
def mrp_view(request):
    try:
        compute_abc()
    except:
        pass
    try:
        mrp, buckets = compute_mrp()
    except:
        mrp, buckets = {}, []
    return render(request, 'core/mrp.html', {'mrp': mrp, 'buckets': buckets})

@login_required
def capacity_view(request):
    try:
        report, buckets = capacity_report()
    except:
        report, buckets = [], []
    return render(request, 'core/capacity.html', {'report': report, 'buckets': buckets})

@login_required
def offset_graph_view(request):
    try:
        mrp, buckets = compute_mrp()
    except:
        mrp, buckets = {}, []
    rows = []
    for article, records in mrp.items():
        launches = [r for r in records if r.planned_release > 0]
        receipts = [r for r in records if r.planned_receipt > 0]
        rows.append({'article': article, 'launches': launches, 'receipts': receipts})
    return render(request, 'core/decalages.html', {'rows': rows, 'buckets': buckets})

@login_required
def order_list(request):
    orders = CustomerOrder.objects.select_related('customer').prefetch_related('lines__article').order_by('-due_date')
    return render(request, 'core/orders.html', {'orders': orders})

@login_required
def order_create(request):
    if request.method == 'POST':
        form = CustomerOrderForm(request.POST)
        line_form = CustomerOrderLineForm(request.POST)
        if form.is_valid() and line_form.is_valid():
            order = form.save()
            line = line_form.save(commit=False)
            line.order = order
            line.save()
            messages.success(request, 'Commande créée.')
            return redirect('order_list')
    else:
        form = CustomerOrderForm()
        line_form = CustomerOrderLineForm()
    return render(request, 'core/order_form.html', {'form': form, 'line_form': line_form})

@login_required
def order_confirm(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    order.status = 'CONFIRMED'
    order.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Commande confirmée.')
    return redirect('order_list')

@login_required
def generate_of(request):
    try:
        count = generate_mo_from_confirmed_orders()
        messages.success(request, f'{count} ordre(s) de fabrication généré(s).')
    except Exception as e:
        messages.warning(request, f'Erreur lors de la génération des OF: {str(e)}')
    return redirect('mo_list')

@login_required
@role_required('OPERATOR', 'ADMIN')
def mo_list(request):
    mos = ManufacturingOrder.objects.select_related('article').prefetch_related('work_orders__operation', 'work_orders__machine').order_by('due_date')
    return render(request, 'core/mo_list.html', {'mos': mos})

@login_required
@role_required('OPERATOR', 'ADMIN')
def workorder_status(request, pk, status):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if status in {'PLANNED','IN_PROGRESS','PAUSED','DONE'}:
        wo.status = status
        wo.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Ordre de travail mis à jour: {status}.')
    return redirect('mo_list')

@login_required
def maintenance_list(request):
    tickets = MaintenanceTicket.objects.select_related('machine').order_by('-created_at')
    return render(request, 'core/maintenance_list.html', {'tickets': tickets})

@login_required
def machine_status(request):
    from django.db.models import Count, Q
    
    machines = Machine.objects.annotate(
        active_orders=Count('work_orders', filter=Q(work_orders__status='IN_PROGRESS'))
    )
    
    available_machines = machines.filter(status='AVAILABLE').count()
    busy_machines = machines.filter(status='BUSY').count()
    down_machines = machines.filter(status='DOWN').count()
    total_machines = machines.count()
    
    context = {
        'machines': machines,
        'available_machines': available_machines,
        'busy_machines': busy_machines,
        'down_machines': down_machines,
        'total_machines': total_machines,
    }
    return render(request, 'core/machine_status.html', context)

@login_required
def production_planning(request):
    from datetime import date, timedelta
    from django.db.models import Count, Sum, Q
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get manufacturing orders for the week
    mos_week = ManufacturingOrder.objects.filter(
        due_date__range=[week_start, week_end]
    ).select_related('article').prefetch_related('work_orders')
    
    # Get machine capacity
    machines = Machine.objects.annotate(
        active_orders=Count('work_orders', filter=Q(work_orders__status='IN_PROGRESS'))
    )
    
    # Get production statistics
    total_mos = ManufacturingOrder.objects.count()
    completed_mos = ManufacturingOrder.objects.filter(status='DONE').count()
    in_progress_mos = ManufacturingOrder.objects.filter(status='IN_PROGRESS').count()
    
    context = {
        'mos_week': mos_week,
        'machines': machines,
        'week_start': week_start,
        'week_end': week_end,
        'total_mos': total_mos,
        'completed_mos': completed_mos,
        'in_progress_mos': in_progress_mos,
    }
    return render(request, 'core/production_planning.html', context)

@login_required
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.save()
            if ticket.machine:
                if ticket.status == 'RESOLVED':
                    ticket.machine.status = 'AVAILABLE'
                else:
                    ticket.machine.status = 'DOWN'
                ticket.machine.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Ticket maintenance enregistré.')
            return redirect('maintenance_list')
    else:
        form = MaintenanceTicketForm()
    return render(request, 'core/maintenance_form.html', {'form': form})

@login_required
@role_required('BUYER', 'ADMIN')
def supplier_order_list(request):
    orders = SupplierOrder.objects.select_related('supplier').prefetch_related('lines__article').order_by('-order_date')
    return render(request, 'core/supplier_orders.html', {'orders': orders})

@login_required
@role_required('BUYER', 'ADMIN')
def supplier_order_create(request):
    if request.method == 'POST':
        form = SupplierOrderForm(request.POST)
        line_form = SupplierOrderLineForm(request.POST)
        if form.is_valid() and line_form.is_valid():
            order = form.save()
            line = line_form.save(commit=False)
            line.order = order
            line.save()
            messages.success(request, 'Commande fournisseur créée.')
            return redirect('supplier_order_list')
    else:
        form = SupplierOrderForm()
        line_form = SupplierOrderLineForm()
    return render(request, 'core/supplier_order_form.html', {'form': form, 'line_form': line_form})

@login_required
@role_required('STOREKEEPER', 'ADMIN')
def supplier_receipt_list(request):
    receipts = SupplierReceipt.objects.select_related('supplier_order__supplier').prefetch_related('lines__article').order_by('-receipt_date')
    return render(request, 'core/supplier_receipts.html', {'receipts': receipts})

@login_required
@role_required('STOREKEEPER', 'ADMIN')
def supplier_receipt_create(request):
    if request.method == 'POST':
        form = SupplierReceiptForm(request.POST)
        line_form = SupplierReceiptLineForm(request.POST)
        if form.is_valid() and line_form.is_valid():
            receipt = form.save()
            line = line_form.save(commit=False)
            line.receipt = receipt
            line.save()
            article = line.article
            article.current_stock += line.quantity_received
            article.save(update_fields=['current_stock', 'updated_at'])
            InventoryMovement.objects.create(
                article=article,
                movement_type='IN',
                quantity=line.quantity_received,
                reference=f'Réception {receipt.id}',
            )
            messages.success(request, 'Réception enregistrée et stock mis à jour.')
            return redirect('supplier_receipt_list')
    else:
        form = SupplierReceiptForm()
        line_form = SupplierReceiptLineForm()
    return render(request, 'core/supplier_receipt_form.html', {'form': form, 'line_form': line_form})

@login_required
@role_required('BUYER', 'ADMIN')
def supplier_invoice_list(request):
    invoices = SupplierInvoice.objects.select_related('supplier_order__supplier').order_by('-due_date')
    return render(request, 'core/supplier_invoices.html', {'invoices': invoices})

@login_required
@role_required('BUYER', 'ADMIN')
def supplier_invoice_create(request):
    if request.method == 'POST':
        form = SupplierInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facture fournisseur enregistrée.')
            return redirect('supplier_invoice_list')
    else:
        form = SupplierInvoiceForm()
    return render(request, 'core/supplier_invoice_form.html', {'form': form})

@login_required
@role_required('OPERATOR', 'ADMIN')
def mo_close(request, pk):
    mo = get_object_or_404(ManufacturingOrder, pk=pk)
    if request.method == 'POST':
        form = ManufacturingOrderCloseForm(request.POST, instance=mo)
        if form.is_valid():
            mo = form.save(commit=False)
            mo.status = 'DONE'
            mo.save()
            mo.article.current_stock += mo.good_qty
            mo.article.save(update_fields=['current_stock', 'updated_at'])
            InventoryMovement.objects.create(
                article=mo.article,
                movement_type='IN',
                quantity=mo.good_qty,
                reference=f'OF {mo.number}',
            )
            messages.success(request, f'OF {mo.number} clôturé. Stock mis à jour.')
            return redirect('mo_list')
    else:
        form = ManufacturingOrderCloseForm(instance=mo)
    return render(request, 'core/mo_close.html', {'form': form, 'mo': mo})

@login_required
@role_required('ADMIN')
def production_cost_list(request):
    costs = ProductionCost.objects.select_related('manufacturing_order__article').order_by('-created_at')
    return render(request, 'core/production_costs.html', {'costs': costs})

@login_required
@role_required('ADMIN')
def production_cost_create(request):
    if request.method == 'POST':
        form = ProductionCostForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coût de production enregistré.')
            return redirect('production_cost_list')
    else:
        form = ProductionCostForm()
    return render(request, 'core/production_cost_form.html', {'form': form})

@login_required
@role_required('ADMIN')
def quality_check_list(request):
    checks = QualityCheck.objects.select_related('article', 'manufacturing_order').order_by('-created_at')
    return render(request, 'core/quality_checks.html', {'checks': checks})

@login_required
@role_required('ADMIN')
def quality_check_create(request):
    if request.method == 'POST':
        form = QualityCheckForm(request.POST)
        if form.is_valid():
            check = form.save()
            if check.blocks_mo and check.manufacturing_order:
                check.manufacturing_order.status = 'PLANNED'
                check.manufacturing_order.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Contrôle qualité enregistré.')
            return redirect('quality_check_list')
    else:
        form = QualityCheckForm()
    return render(request, 'core/quality_check_form.html', {'form': form})

@login_required
@role_required('ADMIN')
def non_conformity_list(request):
    nc = NonConformity.objects.select_related('quality_check__article').order_by('-created_at')
    return render(request, 'core/non_conformities.html', {'non_conformities': nc})

@login_required
@role_required('ADMIN')
def non_conformity_create(request):
    if request.method == 'POST':
        form = NonConformityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Non-conformité enregistrée.')
            return redirect('non_conformity_list')
    else:
        form = NonConformityForm()
    return render(request, 'core/non_conformity_form.html', {'form': form})

@login_required
@role_required('ADMIN')
def certificate_list(request):
    certs = Certificate.objects.select_related('manufacturing_order__article').order_by('-issue_date')
    return render(request, 'core/certificates.html', {'certificates': certs})

@login_required
@role_required('ADMIN')
def certificate_create(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificat de conformité créé.')
            return redirect('certificate_list')
    else:
        form = CertificateForm()
    return render(request, 'core/certificate_form.html', {'form': form})

@login_required
@role_required('ADMIN')
def preventive_maintenance_list(request):
    pm = PreventiveMaintenance.objects.select_related('machine').order_by('next_due')
    return render(request, 'core/preventive_maintenance.html', {'preventive_maintenance': pm})

@login_required
@role_required('ADMIN')
def preventive_maintenance_create(request):
    if request.method == 'POST':
        form = PreventiveMaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance préventive planifiée.')
            return redirect('preventive_maintenance_list')
    else:
        form = PreventiveMaintenanceForm()
    return render(request, 'core/preventive_maintenance_form.html', {'form': form})

@login_required
@role_required('ADMIN')
def spare_part_list(request):
    parts = SparePart.objects.select_related('article', 'machine').order_by('article__code')
    return render(request, 'core/spare_parts.html', {'spare_parts': parts})

@login_required
@role_required('ADMIN')
def spare_part_create(request):
    if request.method == 'POST':
        form = SparePartForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pièce de rechange enregistrée.')
            return redirect('spare_part_list')
    else:
        form = SparePartForm()
    return render(request, 'core/spare_part_form.html', {'form': form})

@login_required
def holiday_list(request):
    holidays = Holiday.objects.all().order_by('date')
    return render(request, 'core/holidays.html', {'holidays': holidays})

@login_required
def gantt_chart(request):
    mos = ManufacturingOrder.objects.filter(status__in=['PLANNED', 'RELEASED', 'IN_PROGRESS']).select_related('article').order_by('planned_start')
    return render(request, 'core/gantt.html', {'mos': mos})
