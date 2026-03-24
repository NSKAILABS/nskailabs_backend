import os
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Subscription, Payment, LicenseKey

PLAN_PRICES = {
    'starter': 2000000,
    'professional': 4500000,
}


def get_razorpay_client():
    import razorpay
    key_id = os.environ.get('RAZORPAY_KEY_ID', '')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    plan = request.data.get('plan')
    if plan not in PLAN_PRICES:
        return Response(
            {'error': 'Invalid plan. Choose starter or professional.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    client = get_razorpay_client()
    if not client:
        return Response(
            {'error': 'Payment service not configured. Please contact support.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    amount = PLAN_PRICES[plan]

    try:
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'notes': {
                'user_id': str(request.user.id),
                'plan': plan,
            }
        }
        razorpay_order = client.order.create(data=order_data)
    except Exception:
        return Response(
            {'error': 'Failed to create payment order. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    subscription = Subscription.objects.create(
        user=request.user,
        plan=plan,
        status='pending',
        amount=amount / 100,
    )

    Payment.objects.create(
        user=request.user,
        subscription=subscription,
        amount=amount / 100,
        currency='INR',
        status='created',
        razorpay_order_id=razorpay_order['id'],
    )

    return Response({
        'order_id': razorpay_order['id'],
        'amount': amount,
        'currency': 'INR',
        'key_id': os.environ.get('RAZORPAY_KEY_ID', ''),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response(
            {'error': 'Missing payment verification data.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        key_secret.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

    if generated_signature != razorpay_signature:
        return Response(
            {'error': 'Payment verification failed.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment record not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = 'paid'
    payment.save()

    subscription = payment.subscription
    if subscription:
        subscription.status = 'active'
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()

        license_key = secrets.token_hex(16).upper()
        license_key = '-'.join([license_key[i:i+4] for i in range(0, len(license_key), 4)])

        LicenseKey.objects.create(
            user=request.user,
            subscription=subscription,
            key=license_key,
            product=f"photonic-ai-{subscription.plan}",
            is_active=True,
            expires_at=subscription.end_date,
        )

    return Response({
        'message': 'Payment verified successfully.',
        'subscription_id': subscription.id if subscription else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_subscriptions(request):
    subs = Subscription.objects.filter(user=request.user)
    data = []
    for sub in subs:
        licenses = LicenseKey.objects.filter(subscription=sub, is_active=True)
        data.append({
            'id': sub.id,
            'plan': sub.plan,
            'status': sub.status,
            'amount': str(sub.amount),
            'start_date': sub.start_date,
            'end_date': sub.end_date,
            'license_keys': [{'key': lk.key, 'product': lk.product, 'expires_at': lk.expires_at} for lk in licenses],
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def plans(request):
    return Response([
        {
            'id': 'starter',
            'name': 'Starter',
            'price': 20000,
            'currency': 'INR',
            'period': 'month',
            'features': [
                'Basic simulation tools',
                'Up to 50 simulations/month',
                'Standard support',
                'GDS export',
                'Community access',
            ],
        },
        {
            'id': 'professional',
            'name': 'Professional',
            'price': 45000,
            'currency': 'INR',
            'period': 'month',
            'features': [
                'Advanced AI optimization',
                'Unlimited simulations',
                'Priority support',
                'RCWA & FDTD workflows',
                'Team collaboration',
                'API access',
            ],
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price': None,
            'currency': 'INR',
            'period': 'custom',
            'features': [
                'Custom integrations',
                'Dedicated infrastructure',
                '24/7 support',
                'On-premise deployment',
                'Custom training',
                'SLA guarantee',
            ],
        },
    ])
