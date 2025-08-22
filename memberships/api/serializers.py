from datetime import date
from decimal import Decimal

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from memberships.models import (
    Status, EducationLevel, Institution, MembershipType,
    PersonalInfo, ContactInfo, WorkInfo, EducationInfo, Membership, MembershipPayment
)
from memberships.services.payments import create_hitpay_payment, PaymentCreateError

User = get_user_model()

class EducationLevelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ("uuid", "name", "description")

class InstitutionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ("uuid", "name", "description")

class MembershipTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = ("uuid", "name", "amount", "description")

class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = ("uuid", "full_name", "date_of_birth", "gender",
                  "country_of_birth", "city_of_birth", "citizenship")

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ("uuid", "nric_fin", "primary_contact", "secondary_contact",
                  "residential_status", "postal_code", "address")

class WorkInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkInfo
        fields = ("uuid", "occupation", "company_name", "company_address",
                  "company_postal_code", "company_contact")

class EducationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationInfo
        fields = ("uuid", "education", "institution", "other_societies")

class MembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = ("uuid", "name", "amount", "description")

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ("uuid", "internal_status", "external_status", "description",
                  "parent", "parent_code", "status_code")

class MembershipReadSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    membership_type = MembershipTypeSerializer()
    profile_info = PersonalInfoSerializer()
    contact_info = ContactInfoSerializer()
    education_info = EducationInfoSerializer(allow_null=True)
    work_info = WorkInfoSerializer(allow_null=True)
    workflow_status = StatusSerializer()

    class Meta:
        model = Membership
        fields = (
            "uuid", "reference_no", "user", "profile_picture", "applied_date",
            "membership_type", "membership_number",
            "profile_info", "contact_info", "education_info", "work_info",
            "workflow_status",
        )

# ---------- INIT (step 1) ----------

class PersonalInfoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = ("full_name", "date_of_birth", "gender",
                  "country_of_birth", "city_of_birth", "citizenship")

_nric_validator = RegexValidator(
    regex=r'^[STFG]\d{7}[A-Z]$',
    message='NRIC/FIN must start with S, T, F, or G followed by 7 digits and an alphabet.'
)

class ContactInfoCreateSerializer(serializers.ModelSerializer):
    nric_fin = serializers.CharField(validators=[_nric_validator])

    class Meta:
        model = ContactInfo
        fields = ("nric_fin", "primary_contact", "secondary_contact",
                  "residential_status", "postal_code", "address")

class MembershipInitRequestSerializer(serializers.Serializer):
    membership_uuid = serializers.UUIDField(required=False)
    profile_info = PersonalInfoCreateSerializer()
    contact_info = ContactInfoCreateSerializer()
    membership_type = serializers.PrimaryKeyRelatedField(queryset=MembershipType.objects.all())
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    def create(self, validated_data):
        user = self.context["request"].user
        pi_data = validated_data.pop("profile_info")
        ci_data = validated_data.pop("contact_info")
        profile_info = PersonalInfo.objects.create(**pi_data)
        contact_info = ContactInfo.objects.create(**ci_data)

        # Ensure draft status exists (status_code "12")
        draft_status, _ = Status.objects.get_or_create(
            status_code="10",
            defaults={"internal_status": "draft", "external_status": "Draft"}
        )

        membership = Membership.objects.create(
            user=user,
            profile_info=profile_info,
            contact_info=contact_info,
            membership_type=validated_data["membership_type"],
            profile_picture=validated_data.get("profile_picture"),
            workflow_status=draft_status,
        )
        return membership

# ---------- COMPLETE (step 2) ----------

class WorkInfoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkInfo
        fields = ("occupation", "company_name", "company_address",
                  "company_postal_code", "company_contact")

class EducationInfoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationInfo
        fields = ("education", "institution", "other_societies")


class MembershipCompleteRequestSerializer(serializers.Serializer):
    work_info = WorkInfoCreateSerializer()
    education_info = EducationInfoCreateSerializer()
    # allow passing amount/currency for the payment we create
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(required=False, default="SGD")

    def validate(self, attrs):
        membership: Membership = self.context["membership"]
        code = membership.workflow_status.status_code if membership.workflow_status else None
        if code not in ["10", "11"]:
            raise serializers.ValidationError("Only draft memberships (status_code=10 or 11) can be updated.")
        if "amount" not in attrs or attrs["amount"] is None:
            if membership.membership_type and membership.membership_type.amount is not None:
                attrs["amount"] = Decimal(membership.membership_type.amount)
            else:
                attrs["amount"] = Decimal("30.00")  # fallback if you want
        if "currency" not in attrs or not attrs["currency"]:
            attrs["currency"] = "SGD"
        return attrs

    def save(self, **kwargs):
        # Set to Pending Payment (11) and create/update work/education
        pending_payment_status, _ = Status.objects.get_or_create(
            status_code="11",
            defaults={"internal_status": "Pending Payment", "external_status": "Pending Payment"}
        )
        membership: Membership = self.context["membership"]
        wi_data = self.validated_data["work_info"]
        ei_data = self.validated_data["education_info"]
        amount = self.validated_data["amount"]
        currency = self.validated_data["currency"]

        if membership.work_info:
            for f, v in wi_data.items(): setattr(membership.work_info, f, v)
            membership.work_info.save()
        else:
            membership.work_info = WorkInfo.objects.create(**wi_data)

        if membership.education_info:
            for f, v in ei_data.items(): setattr(membership.education_info, f, v)
            membership.education_info.save()
        else:
            membership.education_info = EducationInfo.objects.create(**ei_data)

        membership.workflow_status = pending_payment_status
        membership.save()

        # Create an online payment intent for the current year
        payment_ser = CreateOnlinePaymentSerializer(
            data={"amount": amount, "currency": currency},
            context={"membership": membership}
        )
        payment_ser.is_valid(raise_exception=True)
        payment = payment_ser.save()
        self.context["payment"] = payment

        return membership


class PaymentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPayment
        fields = ("uuid","method","provider","status","external_id","reference_no","description",
                  "amount","currency","period_year","due_date","paid_at","qr_code")

class CreateOnlinePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(required=False, default="SGD")
    period_year = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        membership: Membership = self.context["membership"]
        if "amount" not in attrs or attrs["amount"] is None:
            if membership.membership_type and membership.membership_type.amount is not None:
                attrs["amount"] = Decimal(membership.membership_type.amount)
            else:
                raise serializers.ValidationError("Amount is required when membership has no membership_type amount.")
        if "period_year" not in attrs or not attrs["period_year"]:
            attrs["period_year"] = date.today().year
        return attrs

    def save(self):
        membership: Membership = self.context["membership"]
        amount = self.validated_data["amount"]
        currency = self.validated_data.get("currency", "SGD")
        description = self.validated_data.get("description", "Membership payment")
        period_year = self.validated_data["period_year"]

        try:
            data = create_hitpay_payment(str(amount), currency)
        except PaymentCreateError as e:
            raise serializers.ValidationError(str(e))

        external_id = data.get("id")
        qr_code = (data.get("qr_code_data") or {}).get("qr_code")

        payment = MembershipPayment.objects.create(
            membership=membership,
            method="hitpay",
            provider="hitpay",
            status="created",
            external_id=external_id,
            description=description,
            amount=amount,
            currency=currency.upper(),
            period_year=period_year,
            qr_code=qr_code,
            raw_response=data,
        )
        return payment

class CreateOfflinePaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[("bank_transfer","bank_transfer"), ("cash","cash")])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(required=False, default="SGD")
    period_year = serializers.IntegerField(required=False)
    reference_no = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    receipt_image = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        if "period_year" not in attrs or not attrs["period_year"]:
            attrs["period_year"] = date.today().year
        return attrs

    def save(self):
        membership: Membership = self.context["membership"]
        p = MembershipPayment.objects.create(
            membership=membership,
            method=self.validated_data["method"],
            provider=None,
            status="pending",  # pending staff confirmation
            amount=self.validated_data["amount"],
            currency=self.validated_data.get("currency","SGD").upper(),
            period_year=self.validated_data["period_year"],
            reference_no=self.validated_data.get("reference_no"),
            description=self.validated_data.get("description",""),
            receipt_image=self.validated_data.get("receipt_image"),
        )
        return p


