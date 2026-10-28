// synthetic (no TVS-CS counterpart): a param-built processor helper that nothing calls
package com.tvsmotor.notificationdispatcher.config;
import com.azure.messaging.servicebus.*;
public class OrphanServiceBusHelper {
    ServiceBusProcessorClient build(String connectionString, String topicName, String subscriptionName) {
        return new ServiceBusClientBuilder()
                .connectionString(connectionString)
                .processor()
                .topicName(topicName)
                .subscriptionName(subscriptionName)
                .processMessage(c -> c.complete())
                .processError(e -> {})
                .buildProcessorClient();
    }
}
