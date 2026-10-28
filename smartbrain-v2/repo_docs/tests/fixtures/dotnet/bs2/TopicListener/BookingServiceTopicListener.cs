// Fixture: trimmed reproduction of BS2.0Backend_Integration TopicListener/BookingServiceTopicListener.cs
using Azure.Messaging.ServiceBus;

namespace CustomerBay.TopicListener
{
    public class BookingServiceTopicListener
    {
        private readonly ServiceBusClient _client;
        private readonly string? Endpoint;
        private readonly string? TopicName;
        private readonly string? Subscription;

        public BookingServiceTopicListener(IConfiguration _configuration)
        {
            this.Endpoint = _configuration.GetSection("ServiceBusSettings")["ServiceBusEndpoint"];
            this.TopicName = _configuration.GetSection("ServiceBusSettings")["TopicName"];
            this.Subscription = _configuration.GetSection("ServiceBusSettings")["Subscription"];
            _client = new ServiceBusClient(Endpoint, new ServiceBusClientOptions
            {
                TransportType = ServiceBusTransportType.AmqpWebSockets
            });
        }

        public async Task Register()
        {
            ServiceBusSessionProcessorOptions _sessionProcessorOptions = new ServiceBusSessionProcessorOptions
            {
                MaxConcurrentSessions = 1,
                AutoCompleteMessages = false
            };
            ServiceBusSessionProcessor _processor = _client.CreateSessionProcessor(TopicName, Subscription, _sessionProcessorOptions);
            _processor.ProcessMessageAsync += ProcessMessagesAsync;
            await _processor.StartProcessingAsync().ConfigureAwait(false);
        }

        private async Task ProcessMessagesAsync(ProcessSessionMessageEventArgs args)
        {
            await args.DeadLetterMessageAsync(args.Message);
        }
    }
}
