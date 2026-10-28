const { MongoClient } = require("mongodb");
const collectionNames = {
  icePrices: "icePrices",
  products: "products",
};
const connect = () => new MongoClient(process.env.MONGO_DB_HOST);
module.exports = { collectionNames, connect };
