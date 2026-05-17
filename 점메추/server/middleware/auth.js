const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "foodfusion_secret_key";

function authMiddleware(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith("Bearer ")) {
    return res.status(401).json({ success: false, data: null, error: "인증 토큰이 없습니다." });
  }
  try {
    req.user = jwt.verify(header.split(" ")[1], JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ success: false, data: null, error: "유효하지 않은 토큰입니다." });
  }
}

module.exports = { authMiddleware, JWT_SECRET };
