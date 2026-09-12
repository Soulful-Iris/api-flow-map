const Joi = require('joi');
module.exports = { createOrderSchema: Joi.object({ items: Joi.array().min(1).required() }) };
