const orderService = require('../services/orderService');
const { NotFoundError } = require('../errors');

async function getOrder(req, res) {
  const order = await orderService.findById(req.params.id);
  if (!order) {
    return res.status(404).json({ error: 'order not found' });
  }
  if (order.customerId !== req.user.id && !req.user.roles.includes('admin')) {
    return res.status(403).json({ error: 'forbidden' });
  }
  res.json(order);
}

async function createOrder(req, res, next) {
  try {
    const order = await orderService.place(req.body, req.user);
    res.status(201).json(order);
  } catch (err) {
    if (err.code === 'OUT_OF_STOCK') {
      return res.status(409).json({ error: err.message });
    }
    next(err);
  }
}

async function cancelOrder(id, user) {
  const order = await orderService.findById(id);
  if (!order) throw new NotFoundError('order');
  await orderService.cancel(order, user);
}

module.exports = { getOrder, createOrder, cancelOrder };
