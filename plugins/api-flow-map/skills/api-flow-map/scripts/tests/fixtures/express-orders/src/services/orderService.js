const db = require('../db');
const paymentsClient = require('../clients/payments');
const { publish } = require('../clients/events');
const logger = require('../logger');
const { isEnabled } = require('../featureFlags');

async function findById(id) {
  return db.orders.findOne({ where: { id } });
}

async function place(payload, user) {
  const total = payload.items.reduce((sum, i) => sum + i.price * i.qty, 0);
  if (total > 1000 && isEnabled('manual-review')) {
    logger.info('flagging order for review');
    const flagged = await db.orders.create({ ...payload, status: 'UNDER_REVIEW', customerId: user.id });
    await publish('order-events', { type: 'ORDER_FLAGGED', id: flagged.id });
    return flagged;
  }
  const charge = await paymentsClient.charge({ amount: total, token: payload.paymentToken });
  const order = await db.orders.create({ ...payload, status: 'CONFIRMED', paymentId: charge.id, customerId: user.id });
  await publish('order-events', { type: 'ORDER_PLACED', id: order.id });
  return order;
}

async function cancel(order, user) {
  switch (order.status) {
    case 'CONFIRMED':
      await paymentsClient.refund(order.paymentId);
      break;
    case 'UNDER_REVIEW':
      break;
    default:
      throw new Error(`cannot cancel order in status ${order.status}`);
  }
  await db.orders.update({ status: 'CANCELLED' }, { where: { id: order.id } });
  await publish('order-events', { type: 'ORDER_CANCELLED', id: order.id });
}

module.exports = { findById, place, cancel };
