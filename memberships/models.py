from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone

from core.models import AuditModel, Status
import random
import string

class EducationLevel(AuditModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Institution(AuditModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class MembershipType(AuditModel):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class PersonalInfo(AuditModel):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    COUNTRY_CHOICES = (
        ('MM', 'Myanmar'),
        ('SG', 'Singapore'),
        ('Others', 'Others'),
    )
    CITIZEN_CHOICES = (
        ('MM', 'Myanmar'),
        ('SG', 'Singapore'),
        ('Others', 'Others'),
    )
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    country_of_birth = models.CharField(max_length=10, choices=COUNTRY_CHOICES)
    city_of_birth = models.CharField(max_length=200, blank=True, null=True)
    citizenship = models.CharField(max_length=10, choices=CITIZEN_CHOICES)

    class Meta:
        verbose_name = "Personal Info"

    def __str__(self):
        return self.full_name

    def get_age(self):
        """Calculate age from date_of_birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class ContactInfo(AuditModel):
    RESIDENTIAL_STATUS_CHOICES = [
        ('singaporean', 'Singaporean'),
        ('permanent_resident', 'Permanent Resident'),
        ('employment_pass', 'Employment Pass Holder'),
        ('s_pass', 'S-Pass Holder'),
        ('work_permit', 'Work Permit Holder'),
        ('dependent_pass', 'Dependent Pass Holder'),
        ('long_term_visit_pass', 'Long Term Visit Pass Holder'),
        ('others', 'Others'),
    ]
    nric_fin_validator = RegexValidator(
        regex=r'^[STFG]\d{7}[A-Z]$',
        message='NRIC/FIN must start with S, T, F, or G followed by 7 digits and an alphabet.'
    )
    # pass_type_others = models.CharField(blank=True, null=True, max_length=100)
    nric_fin = models.CharField(max_length=255, validators=[nric_fin_validator])
    primary_contact = models.CharField(max_length=25, null=True)
    secondary_contact = models.CharField(max_length=25, null=True, blank=True)
    residential_status = models.CharField(max_length=255, choices=RESIDENTIAL_STATUS_CHOICES, null=True, blank=True)
    postal_code = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Info"

    def __str__(self):
        return f"{self.address} ({self.postal_code})"


class WorkInfo(AuditModel):
    occupation = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_address = models.TextField(null=True, blank=True)
    company_postal_code = models.CharField(max_length=255, null=True, blank=True)
    company_contact = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Work Info"

    def __str__(self):
        return f"{self.occupation} at {self.company_name}"


class EducationInfo(AuditModel):
    education = models.ForeignKey(EducationLevel, on_delete=models.SET_NULL, blank=True, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, blank=True, null=True)
    other_societies = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Education Info"

    def __str__(self):
        return f"{self.education} at {self.institution}"


class Membership(AuditModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    reference_no = models.CharField(
        max_length=12,
        unique=True,
        blank=True
    )
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    applied_date = models.DateField(auto_now_add=True)
    membership_type = models.ForeignKey(MembershipType, on_delete=models.SET_NULL, blank=True, null=True)
    membership_number = models.CharField(max_length=255, null=True, blank=True)

    profile_info = models.OneToOneField(PersonalInfo, on_delete=models.SET_NULL, blank=True, null=True)
    contact_info = models.OneToOneField(ContactInfo, on_delete=models.SET_NULL, blank=True, null=True)
    work_info = models.OneToOneField(WorkInfo, on_delete=models.SET_NULL, blank=True, null=True)
    education_info = models.OneToOneField(EducationInfo, on_delete=models.SET_NULL, blank=True, null=True)
    workflow_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    # draft, created, pending_payment, pending_approval, approve, reject, revise, terminated

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = self.generate_reference_no()
        super().save(*args, **kwargs)

    def generate_reference_no(self):
        """Generate a unique reference number"""
        while True:
            number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            ref_no = f"BMR-{number}"
            if not type(self).objects.filter(reference_no=ref_no).exists():
                return ref_no

    def generate_membership_number(self):
        """Generate membership number when approved"""
        if self.membership_number:
            return self.membership_number

        year = timezone.now().year
        membership_type_code = self.membership_type.type_code.upper()[:2] if self.membership_type else "OR"

        # Count existing approved memberships for this year and type
        count = Membership.objects.filter(
            membership_number__isnull=False,
            membership_number__startswith=f"{membership_type_code}{year}"
        ).count() + 1

        self.membership_number = f"{membership_type_code}{year}{count:04d}"
        return self.membership_number

    def calculate_membership_fee(self):
        """Calculate membership fee based on age and membership type"""
        if not self.membership_type or not self.profile_info:
            return Decimal('0.00')

        base_amount = self.membership_type.amount
        age = self.profile_info.get_age()

        # 50% discount for members aged 60+ or 18 and below
        if age >= 60 or age <= 18:
            return base_amount / 2

        return base_amount

    def transition(self, new_status, *, reason: str | None = None, actor=None, save_membership: bool = True):
        """
        Transition to a new Status (instance or status_code str).
        Always writes WorkflowLog with given reason/actor.
        """
        if isinstance(new_status, str):
            new_status = Status.objects.get(status_code=new_status)

        with transaction.atomic():
            old_status = self.workflow_status

            # Generate membership number when approved
            if new_status.status_code == "13":  # Approved
                self.generate_membership_number()

            self.workflow_status = new_status
            if reason is not None:
                self.reason = reason
            if save_membership:
                self.save(update_fields=["workflow_status", "reason", "modified_at", "modified_by"])

            if actor and not getattr(actor, "is_authenticated", False):
                actor = None

            WorkflowLog.objects.create(
                membership=self,
                old_status=old_status,
                new_status=new_status,
                action_by=actor,
                reason=reason,
            )
        return self

    def __str__(self):
        return f"{self.user.username} - {self.reference_no}"


class MembershipPayment(AuditModel):
    METHOD_CHOICES = (
        ("hitpay", "HitPay"),
        ("bank_transfer", "Bank Transfer"),
        ("cash", "Cash"),
    )
    STATUS_CHOICES = (
        ("created", "Created"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True, related_name='payments')
    method = models.CharField(max_length=32, choices=METHOD_CHOICES)
    provider = models.CharField(max_length=32, blank=True, null=True)  # e.g., 'hitpay' for online
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="created")

    receipt_no = models.CharField(max_length=15, unique=True, editable=False)

    # identifiers
    external_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)  # provider payment id
    reference_no = models.CharField(max_length=128, blank=True, null=True)  # bank/cash reference
    description = models.CharField(max_length=255, blank=True, null=True)

    # money
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="SGD")

    # period / due
    period_year = models.PositiveIntegerField()  # billing year (e.g., 2025)
    due_date = models.DateField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    # artifacts
    qr_code = models.TextField(blank=True, null=True)  # HitPay QR payload
    receipt_image = models.ImageField(upload_to="receipts/", blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)  # extra
    raw_response = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = self.generate_receipt_no()
        super().save(*args, **kwargs)

    def generate_receipt_no(self):
        year = timezone.now().year % 100
        prefix = f"BMR-{year:02d}-"
        year_receipts = Membership.objects.filter(
            receipt_no__startswith=prefix
        ).count() + 1
        return f"{prefix}{year_receipts:03d}"

    def __str__(self):
        return f"{self.receipt_no} - {self.membership.reference_no} - {self.amount}"


class PaymentLog(AuditModel):
    payment = models.ForeignKey(MembershipPayment, on_delete=models.CASCADE, related_name="logs")
    old_status = models.CharField(max_length=16, blank=True, null=True)
    new_status = models.CharField(max_length=16)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.payment_id} {self.old_status} -> {self.new_status}"


class WorkflowLog(AuditModel):
    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True)
    old_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True,
                                   related_name='old_workflow_logs')
    new_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True,
                                   related_name='new_workflow_logs')
    action_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    action_time = models.DateTimeField(auto_now=True)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action_by} - {self.action_time} - {self.old_status} -> {self.new_status}"