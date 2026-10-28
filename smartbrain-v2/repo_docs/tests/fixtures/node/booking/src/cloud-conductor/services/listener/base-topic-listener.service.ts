import {
    ServiceBusClient,
    ServiceBusSessionReceiver,
} from '@azure/service-bus';

export abstract class BaseTopicListenerService {
    protected serviceBusClient: ServiceBusClient;
    protected topicName: string;
    protected subscriptionName: string;

    protected async initialize(endpoint: string, topic: string, subscription: string): Promise<void> {
        this.serviceBusClient = new ServiceBusClient(endpoint);
        this.topicName = topic;
        this.subscriptionName = subscription;
    }

    private async acceptOne(): Promise<void> {
        const receiver = await this.serviceBusClient.acceptNextSession(
            this.topicName,
            this.subscriptionName,
        );
        receiver.subscribe({ processMessage: async () => {}, processError: async () => {} });
    }
}
