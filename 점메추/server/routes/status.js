const router = require("express").Router({ mergeParams: true });
const { restaurants } = require("../data/mock");

router.get("/", (req, res) => {
  const restaurant = restaurants.find((r) => r.id === req.params.id);
  if (!restaurant) {
    return res.status(404).json({ success: false, data: null, error: "음식점을 찾을 수 없습니다." });
  }
  res.json({
    success: true,
    data: {
      openNow: restaurant.openNow,
      delivery: restaurant.delivery,
      waitTime: restaurant.waitTime,
      estimatedDeliveryTime: restaurant.estimatedDeliveryTime,
    },
    error: null,
  });
});

module.exports = router;
