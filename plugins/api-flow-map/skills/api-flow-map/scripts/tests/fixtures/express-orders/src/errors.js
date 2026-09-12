class NotFoundError extends Error { constructor(what) { super(`${what} not found`); this.status = 404; } }
module.exports = { NotFoundError };
