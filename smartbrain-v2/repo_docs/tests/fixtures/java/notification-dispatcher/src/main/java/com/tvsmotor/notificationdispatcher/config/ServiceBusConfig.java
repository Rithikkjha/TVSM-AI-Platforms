// source: TVS-CS/notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java (trimmed)
package com.tvsmotor.notificationdispatcher.config;
import com.azure.messaging.servicebus.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import java.util.concurrent.ExecutorService;
import java.util.function.Consumer;
@Slf4j
@Configuration
public class ServiceBusConfig {
    @Bean
    public ServiceBusProcessorClient createServiceBusProcessorClientForHighPriorityNotifications(
            @Value("${spring.jms.servicebus.connection-string}") final String azureServiceBusConnectionString,
            @Value("${spring.jms.servicebus.topic.notifications}") final String topicName,
            @Value("${spring.jms.servicebus.subscription.highpriority}") final String subscriptionName,
            ExecutorService serviceBusExecutorService) {
        return createServiceBusProcessorClient(
                azureServiceBusConnectionString, topicName, subscriptionName, serviceBusExecutorService);
    }
    @Bean
    public ServiceBusProcessorClient createServiceBusProcessorClientForEmailNotifications(
            @Value("${spring.jms.servicebus.connection-string}") final String azureServiceBusConnectionString,
            @Value("${spring.jms.servicebus.topic.notifications}") final String topicName,
            @Value("${spring.jms.servicebus.subscription.email}") final String subscriptionName,
            ExecutorService serviceBusExecutorService) {
        return createServiceBusProcessorClient(
                azureServiceBusConnectionString, topicName, subscriptionName, serviceBusExecutorService);
    }
    private ServiceBusProcessorClient createServiceBusProcessorClient(
            String connectionString, String topicName, String subscriptionName, ExecutorService executorService) {
        final Consumer<ServiceBusReceivedMessageContext> onMessage = (context) -> {
            executorService.submit(() -> {
                ServiceBusReceivedMessage message = context.getMessage();
                context.complete();
            });
        };
        final Consumer<ServiceBusErrorContext> onError = (context) -> {
            log.error("error {}", context.getEntityPath());
        };
        return new ServiceBusClientBuilder()
                .connectionString(connectionString)
                .processor()
                .topicName(topicName)
                .subscriptionName(subscriptionName)
                .receiveMode(ServiceBusReceiveMode.PEEK_LOCK)
                .maxConcurrentCalls(250)
                .disableAutoComplete()
                .processMessage(onMessage)
                .processError(onError)
                .buildProcessorClient();
    }
}
