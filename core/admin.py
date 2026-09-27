from django.contrib import admin
from .models import *

for model in [Article, Supplier, Customer, Machine, BOM, RoutingOperation, MPSItem, ScheduledReceipt,
              CustomerOrder, CustomerOrderLine, ManufacturingOrder, WorkOrder, InventoryMovement,
              QualityCheck, NonConformity, Certificate, MaintenanceTicket, PreventiveMaintenance, SparePart,
              SupplierOrder, SupplierOrderLine, SupplierReceipt, SupplierReceiptLine, SupplierInvoice,
              ProductionCost, UserProfile, Holiday]:
    admin.site.register(model)
