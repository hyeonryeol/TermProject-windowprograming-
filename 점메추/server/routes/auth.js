const router = require("express").Router();
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { users } = require("../data/mock");
const { JWT_SECRET } = require("../middleware/auth");

router.post("/register", async (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password || !name) {
    return res.status(400).json({ success: false, data: null, error: "이메일, 비밀번호, 이름을 입력해주세요." });
  }
  if (users.find((u) => u.email === email)) {
    return res.status(400).json({ success: false, data: null, error: "이미 사용 중인 이메일입니다." });
  }
  const hashed = await bcrypt.hash(password, 10);
  const user = { id: `user_${Date.now()}`, email, name, password: hashed, preferences: {} };
  users.push(user);
  const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: "24h" });
  res.status(201).json({ success: true, data: { token, user: { id: user.id, email, name } }, error: null });
});

router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const user = users.find((u) => u.email === email);
  if (!user || !(await bcrypt.compare(password, user.password))) {
    return res.status(401).json({ success: false, data: null, error: "이메일 또는 비밀번호가 잘못되었습니다." });
  }
  const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: "24h" });
  res.json({ success: true, data: { token, user: { id: user.id, email: user.email, name: user.name } }, error: null });
});

module.exports = router;
