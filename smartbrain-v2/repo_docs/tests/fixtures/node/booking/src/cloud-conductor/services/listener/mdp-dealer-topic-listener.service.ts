import { Injectable, OnModuleInit } from '@nestjs/common';
import { BaseTopicListenerService } from './base-topic-listener.service';

@Injectable()
export class MDPDealerTopicListenerService extends BaseTopicListenerService implements OnModuleInit {
    constructor(private readonly secretService: any) {
        super();
    }

    async onModuleInit(): Promise<void> {
        const queueConfig = await this.secretService.getSecret(process.env.BOOKING_SERVICE_CONFIG);
        const parsed = JSON.parse(queueConfig);
        const {
            DEALER_TOPIC_SERVICE_BUS_ENDPOINT,
            DEALER_TOPIC_NAME,
            DEALER_TOPIC_SUBSCRIPTION_NAME,
        } = parsed;
        await this.initialize(DEALER_TOPIC_SERVICE_BUS_ENDPOINT, DEALER_TOPIC_NAME, DEALER_TOPIC_SUBSCRIPTION_NAME);
    }
}
