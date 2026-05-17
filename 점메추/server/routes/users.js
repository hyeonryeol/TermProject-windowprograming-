const router = require("express").Router();
const { users } = require("../data/mock");
const { authMiddleware } = require("../middleware/auth");

router.get("/me", authMiddleware, (req, res) => {
  const user = users.find((u) => u.id === req.user.id);
  if (!user) return res.status(404).json({ success: false, data: null, error: "사용자를 찾을 수 없습니다." });
  const { password, ...data } = user;
  res.json({ success: true, data, error: null });
});

router.post("/preferences", authMiddleware, (req, res) => {
  const user = users.find((u) => u.id === req.user.id);
  if (!user) return res.status(404).json({ success: false, data: null, error: "사용자를 찾을 수 없습니다." });

  const { favoriteCategories, priceRange, spicyLevel } = req.body;
  user.preferences = { favoriteCategories, priceRange, spicyLevel };

  res.json({ success: true, data: user.preferences, error: null });
});

module.exports = router;
