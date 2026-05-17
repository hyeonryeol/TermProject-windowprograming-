const router = require("express").Router({ mergeParams: true });
const { reviews } = require("../data/mock");

router.get("/", (req, res) => {
  const { page = 1, limit = 20, sort = "latest" } = req.query;
  const restaurantReviews = reviews[req.params.id] || [];

  let result = [...restaurantReviews];
  if (sort === "latest") result.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  else if (sort === "rating") result.sort((a, b) => b.rating - a.rating);

  const start = (parseInt(page) - 1) * parseInt(limit);
  res.json({
    success: true,
    data: result.slice(start, start + parseInt(limit)),
    error: null,
  });
});

module.exports = router;
