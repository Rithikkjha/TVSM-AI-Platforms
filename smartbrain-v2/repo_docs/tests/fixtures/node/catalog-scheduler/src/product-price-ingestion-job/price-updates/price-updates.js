const { ServiceBusClient } = require("@azure/service-bus");
const { collectionNames } = require("../../constants/db-constant");

class PriceUpdates {
  async sendMessagesViaServiceBus(priceDifferenceList, context) {
    if (priceDifferenceList.length) {
      const topicName = process.env.SERVICE_BUS_TOPIC_NAME;
      const serviceBusPrimaryEndPoint = process.env.SERVICE_BUS_ENDPOINT;
      const serviceBusClient = new ServiceBusClient(serviceBusPrimaryEndPoint);
      const sender = serviceBusClient.createSender(topicName);
      await sender.sendMessages([]);
    }
  }
  async readPrices(dbConnection) {
    return dbConnection.collection(collectionNames.icePrices).find({}).toArray();
  }
}
module.exports = new PriceUpdates();
