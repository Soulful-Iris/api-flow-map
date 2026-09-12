const express = require('express');
const ordersRouter = require('./routes/orders');
const healthRouter = require('./routes/health');
const { authenticate } = require('./middleware/auth');

const app = express();
app.use(express.json());
app.use('/health', healthRouter);
app.use('/api/v1/orders', authenticate, ordersRouter);

module.exports = app;
