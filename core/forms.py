from django import forms
from .models import CustomerOrder, CustomerOrderLine, MaintenanceTicket, SupplierOrder, SupplierOrderLine, SupplierReceipt, SupplierReceiptLine, SupplierInvoice, ManufacturingOrder, ProductionCost, QualityCheck, NonConformity, Certificate, PreventiveMaintenance, SparePart

class CustomerOrderForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = ['number', 'customer', 'due_date', 'status']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'number': 'Numéro',
            'customer': 'Client',
            'due_date': 'Date de livraison',
            'status': 'Statut'
        }

class CustomerOrderLineForm(forms.ModelForm):
    class Meta:
        model = CustomerOrderLine
        fields = ['article', 'quantity', 'unit_price', 'discount_percent']
        labels = {
            'article': 'Article',
            'quantity': 'Quantité',
            'unit_price': 'Prix unitaire',
            'discount_percent': 'Remise (%)'
        }

class MaintenanceTicketForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ['machine', 'title', 'description', 'maintenance_type', 'status', 'opened_on', 'resolved_on']
        widgets = {
            'opened_on': forms.DateInput(attrs={'type': 'date'}),
            'resolved_on': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'machine': 'Machine',
            'title': 'Titre',
            'description': 'Description',
            'maintenance_type': 'Type de maintenance',
            'status': 'Statut',
            'opened_on': 'Date d\'ouverture',
            'resolved_on': 'Date de résolution'
        }

class SupplierOrderForm(forms.ModelForm):
    class Meta:
        model = SupplierOrder
        fields = ['number', 'supplier', 'order_date', 'status']
        widgets = {'order_date': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'number': 'Numéro',
            'supplier': 'Fournisseur',
            'order_date': 'Date de commande',
            'status': 'Statut'
        }

class SupplierOrderLineForm(forms.ModelForm):
    class Meta:
        model = SupplierOrderLine
        fields = ['article', 'quantity', 'unit_price']
        labels = {
            'article': 'Article',
            'quantity': 'Quantité',
            'unit_price': 'Prix unitaire'
        }

class SupplierReceiptForm(forms.ModelForm):
    class Meta:
        model = SupplierReceipt
        fields = ['supplier_order', 'receipt_date', 'notes']
        widgets = {'receipt_date': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'supplier_order': 'Commande fournisseur',
            'receipt_date': 'Date de réception',
            'notes': 'Notes'
        }

class SupplierReceiptLineForm(forms.ModelForm):
    class Meta:
        model = SupplierReceiptLine
        fields = ['article', 'quantity_received', 'warehouse']
        labels = {
            'article': 'Article',
            'quantity_received': 'Quantité reçue',
            'warehouse': 'Magasin'
        }

class SupplierInvoiceForm(forms.ModelForm):
    class Meta:
        model = SupplierInvoice
        fields = ['supplier_order', 'invoice_number', 'amount', 'due_date', 'status']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'supplier_order': 'Commande fournisseur',
            'invoice_number': 'Numéro de facture',
            'amount': 'Montant (Dhs)',
            'due_date': 'Date d\'échéance',
            'status': 'Statut'
        }

class ManufacturingOrderCloseForm(forms.ModelForm):
    class Meta:
        model = ManufacturingOrder
        fields = ['good_qty', 'scrap_qty']
        labels = {
            'good_qty': 'Quantité bonne',
            'scrap_qty': 'Quantité rebut'
        }

class ProductionCostForm(forms.ModelForm):
    class Meta:
        model = ProductionCost
        fields = ['manufacturing_order', 'material_cost', 'labor_cost', 'machine_cost', 'selling_price']
        labels = {
            'manufacturing_order': 'Ordre de fabrication',
            'material_cost': 'Coût matière (Dhs)',
            'labor_cost': 'Coût main-d\'œuvre (Dhs)',
            'machine_cost': 'Coût machine (Dhs)',
            'selling_price': 'Prix de vente (Dhs)'
        }

class QualityCheckForm(forms.ModelForm):
    class Meta:
        model = QualityCheck
        fields = ['article', 'manufacturing_order', 'check_type', 'status', 'notes', 'blocks_mo']
        labels = {
            'article': 'Article',
            'manufacturing_order': 'Ordre de fabrication',
            'check_type': 'Type de contrôle',
            'status': 'Statut',
            'notes': 'Notes',
            'blocks_mo': 'Bloque l\'OF'
        }

class NonConformityForm(forms.ModelForm):
    class Meta:
        model = NonConformity
        fields = ['quality_check', 'description', 'corrective_action', 'resolved', 'resolved_on']
        widgets = {'resolved_on': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'quality_check': 'Contrôle qualité',
            'description': 'Description',
            'corrective_action': 'Action corrective',
            'resolved': 'Résolu',
            'resolved_on': 'Date de résolution'
        }

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['manufacturing_order', 'certificate_number', 'issue_date', 'notes']
        widgets = {'issue_date': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'manufacturing_order': 'Ordre de fabrication',
            'certificate_number': 'Numéro de certificat',
            'issue_date': 'Date d\'émission',
            'notes': 'Notes'
        }

class PreventiveMaintenanceForm(forms.ModelForm):
    class Meta:
        model = PreventiveMaintenance
        fields = ['machine', 'frequency_days', 'last_performed', 'next_due', 'description']
        widgets = {
            'last_performed': forms.DateInput(attrs={'type': 'date'}),
            'next_due': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'machine': 'Machine',
            'frequency_days': 'Fréquence (jours)',
            'last_performed': 'Dernière intervention',
            'next_due': 'Prochaine échéance',
            'description': 'Description'
        }

class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ['article', 'machine', 'quantity', 'min_quantity']
        labels = {
            'article': 'Article',
            'machine': 'Machine',
            'quantity': 'Quantité',
            'min_quantity': 'Quantité minimum'
        }
