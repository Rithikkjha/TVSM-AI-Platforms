import { ServiceBusClient, ServiceBusMessage } from '@azure/service-bus';
import { logger } from '../utils/functions';
class PriceEnginePricePublisher {
  private readonly connectionString = process.env.CONNECTION_STRING_MARKETPLACE || '';
  private readonly topicName = process.env.TOPIC_NAME_MARKETPLACE || '';
  public async publish(messages: ServiceBusMessage[]): Promise<void> {
    if (!messages.length) return;
    const client = new ServiceBusClient(this.connectionString);
    const sender = client.createSender(this.topicName);
    try {
      await sender.sendMessages(messages);
      logger.info(`Published ${messages.length} message(s)`);
    } finally {
      await sender.close();
    }
  }
}
export const priceEnginePricePublisher = new PriceEnginePricePublisher();
