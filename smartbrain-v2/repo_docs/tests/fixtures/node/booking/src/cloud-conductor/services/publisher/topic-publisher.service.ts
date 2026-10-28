import { ServiceBusClient, ServiceBusSender } from "@azure/service-bus";

export class TopicPublisherService {
    private serviceBusClient: ServiceBusClient;
    private topic: string;
    private sender: ServiceBusSender;

    constructor(private readonly secretService: any) { }

    async initialize(): Promise<void> {
        const configString: string = await this.secretService.getSecret(process.env.BOOKING_SERVICE_CONFIG);
        const configJson = JSON.parse(configString);
        const { TOPIC_SB_ENDPOINT, TOPIC_NAME } = configJson;
        this.topic = TOPIC_NAME;
        this.serviceBusClient = new ServiceBusClient(TOPIC_SB_ENDPOINT);
        this.sender = this.serviceBusClient.createSender(this.topic);
    }
}
