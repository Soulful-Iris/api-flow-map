const express = require('express');
const { requireRole } = require('../middleware/auth');
const validate = require('../middleware/validate');
const { createOrderSchema } = require('../schemas/order');
const orderController = require('../controllers/orderController');

const router = express.Router();

router.get('/:id', orderController.getOrder);
router.post('/', requireRole('orders:write'), validate(createOrderSchema), orderController.createOrder);
router.delete('/:id', requireRole('orders:write'), async (req, res, next) => {
  try {
    await orderController.cancelOrder(req.params.id, req.user);
    res.sendStatus(204);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
