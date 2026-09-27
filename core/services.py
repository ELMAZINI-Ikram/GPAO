from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil
from django.db.models import Sum
from .models import Article, BOM, CustomerOrderLine, MPSItem, ScheduledReceipt, RoutingOperation, Machine, ManufacturingOrder

@dataclass
class BucketResult:
    week_start: date
    gross_requirement: float = 0
    scheduled_receipt: float = 0
    projected_available: float = 0
    net_requirement: float = 0
    planned_receipt: float = 0
    planned_release: float = 0


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def add_weeks(d: date, n: int) -> date:
    return d + timedelta(days=7 * n)


def compute_abc():
    articles = list(Article.objects.filter(active=True))
    values = []
    for a in articles:
        value = (a.annual_demand or 0) * (a.unit_cost or 0)
        values.append((a, value))
    total = sum(v for _, v in values) or 1
    values.sort(key=lambda x: x[1], reverse=True)
    cum = 0
    for art, val in values:
        cum += val / total
        art.abc_class = 'A' if cum <= 0.8 else ('B' if cum <= 0.95 else 'C')
        art.reorder_point = art.suggested_reorder_point
        art.save(update_fields=['abc_class', 'reorder_point', 'updated_at'])


def explode_bom(parent: Article, quantity: float, bucket: date, gross: dict):
    gross[parent.id][bucket] += quantity
    for line in BOM.objects.filter(parent=parent).select_related('component'):
        factor = quantity * line.quantity * (1 + (line.scrap_rate or 0))
        explode_bom(line.component, factor, bucket, gross)


def build_gross_requirements(start: date, horizon_weeks: int = 8):
    buckets = [add_weeks(start, i) for i in range(horizon_weeks)]
    gross = defaultdict(lambda: defaultdict(float))

    order_lines = CustomerOrderLine.objects.filter(order__status='CONFIRMED', order__due_date__gte=start, order__due_date__lt=add_weeks(start, horizon_weeks))        .select_related('article', 'order')
    for line in order_lines:
        bucket = monday_of(line.order.due_date)
        explode_bom(line.article, line.quantity, bucket, gross)

    mps_items = MPSItem.objects.filter(week_start__gte=start, week_start__lt=add_weeks(start, horizon_weeks)).select_related('article')
    for item in mps_items:
        explode_bom(item.article, item.quantity, monday_of(item.week_start), gross)
    return gross, buckets


def compute_mrp(horizon_weeks: int = 8):
    start = monday_of(date.today())
    gross_map, buckets = build_gross_requirements(start, horizon_weeks)
    receipts_map = defaultdict(lambda: defaultdict(float))
    for r in ScheduledReceipt.objects.filter(due_date__gte=start, due_date__lt=add_weeks(start, horizon_weeks)):
        receipts_map[r.article_id][monday_of(r.due_date)] += r.quantity

    results = {}
    for article in Article.objects.filter(active=True).order_by('code'):
        lot_size = article.eoq or 1
        stock = article.current_stock
        records = []
        releases_map = defaultdict(float)
        safety = article.safety_stock or 0
        lead_weeks = ceil((article.lead_time_days or 0) / 7) if article.lead_time_days else 0
        for bucket in buckets:
            gross = round(gross_map[article.id].get(bucket, 0), 2)
            sched = round(receipts_map[article.id].get(bucket, 0), 2)
            available_before = stock + sched
            net = max(0, gross + safety - available_before)
            planned_receipt = 0
            if net > 0:
                mult = max(1, ceil(net / lot_size)) if lot_size else 1
                planned_receipt = round(mult * lot_size, 2)
            projected = round(available_before + planned_receipt - gross, 2)
            release_bucket = add_weeks(bucket, -lead_weeks)
            if planned_receipt > 0:
                releases_map[release_bucket] += planned_receipt
            rec = BucketResult(
                week_start=bucket,
                gross_requirement=gross,
                scheduled_receipt=sched,
                projected_available=projected,
                net_requirement=round(net, 2),
                planned_receipt=planned_receipt,
                planned_release=0,
            )
            records.append(rec)
            stock = projected
        for rec in records:
            rec.planned_release = round(releases_map.get(rec.week_start, 0), 2)
        results[article] = records
    return results, buckets


def capacity_report(horizon_weeks: int = 8):
    start = monday_of(date.today())
    mrp, buckets = compute_mrp(horizon_weeks)
    report = []
    ops_by_article = defaultdict(list)
    for op in RoutingOperation.objects.select_related('machine', 'article'):
        ops_by_article[op.article_id].append(op)

    loads = defaultdict(lambda: defaultdict(float))
    for article, records in mrp.items():
        ops = ops_by_article.get(article.id, [])
        for rec in records:
            qty = rec.planned_release
            if qty <= 0:
                continue
            for op in ops:
                if op.machine_id:
                    loads[op.machine_id][rec.week_start] += op.setup_time_hours + (op.unit_time_hours * qty)

    for machine in Machine.objects.all().order_by('code'):
        row = {'machine': machine, 'weeks': []}
        cap = 0 if machine.status != 'AVAILABLE' else machine.weekly_capacity_hours
        for bucket in buckets:
            load = round(loads[machine.id].get(bucket, 0), 2)
            utilization = round((load / cap * 100), 1) if cap else (100.0 if load else 0)
            row['weeks'].append({'week': bucket, 'load': load, 'capacity': cap, 'utilization': utilization, 'overload': load > cap if cap else load > 0})
        report.append(row)
    return report, buckets


def shortage_report(horizon_weeks: int = 8):
    mrp, _ = compute_mrp(horizon_weeks)
    rows = []
    for article, records in mrp.items():
        total_net = sum(r.net_requirement for r in records)
        first_launch = next((r.week_start for r in records if r.planned_release > 0), None)
        if total_net > 0:
            rows.append({'article': article, 'net_total': round(total_net, 2), 'first_launch': first_launch})
    return rows


def generate_mo_from_confirmed_orders():
    created = 0
    for line in CustomerOrderLine.objects.filter(order__status='CONFIRMED').select_related('article', 'order'):
        number = f"OF-{line.order.number}-{line.article.code}"
        if ManufacturingOrder.objects.filter(number=number).exists():
            continue
        lead = line.article.lead_time_days or 0
        planned_start = line.order.due_date - timedelta(days=lead)
        mo = ManufacturingOrder.objects.create(number=number, article=line.article, quantity=line.quantity, due_date=line.order.due_date, planned_start=planned_start)
        for op in RoutingOperation.objects.filter(article=line.article).order_by('sequence'):
            mo.work_orders.create(operation=op, machine=op.machine)
        created += 1
    return created
