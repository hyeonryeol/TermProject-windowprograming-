const express = require("express");
const app = express();

app.use(express.json());

app.use("/v1/auth", require("./routes/auth"));
app.use("/v1/restaurants", require("./routes/restaurants"));
app.use("/v1/restaurants/:id/reviews", require("./routes/reviews"));
app.use("/v1/restaurants/:id/status", require("./routes/status"));
app.use("/v1/recommendations", require("./routes/recommendations"));
app.use("/v1/users", require("./routes/users"));
app.use("/v1/internal", require("./routes/internal"));

app.use((req, res) => {
  res.status(404).json({ success: false, data: null, error: "존재하지 않는 엔드포인트입니다." });
});

module.exports = app;
