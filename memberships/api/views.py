from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.responses import ok, fail
from memberships.models import Membership, EducationLevel, Institution, MembershipType, MembershipPayment
from .serializers import (
    MembershipReadSerializer,
    MembershipInitRequestSerializer,
    MembershipCompleteRequestSerializer, EducationLevelListSerializer, InstitutionListSerializer,
    MembershipTypeListSerializer, CreateOnlinePaymentSerializer, PaymentReadSerializer, CreateOfflinePaymentSerializer,
)
import requests

LOOKUP_PERMISSION = AllowAny

class MembershipViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    Users operate only on their own memberships.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        return Membership.objects.select_related(
            "membership_type", "profile_info", "contact_info",
            "education_info", "work_info", "workflow_status"
        ).filter(user=self.request.user)

    @extend_schema(
        tags=["Memberships"],
        request=MembershipInitRequestSerializer,
        responses={201: MembershipReadSerializer, 200: MembershipReadSerializer},
        examples=[OpenApiExample(
            "InitMembership (new or update)",
            value={
                # optional to target an existing membership:
                # "membership_uuid": "00000000-0000-0000-0000-000000000000",
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
        summary="Step 1: create draft membership or update existing (status 2/11)"
    )
    @action(detail=False, methods=["POST"], url_path="init")
    def init_membership(self, request):
        ser = MembershipInitRequestSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        membership = ser.save()
        status_code = 201 if "membership_uuid" not in ser.validated_data else 200
        return ok(MembershipReadSerializer(membership).data, "Membership initialized.", status=status_code)

    @extend_schema(
        tags=["Memberships"],
        request=MembershipCompleteRequestSerializer,
        responses={200: MembershipReadSerializer},
        examples=[OpenApiExample(
            "CompleteMembership (create/update based on status)",
            value={
                "education_info": {"education": 1, "institution": 2, "other_societies": "IEEE"},
                "work_info": {
                    "occupation": "Engineer",
                    "company_name": "Acme Pte Ltd",
                    "company_address": "123 Street",
                    "company_postal_code": "654321",
                    "company_contact": "+6566667777"
                }
            },
            request_only=True
        )],
        summary="Step 2: add/update Education & Work info (status 10/11/14)"
    )
    @action(detail=True, methods=["POST"], url_path="complete")
    def complete_membership(self, request, uuid=None):
        membership = get_object_or_404(self.get_queryset(), uuid=uuid)
        ser = MembershipCompleteRequestSerializer(data=request.data, context={"membership": membership})
        ser.is_valid(raise_exception=True)
        membership = ser.save()
        payment = ser.context.get("payment")
        payload = {
            "membership": MembershipReadSerializer(membership).data,
            "payment": PaymentReadSerializer(payment).data if payment else None
        }
        return ok(payload, "Membership completed; payment prepared.")

    @extend_schema(
        tags=["Memberships"],
        responses={200: MembershipReadSerializer},
        summary="Get my membership by UUID"
    )
    def retrieve(self, request, *args, **kwargs):
        membership = self.get_object()
        return Response(MembershipReadSerializer(membership).data)

    @extend_schema(
        tags=["Memberships"],
        responses={200: MembershipReadSerializer(many=True)},
        summary="List my memberships"
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return Response(MembershipReadSerializer(qs, many=True).data)
  # or AllowAny

    @extend_schema(
        tags=["Payments"],
        request=CreateOnlinePaymentSerializer,
        responses={201: PaymentReadSerializer},
        summary="Create online (HitPay) payment for this membership"
    )
    @action(detail=True, methods=["POST"], url_path="payments/online")
    def create_online_payment(self, request, uuid=None):
        membership = self.get_object()
        ser = CreateOnlinePaymentSerializer(data=request.data, context={"membership": membership})
        ser.is_valid(raise_exception=True)
        payment = ser.save()
        return ok(PaymentReadSerializer(payment).data, "Online payment intent created.", status=201)


    @extend_schema(
        tags=["Payments"],
        request=CreateOfflinePaymentSerializer,
        responses={201: PaymentReadSerializer},
        summary="Record an offline payment (bank transfer / cash)"
    )
    @action(detail=True, methods=["POST"], url_path="payments/offline")
    def create_offline_payment(self, request, uuid=None):
        membership = self.get_object()
        ser = CreateOfflinePaymentSerializer(data=request.data, context={"membership": membership})
        ser.is_valid(raise_exception=True)
        payment = ser.save()
        return ok(PaymentReadSerializer(payment).data, "Offline payment recorded (pending).", status=201)


    @extend_schema(
        tags=["Payments"],
        responses={200: PaymentReadSerializer(many=True)},
        summary="List payments for this membership"
    )
    @action(detail=True, methods=["GET"], url_path="payments")
    def list_payments(self, request, uuid=None):
        membership = self.get_object()
        qs = membership.payments.all()
        return ok(PaymentReadSerializer(qs, many=True).data, "Payments")

@extend_schema(tags=["Lookups"], summary="List education levels")
class EducationLevelListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = EducationLevelListSerializer

    def get_queryset(self):
        return EducationLevel.objects.filter(is_active=True).order_by("name")

@extend_schema(tags=["Lookups"], summary="List institutions")
class InstitutionListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = InstitutionListSerializer

    def get_queryset(self):
        return Institution.objects.filter(is_active=True).order_by("name")

@extend_schema(tags=["Lookups"], summary="List membership types")
class MembershipTypeListAPIView(ListAPIView):
    permission_classes = [LOOKUP_PERMISSION]
    serializer_class = MembershipTypeListSerializer

    def get_queryset(self):
        return MembershipType.objects.filter(is_active=True).order_by("name")


# @extend_schema(tags=["Memberships"], summary="Membership QR Payment")
# class QRPaymentView(APIView):
#     def post(self, request):
#         amount = 30 # request.data.get('amount')
#         currency = request.data.get('currency', 'SGD')
#
#         # Validate required fields
#         if not amount:
#             return Response({'error': 'Amount is required'},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         url = 'https://api.sandbox.hit-pay.com/v1/payment-requests'
#
#         headers = {
#             'X-BUSINESS-API-KEY': settings.HITPAY_API_KEY,
#             'Content-Type': 'application/x-www-form-urlencoded',  # Critical!
#             'X-Requested-With': 'XMLHttpRequest'  # Critical!
#         }
#
#         # Use proper form data format
#         payload = {
#             'amount': str(amount),  # Ensure string format
#             'currency': currency.upper(),
#             'payment_methods[]': 'paynow_online',  # Note the [] syntax
#             'generate_qr': 'true',  # String, not boolean
#             'webhook': 'https://yoursite.com/webhook/'
#         }
#
#         try:
#             response = requests.post(url, data=payload, headers=headers)
#             response.raise_for_status()
#
#             payment_data = response.json()
#             return Response({
#                 'payment_id': payment_data['id'],
#                 'qr_code': payment_data['qr_code_data']['qr_code'],
#                 'status': 'success'
#             })
#
#         except requests.exceptions.HTTPError as e:
#             return Response({
#                 'error': f'HTTP {e.response.status_code}: {e.response.text}',
#                 'status': 'failed'
#             }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Payments"],
    request=CreateOnlinePaymentSerializer,
    responses={201: PaymentReadSerializer},
    summary="Create online (HitPay) payment intent for a membership"
)
@action(detail=True, methods=["POST"], url_path="payments/online")
def create_online_payment(self, request, uuid=None):
    membership = self.get_object()
    ser = CreateOnlinePaymentSerializer(data=request.data, context={"membership": membership})
    ser.is_valid(raise_exception=True)
    payment = ser.save()
    return ok(PaymentReadSerializer(payment).data, "Online payment intent created.", status=201)

@extend_schema(
    tags=["Payments"],
    request=CreateOfflinePaymentSerializer,
    responses={201: PaymentReadSerializer},
    summary="Record an offline payment (bank transfer / cash) pending confirmation"
)
@action(detail=True, methods=["POST"], url_path="payments/offline")
def create_offline_payment(self, request, uuid=None):
    membership = self.get_object()
    ser = CreateOfflinePaymentSerializer(data=request.data, context={"membership": membership})
    ser.is_valid(raise_exception=True)
    payment = ser.save()
    return ok(PaymentReadSerializer(payment).data, "Offline payment recorded (pending).", status=201)

@extend_schema(
    tags=["Payments"],
    responses={200: PaymentReadSerializer(many=True)},
    summary="List payments for this membership"
)
@action(detail=True, methods=["GET"], url_path="payments")
def list_payments(self, request, uuid=None):
    membership = self.get_object()
    qs = membership.payments.all()
    return ok(PaymentReadSerializer(qs, many=True).data, "Payments")


@extend_schema(
    tags=["Payments"],
    request=None,
    responses={200: PaymentReadSerializer},
    summary="Confirm an offline payment by Management (mark as paid)"
)
@action(detail=True, methods=["POST"], url_path="payments/{payment_uuid}/confirm", url_name="confirm_payment")
def confirm_offline_payment(self, request, uuid=None, payment_uuid=None):
    # enforce staff here; or move to a separate ViewSet with IsAdminUser
    if not request.user.is_staff:
        return fail("Only staff can confirm payments.", status=403)
    membership = self.get_object()
    try:
        payment = membership.payments.get(uuid=payment_uuid, method__in=["bank_transfer","cash"])
    except MembershipPayment.DoesNotExist:
        return fail("Payment not found.", status=404)
    payment.status = "paid"
    from django.utils import timezone
    payment.paid_at = timezone.now()
    payment.save()
    return ok(PaymentReadSerializer(payment).data, "Payment confirmed.")


# Webhook handler
class HitPayWebhookView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @extend_schema(tags=["Payments"], summary="HitPay webhook")
    def post(self, request):
        payload = request.data
        ext_id = payload.get("id") or payload.get("payment_request_id")
        status = (payload.get("status") or "").lower()
        if not ext_id:
            return fail("Missing id.", status=400)

        try:
            payment = MembershipPayment.objects.get(external_id=ext_id, method="hitpay")
        except MembershipPayment.DoesNotExist:
            return fail("Payment not found.", status=404)

        # map provider status to our status
        mapping = {
            "succeeded": "paid",
            "completed": "paid",
            "pending": "created",
            "failed": "failed",
            "cancelled": "cancelled",
        }
        new_status = mapping.get(status, payment.status)
        payment.status = new_status
        payment.raw_response = payload
        from django.utils import timezone
        if new_status == "paid" and not payment.paid_at:
            payment.paid_at = timezone.now()
        payment.save()
        return ok(PaymentReadSerializer(payment).data, "Webhook processed.")