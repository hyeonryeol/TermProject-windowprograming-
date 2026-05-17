const router = require("express").Router();
const { reviews } = require("../data/mock");

router.post("/reviews/import", (req, res) => {
  const { platform, restaurantId, reviews: incoming } = req.body;
  if (!platform || !restaurantId || !Array.isArray(incoming)) {
    return res.status(400).json({ success: false, data: null, error: "platform, restaurantId, reviews 배열이 필요합니다." });
  }

  if (!reviews[restaurantId]) reviews[restaurantId] = [];

  const imported = incoming.map((r, i) => ({
    id: `rev_import_${Date.now()}_${i}`,
    platform,
    rating: r.rating,
    content: r.content,
    sentimentScore: r.sentimentScore ?? 0.75,
    createdAt: r.createdAt ?? new Date().toISOString().split("T")[0],
  }));

  reviews[restaurantId].push(...imported);

  res.json({ success: true, data: { imported: imported.length }, error: null });
});

module.exports = router;
