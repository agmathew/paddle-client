import os
from datetime import datetime, timedelta

import pytest

from paddle import PaddleException

from .test_paddle import paddle_client  # NOQA: F401


@pytest.fixture()
def create_coupon(paddle_client):  # NOQA: F811
    product_id = int(os.environ['PADDLE_TEST_DEFAULT_PRODUCT_ID'])
    currency = 'GBP'
    now = datetime.now().isoformat()
    response = paddle_client.create_coupon(
        coupon_type='product',
        discount_type='percentage',
        discount_amount=1,
        allowed_uses=1,
        recurring=False,
        currency=currency,
        product_ids=[product_id],
        coupon_code='paddle-python-create_coupon_fixture-{0}'.format(now),
        description='Test coupon created by paddle-python create_coupon_fixture',  # NOQA: E501
        expires=datetime.today(),
        minimum_threshold=9999,
        group='paddle-python',
    )
    coupon_code = response['coupon_codes'][0]
    yield coupon_code, product_id

    try:
        paddle_client.delete_coupon(
            coupon_code=coupon_code, product_id=product_id
        )
    except PaddleException as error:
        valid_error = 'Paddle error 135 - Unable to find requested coupon'
        if str(error) != valid_error:
            raise


def test_list_coupons(paddle_client, create_coupon):  # NOQA: F811
    # ToDo: Create coupon with fixture
    coupon_code, product_id = create_coupon
    response = paddle_client.list_coupons(product_id=product_id)
    for coupon in response:
        assert 'allowed_uses' in coupon
        assert 'coupon' in coupon
        assert 'description' in coupon
        assert 'discount_amount' in coupon
        assert 'discount_currency' in coupon
        assert 'discount_type' in coupon
        assert 'expires' in coupon
        assert 'is_recurring' in coupon
        assert 'times_used' in coupon


def test_list_coupons_invalid_product(paddle_client):  # NOQA: F811
    product_id = 11
    with pytest.raises(PaddleException) as error:
        paddle_client.list_coupons(product_id=product_id)

    error.match('Paddle error 108 - Unable to find requested product')


def test_create_coupon(paddle_client):  # NOQA: F811
    coupon_type = 'product'
    discount_type = 'percentage'
    discount_amount = 1
    allowed_uses = 1
    recurring = False
    product_id = int(os.environ['PADDLE_TEST_DEFAULT_PRODUCT_ID'])
    product_ids = [product_id]
    currency = 'GBP'
    now = datetime.now().isoformat()
    coupon_code = 'paddle-python-test_create_coupon-{0}'.format(now)
    description = 'Test code created by paddle-python test_create_coupon'
    expires = datetime.today().strftime('%Y-%m-%d')
    minimum_threshold = 100
    group = 'paddle-python'

    response = paddle_client.create_coupon(
        coupon_type=coupon_type,
        discount_type=discount_type,
        discount_amount=discount_amount,
        allowed_uses=allowed_uses,
        recurring=recurring,
        currency=currency,
        product_ids=product_ids,
        coupon_code=coupon_code,
        description=description,
        expires=expires,
        minimum_threshold=minimum_threshold,
        group=group,
    )
    assert response['coupon_codes'] == [coupon_code]

    coupon_list = paddle_client.list_coupons(product_id=product_id)
    paddle_client.delete_coupon(coupon_code=coupon_code, product_id=product_id)

    found = False
    discount_percentage = discount_amount / 100
    expires_time = '{0} 00:00:00'.format(expires)
    for coupon in coupon_list:
        if coupon['coupon'] != coupon_code:
            continue
        found = True
        assert 'times_used' in coupon
        assert coupon['description'] == description
        assert coupon['discount_type'] == discount_type
        assert coupon['allowed_uses'] == allowed_uses
        assert float(coupon['discount_amount']) == discount_percentage
        assert coupon['is_recurring'] == recurring
        assert coupon['expires'] == expires_time
        # Commented out due to a bug in the Paddle list coupons response
        # The discount_currency is returned as None
        # assert coupon['discount_currency'] == currency
    assert found


def test_delete_coupon(paddle_client, create_coupon):  # NOQA: F811
    coupon_code, product_id = create_coupon

    paddle_client.delete_coupon(coupon_code=coupon_code, product_id=product_id)
    for coupon in paddle_client.list_coupons(product_id=product_id):
        assert coupon['coupon'] != coupon_code


def test_update_coupon(paddle_client, create_coupon):  # NOQA: F811
    coupon_code, product_id = create_coupon
    now = datetime.now().isoformat()
    new_coupon_code = 'paddle-python-test_update_coupon-{0}'.format(now)
    expires = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    currency = 'GBP'
    recurring = True
    allowed_uses = 2
    discount_amount = 2
    response = paddle_client.update_coupon(
        coupon_code=coupon_code,
        new_coupon_code=new_coupon_code,
        new_group='paddle-python-test',
        product_ids=[product_id],
        expires=expires,
        allowed_uses=allowed_uses,
        currency=currency,
        minimum_threshold=9998,
        discount_amount=discount_amount,
        recurring=True
    )
    assert response['updated'] == 1

    coupon_list = paddle_client.list_coupons(product_id=product_id)
    paddle_client.delete_coupon(
        coupon_code=new_coupon_code, product_id=product_id
    )
    found = False
    discount_percentage = discount_amount / 100
    expires_time = '{0} 00:00:00'.format(expires)
    for coupon in coupon_list:
        assert coupon['coupon'] != coupon_code
        if coupon['coupon'] == new_coupon_code:
            found = True
            assert 'description' in coupon
            assert 'times_used' in coupon
            assert 'discount_type' in coupon
            assert coupon['allowed_uses'] == allowed_uses
            assert float(coupon['discount_amount']) == discount_percentage
            assert coupon['is_recurring'] == recurring
            assert coupon['expires'] == expires_time
            # Commented out due to a bug in the Paddle list coupons response
            # The discount_currency is returned as None
            # assert coupon['discount_currency'] == currency
    assert found
