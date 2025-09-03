# memberships/api/views.py - CORRECTED VERSION
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.responses import ok, fail
from memberships.models import Membership, EducationLevel, Institution, MembershipType, MembershipPayment

# Import ONLY the new serializers
from .serializers import (
    MembershipReadSerializer,
    MembershipPage1Serializer,
    MembershipPage2Serializer,
    EducationLevelListSerializer,
    InstitutionListSerializer,
    MembershipTypeListSerializer,
    CreateOnlinePaymentSerializer,
    PaymentReadSerializer,
    CreateOfflinePaymentSerializer,
)

LOOKUP_PERMISSION = AllowAny


class MembershipViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    Enhanced membership management with 2-page workflow.
    Page 1: Profile + Contact Info
    Page 2: Education + Work Info + Submit with HitPay QR generation
    """
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        return Membership.objects.select_related(
            "membership_type", "profile_info", "contact_info",
            "education_info", "work_info", "workflow_status"
        ).filter(user=self.request.user)

    def get_or_create_membership(self):
        """Get existing membership or create new draft"""
        membership, created = Membership.objects.get_or_create(
            user=self.request.user,
            defaults={
                'workflow_status': self._get_draft_status()
            }
        )
        return membership

    def _get_draft_status(self):
        """Get or create draft status"""
        from core.models import Status
        draft_status, _ = Status.objects.get_or_create(
            status_code="10",
            defaults={"internal_status": "Draft", "external_status": "Draft"}
        )
        return draft_status

    @extend_schema(
        tags=["Memberships"],
        responses={200: MembershipReadSerializer},
        summary="Get my membership (creates if not exists)"
    )
    @action(detail=False, methods=["GET"], url_path="my-membership")
    def my_membership(self, request):
        """Get user's membership, create if doesn't exist"""
        membership = self.get_or_create_membership()
        serializer = MembershipReadSerializer(membership, context={'request': request})
        return ok(serializer.data, "Membership retrieved")

    @extend_schema(
        tags=["Memberships"],
        request=MembershipPage1Serializer,
        responses={200: MembershipReadSerializer},
        examples=[OpenApiExample(
            "Page1Submit",
            value={
                "profile_info": {
                    "full_name": "Alice Tan",
                    "date_of_birth": "1995-02-03",
                    "gender": "F",
                    "country_of_birth": "SG",
                    "city_of_birth": "Singapore",
                    "citizenship": "SG"
                },
                "contact_info": {
                    "nric_fin": "S1234567A",
                    "primary_contact": "+6591234567",
                    "secondary_contact": "+6597654321",
                    "residential_status": "singaporean",
                    "postal_code": "123456",
                    "address": "1 Orchard Rd"
                },
                "membership_type": 1
            },
            request_only=True
        )],
        summary="Page 1: Submit Profile + Contact Info + Membership Type"
    )
    @action(detail=False, methods=["POST"], url_path="submit-page1")
    def submit_page1(self, request):
        """Page 1: Submit Profile Info, Contact Info, Membership Type, and Profile Picture"""
        membership = self.get_or_create_membership()

        serializer = MembershipPage1Serializer(
            data=request.data,
            context={'membership': membership}
        )
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()

        response_serializer = MembershipReadSerializer(membership, context={'request': request})
        return ok(response_serializer.data, "Page 1 completed successfully. Please proceed to Page 2.")

    @extend_schema(
        tags=["Memberships"],
        request=MembershipPage2Serializer,
        responses={200: MembershipReadSerializer},
        examples=[OpenApiExample(
            "Page2Submit",
            value={
                "education_info": {
                    "education": 1,
                    "institution": 2,
                    "other_societies": "IEEE, Computing Society"
                },
                "work_info": {
                    "occupation": "Software Engineer",
                    "company_name": "Tech Corp Pte Ltd",
                    "company_address": "123 Tech Street",
                    "company_postal_code": "654321",
                    "company_contact": "+6566667777"
                }
            },
            request_only=True
        )],
        summary="Page 2: Submit Education + Work Info + Generate HitPay QR"
    )
    @action(detail=False, methods=["POST"], url_path="submit-page2")
    def submit_page2(self, request):
        """Page 2: Submit Education Info, Work Info, and Generate HitPay Payment QR"""
        membership = self.get_or_create_membership()

        serializer = MembershipPage2Serializer(
            data=request.data,
            context={'membership': membership}
        )
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()

        # Get the generated payment with QR
        payment = serializer.context.get('payment')

        response_data = {
            "membership": MembershipReadSerializer(membership, context={'request': request}).data,
            "payment": PaymentReadSerializer(payment).data if payment else None,
            "qr_code_url": payment.qr_code if payment else None,
            "payment_amount": str(payment.amount) if payment else None,
            "payment_currency": payment.currency if payment else None
        }

        return ok(
            response_data,
            "Application submitted successfully! Please scan the QR code to complete payment."
        )

    @extend_schema(
        tags=["Memberships"],
        responses={200: MembershipReadSerializer},
        summary="Get my membership by UUID"
    )
    def retrieve(self, request, *args, **kwargs):
        membership = self.get_object()
        serializer = MembershipReadSerializer(membership, context={'request': request})
        return ok(serializer.data)

    @extend_schema(
        tags=["Memberships"],
        responses={200: MembershipReadSerializer},
        summary="List my memberships (should be only one)"
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = MembershipReadSerializer(qs, many=True, context={'request': request})
        return ok(serializer.data)

    @extend_schema(
        tags=["Payments"],
        request=CreateOnlinePaymentSerializer,
        responses={201: PaymentReadSerializer},
        summary="Create online (HitPay) payment for membership"
    )
    @action(detail=False, methods=["POST"], url_path="create-payment")
    def create_online_payment(self, request):
        membership = self.get_or_create_membership()
        serializer = CreateOnlinePaymentSerializer(data=request.data, context={"membership": membership})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return ok(PaymentReadSerializer(payment).data, "Online payment intent created.", status=201)

    @extend_schema(
        tags=["Payments"],
        request=CreateOfflinePaymentSerializer,
        responses={201: PaymentReadSerializer},
        summary="Record an offline payment (bank transfer / cash)"
    )
    @action(detail=False, methods=["POST"], url_path="offline-payment")
    def create_offline_payment(self, request):
        membership = self.get_or_create_membership()
        serializer = CreateOfflinePaymentSerializer(data=request.data, context={"membership": membership})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return ok(PaymentReadSerializer(payment).data, "Offline payment recorded (pending).", status=201)

    @extend_schema(
        tags=["Payments"],
        responses={200: PaymentReadSerializer(many=True)},
        summary="List payments for my membership"
    )
    @action(detail=False, methods=["GET"], url_path="payments")
    def list_payments(self, request):
        membership = self.get_or_create_membership()
        qs = membership.payments.all()
        return ok(PaymentReadSerializer(qs, many=True).data, "Payments")


# Lookup views
@extend_schema(tags=["Lookups"], summary="List education levels")
class EducationLevelListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = EducationLevelListSerializer

    def get_queryset(self):
        return EducationLevel.objects.filter(is_active=True).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ok(serializer.data, "Education levels")


@extend_schema(tags=["Lookups"], summary="List institutions")
class InstitutionListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = InstitutionListSerializer

    def get_queryset(self):
        return Institution.objects.filter(is_active=True).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ok(serializer.data, "Institutions")


@extend_schema(tags=["Lookups"], summary="List membership types")
class MembershipTypeListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = MembershipTypeListSerializer

    def get_queryset(self):
        return MembershipType.objects.filter(is_active=True).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ok(serializer.data, "Membership types")


# Webhook handler
@extend_schema(tags=["Payments"], summary="HitPay webhook handler")
class HitPayWebhookView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        payload = request.data
        ext_id = payload.get("id") or payload.get("payment_request_id")
        status = (payload.get("status") or "").lower()

        if not ext_id:
            return fail("Missing payment ID.", status=400)

        try:
            payment = MembershipPayment.objects.get(external_id=ext_id, method="hitpay")
        except MembershipPayment.DoesNotExist:
            return fail("Payment not found.", status=404)

        # Map provider status to our status
        status_mapping = {
            "succeeded": "paid",
            "completed": "paid",
            "pending": "created",
            "failed": "failed",
            "cancelled": "cancelled",
        }

        new_status = status_mapping.get(status, payment.status)
        payment.status = new_status
        payment.raw_response = payload

        from django.utils import timezone
        if new_status == "paid" and not payment.paid_at:
            payment.paid_at = timezone.now()

        payment.save()

        return ok(PaymentReadSerializer(payment).data, "Webhook processed successfully")