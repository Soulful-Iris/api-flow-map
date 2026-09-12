const jwt = require('jsonwebtoken');
function authenticate(req, res, next) {
  const token = req.headers.authorization;
  if (!token) return res.status(401).json({ error: 'missing token' });
  req.user = jwt.verify(token.replace('Bearer ', ''), process.env.JWT_SECRET);
  next();
}
function requireRole(role) {
  return (req, res, next) => (req.user.roles.includes(role) ? next() : res.status(403).end());
}
module.exports = { authenticate, requireRole };
