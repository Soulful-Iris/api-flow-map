const axios = require('axios');
const PAYMENTS_URL = process.env.PAYMENTS_URL;

async function charge(req) {
  const { data } = await axios.post(`${PAYMENTS_URL}/v2/charges`, req);
  return data;
}

async function refund(paymentId) {
  await axios.post(`${PAYMENTS_URL}/v2/charges/${paymentId}/refund`);
}

module.exports = { charge, refund };
